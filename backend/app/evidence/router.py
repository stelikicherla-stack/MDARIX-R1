import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from backend.app.db.models.foundation import Evidence, Tenant
from backend.app.db.session import get_db
from evidence.services.evidence_service import EvidenceIntelligenceService
from auth.service import auth_service

router = APIRouter(prefix="/api/v1/evidence", tags=["Evidence Intelligence"])
service = EvidenceIntelligenceService()


def get_default_tenant_id(db: Session) -> uuid.UUID:
    """Legacy compatibility guard: anonymous default-tenant access is forbidden."""
    raise HTTPException(status_code=401, detail={"code": "UNAUTHENTICATED", "message": "Authentication required"})

def tenant_context(request: Request, db: Session) -> uuid.UUID:
    token = request.cookies.get("mdarix_session", "")
    if token:
        try:
            return uuid.UUID(auth_service.context(token)["tenant_id"])
        except ValueError as exc:
            raise HTTPException(status_code=401, detail={"code": "UNAUTHENTICATED", "message": "Authentication required"}) from exc
    return get_default_tenant_id(db)



@router.get("", response_model=List[Dict[str, Any]])
def list_evidence(
    request: Request,
    evidence_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Lists evidence items for default tenant with optional filtering."""
    tenant_id = tenant_context(request, db)
    query = db.query(Evidence).filter(Evidence.tenant_id == tenant_id)
    if evidence_type:
        query = query.filter(Evidence.evidence_type == evidence_type)

    evidence_records = query.limit(limit).all()
    return [
        {
            "id": str(ev.id),
            "evidence_identifier": ev.evidence_identifier,
            "evidence_type": ev.evidence_type,
            "title": ev.title,
            "source_system": ev.source_system,
            "reliability_status": ev.reliability_status,
            "fact_type": ev.fact_type,
            "document_ref": ev.document_ref,
            "effective_timestamp": ev.effective_timestamp.isoformat() if ev.effective_timestamp else None,
            "ingestion_timestamp": ev.ingestion_timestamp.isoformat() if ev.ingestion_timestamp else None,
        }
        for ev in evidence_records
    ]


@router.get("/{evidence_id}")
def get_evidence_detail(evidence_id: str, request: Request, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Returns evidence detail summary including chunks, observations, links, and provenance."""
    tenant_id = tenant_context(request, db)
    try:
        ev_uuid = uuid.UUID(evidence_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid evidence UUID format.")

    try:
        return service.get_evidence_intelligence_summary(db, tenant_id, ev_uuid)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{evidence_id}/content")
def get_evidence_content(evidence_id: str, request: Request, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Returns secure tenant-isolated raw content of an evidence record."""
    tenant_id = tenant_context(request, db)
    try:
        ev_uuid = uuid.UUID(evidence_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid evidence UUID format.")

    try:
        content, metadata = service.content_reader.get_evidence_content(db, tenant_id, ev_uuid)
        return {"content": content, "metadata": metadata}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/{evidence_id}/chunks")
def get_evidence_chunks(evidence_id: str, request: Request, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Returns chunk list and locators for an evidence item."""
    summary = get_evidence_detail(evidence_id, request, db)
    return {"evidence_id": evidence_id, "chunks_count": summary["chunks_count"], "chunks": summary["chunks"]}


@router.get("/{evidence_id}/observations")
def get_evidence_observations(evidence_id: str, request: Request, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Returns extracted observations and source anchors for an evidence item."""
    summary = get_evidence_detail(evidence_id, request, db)
    return {
        "evidence_id": evidence_id,
        "observations_count": summary["observations_count"],
        "observations": summary["observations"],
    }


@router.get("/{evidence_id}/provenance")
def get_evidence_provenance(evidence_id: str, request: Request, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Returns AI execution provenance records for an evidence item."""
    summary = get_evidence_detail(evidence_id, request, db)
    return {
        "evidence_id": evidence_id,
        "ai_provenance_count": summary["ai_provenance_count"],
        "ai_provenance": summary["ai_provenance"],
    }


@router.get("/{evidence_id}/related-entities")
def get_evidence_related_entities(evidence_id: str, request: Request, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Returns canonical entity links and unresolved entity references for an evidence item."""
    summary = get_evidence_detail(evidence_id, request, db)
    return {
        "evidence_id": evidence_id,
        "entity_links_count": summary["entity_links_count"],
        "entity_links": summary["entity_links"],
    }


@router.post("/{evidence_id}/process")
def process_evidence_intelligence(
    evidence_id: str,
    request: Request,
    reprocess: bool = Query(False),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Triggers Evidence Intelligence processing pipeline on evidence item."""
    tenant_id = tenant_context(request, db)
    try:
        ev_uuid = uuid.UUID(evidence_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid evidence UUID format.")

    try:
        return service.process_evidence_intelligence(db, tenant_id, ev_uuid, reprocess=reprocess)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
