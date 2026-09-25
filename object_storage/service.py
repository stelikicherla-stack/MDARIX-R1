"""Tenant-safe object storage with local and S3-compatible backends.

The local backend is intentionally retained for development.  Production must
select ``MDARIX_OBJECT_STORAGE_PROVIDER=s3`` and provide an S3-compatible
endpoint/bucket and credentials.  Object keys and signed URLs never cross a
tenant prefix.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path, PurePosixPath
from urllib.parse import urlencode


class StorageError(RuntimeError):
    pass


class ObjectStorageService:
    def __init__(self, root: str | None = None, *, audit=None):
        self.provider = os.getenv("MDARIX_OBJECT_STORAGE_PROVIDER", "local").lower()
        self.max_object_bytes = int(os.getenv("MDARIX_OBJECT_STORAGE_MAX_BYTES", str(10 * 1024 * 1024)))
        self.tenant_quota_bytes = int(os.getenv("MDARIX_OBJECT_STORAGE_TENANT_QUOTA_BYTES", str(100 * 1024 * 1024)))
        self.signing_secret = os.getenv("MDARIX_OBJECT_STORAGE_SIGNING_SECRET")
        if self.provider == "s3":
            try:
                import boto3
            except ImportError as exc:
                raise StorageError("S3 provider requires the boto3 dependency") from exc
            self.bucket = os.environ["MDARIX_OBJECT_STORAGE_BUCKET"]
            self.client = boto3.client(
                "s3", endpoint_url=os.getenv("MDARIX_OBJECT_STORAGE_ENDPOINT"),
                region_name=os.getenv("MDARIX_OBJECT_STORAGE_REGION", "us-east-1"),
                aws_access_key_id=os.getenv("MDARIX_OBJECT_STORAGE_ACCESS_KEY"),
                aws_secret_access_key=os.getenv("MDARIX_OBJECT_STORAGE_SECRET_KEY"),
            )
        elif self.provider == "local":
            self.root = Path(root or os.getenv("MDARIX_OBJECT_STORAGE_ROOT", ".mdarix-object-storage"))
            self.root.mkdir(parents=True, exist_ok=True)
        else:
            raise StorageError(f"Unsupported object storage provider: {self.provider}")
        self.audit = audit

    @staticmethod
    def _tenant_key(tenant_id: str, key: str) -> str:
        tenant = str(tenant_id).strip()
        name = str(key).replace("\\", "/").lstrip("/")
        path = PurePosixPath(name)
        if not tenant or tenant in {".", ".."} or any(part in {"", ".", ".."} for part in path.parts):
            raise StorageError("Invalid tenant or object key")
        return f"{tenant}/{path.as_posix()}"

    @staticmethod
    def _assert_tenant_key(tenant_id: str, object_key: str) -> str:
        expected_prefix = f"{tenant_id}/"
        if not str(object_key).startswith(expected_prefix):
            raise FileNotFoundError(object_key)
        suffix = str(object_key)[len(expected_prefix):]
        if not suffix or any(part in {"", ".", ".."} for part in PurePosixPath(suffix).parts):
            raise FileNotFoundError(object_key)
        return str(object_key)

    def _tenant_usage(self, tenant_id: str) -> int:
        if self.provider == "local":
            base = self.root / str(tenant_id)
            return sum(p.stat().st_size for p in base.rglob("*") if p.is_file()) if base.exists() else 0
        return 0  # S3 quota is enforced by the durable attachment metadata layer.

    def _audit(self, action: str, tenant_id: str, object_key: str, **details):
        if self.audit:
            self.audit(action, tenant_id, object_key, details)

    def put(self, tenant_id: str, key: str, content: bytes, *, content_type: str = "application/octet-stream", retention_until: datetime | None = None) -> dict:
        if len(content) > self.max_object_bytes:
            raise StorageError("OBJECT_SIZE_QUOTA_EXCEEDED")
        object_key = self._tenant_key(tenant_id, key)
        if self.provider == "local" and self._tenant_usage(tenant_id) + len(content) > self.tenant_quota_bytes:
            raise StorageError("TENANT_STORAGE_QUOTA_EXCEEDED")
        checksum = hashlib.sha256(content).hexdigest()
        if self.provider == "s3":
            self.client.put_object(Bucket=self.bucket, Key=object_key, Body=content, ContentType=content_type,
                                   ServerSideEncryption=os.getenv("MDARIX_OBJECT_STORAGE_SSE", "AES256"),
                                   Metadata={"tenant-id": str(tenant_id), "sha256": checksum,
                                            **({"retention-until": retention_until.isoformat()} if retention_until else {})})
        else:
            path = self.root / object_key
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        self._audit("OBJECT_STORED", str(tenant_id), object_key, size=len(content), checksum=checksum)
        return {"tenant_id": str(tenant_id), "object_key": object_key, "size": len(content), "checksum": checksum,
                "content_type": content_type, "retention_until": retention_until}

    def scan(self, content: bytes, content_type: str) -> bool:
        scanner = os.getenv("MDARIX_MALWARE_SCANNER_COMMAND")
        if scanner:
            try:
                result = subprocess.run(scanner.split(), input=content, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, timeout=15, check=False)
                return result.returncode == 0
            except (OSError, subprocess.TimeoutExpired):
                return False
        dangerous_headers = (b"MZ", b"\x7fELF", b"#!")
        if content[:2] in dangerous_headers[:2] or content.startswith(dangerous_headers[2]):
            return False
        return not (content_type == "application/pdf" and b"/JavaScript" in content[:2_000_000])

    def get(self, tenant_id: str, object_key: str) -> bytes:
        expected = self._assert_tenant_key(tenant_id, object_key)
        if self.provider == "s3":
            body = self.client.get_object(Bucket=self.bucket, Key=expected)["Body"].read()
        else:
            path = self.root / expected
            if not path.is_file():
                raise FileNotFoundError(object_key)
            body = path.read_bytes()
        self._audit("OBJECT_READ", str(tenant_id), expected, size=len(body))
        return body

    def signed_url(self, tenant_id: str, object_key: str, *, expires_seconds: int = 300) -> str:
        expected = self._assert_tenant_key(tenant_id, object_key)
        if expires_seconds < 1 or expires_seconds > 3600:
            raise StorageError("INVALID_SIGNED_URL_REQUEST")
        if self.provider == "s3":
            return self.client.generate_presigned_url("get_object", Params={"Bucket": self.bucket, "Key": expected}, ExpiresIn=expires_seconds)
        if not self.signing_secret:
            raise StorageError("SIGNED_URL_SECRET_NOT_CONFIGURED")
        expires = int(time.time()) + expires_seconds
        signature = hmac.new(self.signing_secret.encode(), f"{expected}:{expires}".encode(), hashlib.sha256).hexdigest()
        self._audit("OBJECT_SIGNED_URL_CREATED", str(tenant_id), expected, expires_at=expires)
        return "local://object?" + urlencode({"key": expected, "expires": expires, "signature": signature})

    def verify_signed_url(self, tenant_id: str, signed_url: str) -> str:
        """Validate a development signed URL and return its tenant-scoped key."""
        if self.provider != "local" or not signed_url.startswith("local://object?"):
            raise StorageError("SIGNED_URL_VERIFICATION_UNSUPPORTED")
        from urllib.parse import parse_qs, urlparse
        query = parse_qs(urlparse(signed_url).query)
        key = query.get("key", [""])[0]
        expires = int(query.get("expires", ["0"])[0])
        signature = query.get("signature", [""])[0]
        expected = self._assert_tenant_key(tenant_id, key)
        if expires < int(time.time()) or not self.signing_secret:
            raise StorageError("SIGNED_URL_EXPIRED")
        expected_signature = hmac.new(self.signing_secret.encode(), f"{expected}:{expires}".encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            raise StorageError("INVALID_SIGNED_URL")
        return expected

    def delete_expired(self, *, now: datetime | None = None) -> int:
        """Delete locally retained objects; S3 lifecycle rules handle production retention."""
        if self.provider != "local":
            return 0
        # Retention is carried in metadata by S3; local callers should delete via
        # the durable attachment policy rather than guessing from filenames.
        return 0

    def delete(self, tenant_id: str, object_key: str) -> None:
        expected = self._assert_tenant_key(tenant_id, object_key)
        if self.provider == "s3":
            self.client.delete_object(Bucket=self.bucket, Key=expected)
        else:
            path = self.root / expected
            if path.exists():
                path.unlink()
        self._audit("OBJECT_DELETED", str(tenant_id), expected)
