import hashlib
from pathlib import Path

class ObjectStorageService:
    """Provider-neutral object storage; local filesystem is development-only."""
    def __init__(self, root: str = ".mdarix-object-storage"):
        self.root = Path(root); self.root.mkdir(parents=True, exist_ok=True)
    def put(self, tenant_id: str, key: str, content: bytes) -> dict:
        safe = Path(key).name; path = self.root / tenant_id / safe; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(content)
        return {"tenant_id":tenant_id,"object_key":f"{tenant_id}/{safe}","size":len(content),"checksum":hashlib.sha256(content).hexdigest()}
