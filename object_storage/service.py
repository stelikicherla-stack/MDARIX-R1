import hashlib
from pathlib import Path

class ObjectStorageService:
    """Provider-neutral object storage; local filesystem is development-only."""
    def __init__(self, root: str = ".mdarix-object-storage"):
        self.root = Path(root); self.root.mkdir(parents=True, exist_ok=True)
    def put(self, tenant_id: str, key: str, content: bytes) -> dict:
        safe = Path(key).name; path = self.root / tenant_id / safe; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(content)
        return {"tenant_id":tenant_id,"object_key":f"{tenant_id}/{safe}","size":len(content),"checksum":hashlib.sha256(content).hexdigest()}
    def scan(self, content: bytes, content_type: str) -> bool:
        """Provider-neutral safety gate; production should replace this with AV scanning."""
        dangerous_headers = (b"MZ", b"\x7fELF", b"#!")
        if content[:2] in dangerous_headers[:2] or content.startswith(dangerous_headers[2]):
            return False
        if content_type == "application/pdf" and b"/JavaScript" in content[:2_000_000]:
            return False
        return True
    def get(self, tenant_id: str, object_key: str) -> bytes:
        path = self.root / tenant_id / Path(object_key).name
        if not path.is_file(): raise FileNotFoundError(object_key)
        return path.read_bytes()
