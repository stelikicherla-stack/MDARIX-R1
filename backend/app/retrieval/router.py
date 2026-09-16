from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.evidence.router import get_default_tenant_id
from retrieval.schemas import RetrievalRequest, RetrievalResponse
from retrieval.service import RetrievalError, TrustedRetrievalService


router = APIRouter(prefix="/api/v1/retrieval", tags=["Trusted Evidence Retrieval"])
service = TrustedRetrievalService()


@router.post("/index")
def index_evidence_chunks(reprocess: bool = Query(False), db: Session = Depends(get_db)) -> dict[str, Any]:
    tenant_id = get_default_tenant_id(db)
    return service.index_evidence_chunks(db, tenant_id, reprocess=reprocess)


@router.post("/query", response_model=RetrievalResponse)
def query_retrieval(request: RetrievalRequest, db: Session = Depends(get_db)) -> RetrievalResponse:
    tenant_id = get_default_tenant_id(db)
    scoped_request = request.model_copy(update={"tenant_id": tenant_id})
    try:
        return service.retrieve(db, scoped_request)
    except RetrievalError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
