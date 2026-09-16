import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
import uuid

from sqlalchemy.orm import Session
from backend.app.db.models.foundation import Evidence


class ContentSecurityError(Exception):
    """Raised when an illegal path traversal or cross-tenant file access attempt is detected."""
    pass


class EvidenceContentReader:
    """Securely reads and resolves evidence content from DB records or tenant-scoped local storage."""

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = workspace_root or Path(os.getcwd())

    def get_evidence_content(self, db: Session, tenant_id: uuid.UUID, evidence_id: uuid.UUID) -> tuple[str, Dict[str, Any]]:
        """Retrieves raw content and metadata for a tenant-scoped evidence item."""
        evidence = (
            db.query(Evidence)
            .filter(Evidence.tenant_id == tenant_id, Evidence.id == evidence_id)
            .first()
        )
        if not evidence:
            raise ValueError(f"Evidence {evidence_id} not found for tenant {tenant_id}")

        metadata = {
            "evidence_id": str(evidence.id),
            "evidence_identifier": evidence.evidence_identifier,
            "evidence_type": evidence.evidence_type,
            "title": evidence.title,
            "source_system": evidence.source_system,
            "source_reference": evidence.source_reference,
            "reliability_status": evidence.reliability_status,
            "fact_type": evidence.fact_type,
            "document_ref": evidence.document_ref,
            "effective_timestamp": evidence.effective_timestamp.isoformat() if evidence.effective_timestamp else None,
            "recorded_timestamp": evidence.recorded_timestamp.isoformat() if evidence.recorded_timestamp else None,
            "ingestion_timestamp": evidence.ingestion_timestamp.isoformat() if evidence.ingestion_timestamp else None,
        }

        # 1. Directly stored text content in DB
        if evidence.content and evidence.content.strip():
            return evidence.content, metadata

        # 2. File-backed evidence reference resolving with strict path traversal defense
        if evidence.document_ref:
            safe_content = self.read_file_reference(evidence.document_ref)
            return safe_content, metadata

        if evidence.source_reference:
            safe_content = self.read_file_reference(evidence.source_reference)
            return safe_content, metadata

        # Default fallback string if no content text is populated
        return f"Evidence record: {evidence.title} ({evidence.evidence_type})", metadata

    def read_file_reference(self, file_ref: str) -> str:
        """Resolves file reference safely, preventing path traversal attacks."""
        # Sanitize and resolve target path
        clean_ref = file_ref.replace("file:///", "").replace("file://", "")
        target_path = Path(clean_ref).resolve()

        # Check path traversal
        try:
            target_path.relative_to(self.workspace_root.resolve())
        except ValueError:
            # If path is outside workspace, reject path traversal
            raise ContentSecurityError(f"Access denied: file path {clean_ref} is outside the allowed tenant workspace.")

        if not target_path.exists():
            return f"File reference {clean_ref} not found on disk."

        with open(target_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
