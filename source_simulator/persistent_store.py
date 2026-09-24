"""Small persistent store used by the external-provider simulator.

The simulator deliberately has its own database URL. It never imports MDARIX
models and therefore cannot read or write the MDARIX business database.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from sqlalchemy import DateTime, Integer, String, Text, create_engine, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from source_simulator.provider_catalog import schema_for

class Base(DeclarativeBase):
    pass

class SourceRecord(Base):
    __tablename__ = "provider_source_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_key: Mapped[str] = mapped_column(String(80), index=True)
    provider: Mapped[str] = mapped_column(String(80), index=True)
    source_entity: Mapped[str] = mapped_column(String(120), index=True)
    external_id: Mapped[str] = mapped_column(String(255), index=True)
    record_version: Mapped[str] = mapped_column(String(80))
    payload: Mapped[str] = mapped_column(Text())
    fingerprint: Mapped[str] = mapped_column(String(64))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class SourceRecordHistory(Base):
    __tablename__ = "provider_source_record_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_key: Mapped[str] = mapped_column(String(80), index=True)
    provider: Mapped[str] = mapped_column(String(80))
    source_entity: Mapped[str] = mapped_column(String(120))
    external_id: Mapped[str] = mapped_column(String(255))
    record_version: Mapped[str] = mapped_column(String(80))
    payload: Mapped[str] = mapped_column(Text())
    fingerprint: Mapped[str] = mapped_column(String(64))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

def _engine():
    url = os.getenv("SIMULATOR_DATABASE_URL", "sqlite:///source-simulator.db")
    return create_engine(url, pool_pre_ping=True)

engine = _engine()
Base.metadata.create_all(engine)

def _json(value: dict) -> dict:
    return json.loads(value) if isinstance(value, str) else value

def upsert(provider: str, tenant_key: str, entity: str, external_id: str, version: str, payload: dict) -> dict:
    now = datetime.now(timezone.utc)
    clean = dict(payload)
    clean["tenant_key"] = tenant_key
    fingerprint = hashlib.sha256(json.dumps(clean, sort_keys=True).encode()).hexdigest()
    with Session(engine) as db:
        current = db.scalar(select(SourceRecord).where(SourceRecord.tenant_key == tenant_key, SourceRecord.provider == provider, SourceRecord.source_entity == entity, SourceRecord.external_id == external_id))
        outcome = "CREATED"
        if current is None:
            current = SourceRecord(tenant_key=tenant_key, provider=provider, source_entity=entity, external_id=external_id, record_version=version, payload=json.dumps(clean), fingerprint=fingerprint, updated_at=now)
            db.add(current)
        elif current.fingerprint != fingerprint:
            outcome = "UPDATED"
            db.add(SourceRecordHistory(tenant_key=tenant_key, provider=provider, source_entity=entity, external_id=external_id, record_version=current.record_version, payload=json.dumps(_json(current.payload)), fingerprint=current.fingerprint, recorded_at=now))
            current.record_version = version; current.payload = json.dumps(clean); current.fingerprint = fingerprint; current.updated_at = now
        else:
            outcome = "DUPLICATE"
        db.commit()
        return {"external_id": external_id, "record_version": current.record_version, "fingerprint": current.fingerprint, "payload": _json(current.payload), "outcome": outcome}

def list_records(provider: str, tenant_key: str, entity: str) -> list[dict]:
    with Session(engine) as db:
        rows = db.scalars(select(SourceRecord).where(SourceRecord.provider == provider, SourceRecord.tenant_key == tenant_key, SourceRecord.source_entity == entity).order_by(SourceRecord.external_id)).all()
        return [{**_json(row.payload), "external_id": row.external_id, "record_version": row.record_version} for row in rows]

def history(provider: str, tenant_key: str, entity: str, external_id: str) -> list[dict]:
    with Session(engine) as db:
        rows = db.scalars(select(SourceRecordHistory).where(SourceRecordHistory.provider == provider, SourceRecordHistory.tenant_key == tenant_key, SourceRecordHistory.source_entity == entity, SourceRecordHistory.external_id == external_id).order_by(SourceRecordHistory.recorded_at)).all()
        return [{"external_id": row.external_id, "record_version": row.record_version, "payload": _json(row.payload), "recorded_at": row.recorded_at} for row in rows]
