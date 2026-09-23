from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from backend.app.db.session import engine
from backend.app.db.session import get_db
from backend.app.enterprise_audit import make_audit_event
from auth.service import auth_service
from sqlalchemy.orm import Session
from uuid import uuid4
from backend.app.evidence.router import router as evidence_router
from backend.app.investigations.router import router as investigations_router
from backend.app.product360.schemas import Product360Response, ProductSummary, TemporalRealityResponse
from backend.app.product360.service import Product360Error, Product360Service
from backend.app.retrieval.router import router as retrieval_router
from backend.app.challenger_router import router as challenger_router
from backend.app.day14_router import router as day14_router
from backend.app.decision_router import router as decision_router
from counterfactual.router import router as counterfactual_router
from backend.app.investigations.brief_router import router as brief_router
from backend.app.trust_router import router as trust_router
from backend.app.evaluation_router import router as evaluation_router
from backend.app.integration_router import router as integration_router
from backend.app.access_router import router as access_router
from backend.app.auth_router import router as auth_router
from backend.app.governance_router import router as governance_router
from backend.app.ask_router import router as ask_router
from scenario_intelligence.router import router as scenario_router
from backend.app.workspace_context import router as workspace_context_router
from backend.app.stage3_router import router as stage3_router
from backend.app.communication_router import router as communication_router
from backend.app.stage3_workflow_router import router as stage3_workflow_router
from backend.app.request_context import AuthenticatedRequestContext, get_request_context
from graph.schemas import GraphResponse, HealthResponse, RelationshipDetail
from graph.service import GraphError, RealityGraphService

app = FastAPI(title="MDARIX R1 API", version="0.8.0")


@app.exception_handler(Exception)
async def safe_internal_error(request: Request, exc: Exception) -> JSONResponse:
    """Keep unexpected customer-facing errors free of implementation details."""
    correlation_id = request.headers.get("X-Correlation-ID")
    body = {"code": "INTERNAL_ERROR", "message": "The request could not be completed."}
    if correlation_id:
        body["correlation_id"] = correlation_id
    return JSONResponse(status_code=500, content={"detail": body})


app.include_router(evidence_router)
app.include_router(investigations_router)
app.include_router(retrieval_router)
app.include_router(challenger_router)
app.include_router(day14_router)
app.include_router(decision_router)
app.include_router(counterfactual_router)
app.include_router(brief_router)
app.include_router(trust_router)
app.include_router(evaluation_router)
app.include_router(integration_router)
app.include_router(access_router)
app.include_router(auth_router)
app.include_router(governance_router)
app.include_router(ask_router)
app.include_router(scenario_router)
app.include_router(workspace_context_router)
app.include_router(stage3_router)
app.include_router(communication_router)
app.include_router(stage3_workflow_router)
graph_service = RealityGraphService()
product360_service = Product360Service()


def graph_error(exc: GraphError) -> HTTPException:
    status = 404 if exc.code in {"NODE_NOT_FOUND", "RELATIONSHIP_NOT_FOUND", "PATH_NOT_FOUND"} else 400
    return HTTPException(status_code=status, detail={"code": exc.code, "message": exc.message})


def product_error(exc: Product360Error) -> HTTPException:
    status = 404 if exc.code == "PRODUCT_NOT_FOUND" else 400
    return HTTPException(status_code=status, detail={"code": exc.code, "message": exc.message})


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1")).scalar_one()
    return HealthResponse(status="ok", database="reachable")

@app.get("/health/live")
def liveness() -> dict[str, str]:
    return {"status": "alive"}

@app.get("/health/ready")
def readiness() -> dict[str, str]:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1")).scalar_one()
    return {"status": "ready", "database": "reachable"}


@app.get("/api/v1/graph/nodes/{entity_type}/{entity_id}")
def get_node(entity_type: str, entity_id: str, ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    try:
        return graph_service.get_node(entity_type, entity_id, ctx.tenant_id)
    except GraphError as exc:
        raise graph_error(exc) from exc


@app.get("/api/v1/graph/nodes/{entity_type}/{entity_id}/neighbors", response_model=GraphResponse)
def get_neighbors(entity_type: str, entity_id: str, depth: int = Query(1, ge=0, le=3), direction: str = "both", relationship_type: str | None = None, target_entity_type: str | None = None, ctx: AuthenticatedRequestContext = Depends(get_request_context)) -> GraphResponse:
    try:
        return graph_service.get_neighbors(entity_type, entity_id, depth, direction, relationship_type, target_entity_type, ctx.tenant_id)
    except GraphError as exc:
        raise graph_error(exc) from exc


@app.get("/api/v1/graph/products/{product_id}", response_model=GraphResponse)
def get_product_graph(product_id: str, depth: int = Query(2, ge=0, le=3), ctx: AuthenticatedRequestContext = Depends(get_request_context)) -> GraphResponse:
    try:
        return graph_service.get_product_graph(product_id, depth, ctx.tenant_id)
    except GraphError as exc:
        raise graph_error(exc) from exc


@app.get("/api/v1/graph/investigations/{investigation_id}", response_model=GraphResponse)
def get_investigation_graph(investigation_id: str, depth: int = Query(2, ge=0, le=3), ctx: AuthenticatedRequestContext = Depends(get_request_context)) -> GraphResponse:
    try:
        return graph_service.get_investigation_graph(investigation_id, depth, ctx.tenant_id)
    except GraphError as exc:
        raise graph_error(exc) from exc


@app.get("/api/v1/graph/relationships/{relationship_id}", response_model=RelationshipDetail)
def get_relationship(relationship_id: str, ctx: AuthenticatedRequestContext = Depends(get_request_context)) -> RelationshipDetail:
    try:
        return graph_service.get_relationship_detail(relationship_id, ctx.tenant_id)
    except GraphError as exc:
        raise graph_error(exc) from exc


@app.get("/api/v1/graph/paths", response_model=GraphResponse)
def get_path(source_type: str, source_id: str, target_type: str, target_id: str, max_depth: int = Query(4, ge=0, le=5), ctx: AuthenticatedRequestContext = Depends(get_request_context)) -> GraphResponse:
    try:
        return graph_service.get_path(source_type, source_id, target_type, target_id, max_depth, ctx.tenant_id)
    except GraphError as exc:
        raise graph_error(exc) from exc


@app.get("/api/v1/products", response_model=list[ProductSummary])
def list_products(ctx: AuthenticatedRequestContext = Depends(get_request_context)) -> list[ProductSummary]:
    return product360_service.list_products(ctx.tenant_id)


@app.get("/api/v1/products/{product_id}/investigations")
def list_product_investigations(product_id: str, ctx: AuthenticatedRequestContext = Depends(get_request_context)) -> list[dict]:
    try:
        return product360_service.list_product_investigations(product_id, ctx.tenant_id)
    except Product360Error as exc:
        raise product_error(exc) from exc


def _product360_audit(db: Session, request: Request, product: Product360Response, mode: str, as_of: datetime | None, correlation_id: str) -> None:
    actor = "anonymous"
    tenant_id = product.metadata.get("tenant_id")
    token = request.cookies.get("mdarix_session", "")
    if token:
        try:
            context = auth_service.context(token)
            actor = context["user_id"]
            tenant_id = context["tenant_id"]
        except ValueError:
            pass
    details = {"temporal_mode": {"current": "CURRENT", "event": "EVENT_AS_OF", "known": "KNOWN_AS_OF"}[mode], "result_count": len(product.timeline)}
    if as_of:
        details["temporal_cutoff"] = as_of.isoformat()
    db.add(make_audit_event(tenant_id=tenant_id, actor_ref=actor, action="PRODUCT360_TEMPORAL_RETRIEVAL", entity_type="Product360", correlation_id=correlation_id, details=details))
    db.commit()


@app.get("/api/v1/products/{product_id}/product-360", response_model=Product360Response)
def get_product360(request: Request, product_id: str, version_id: str | None = None, as_of: datetime | None = None, mode: str = Query("current", pattern="^(current|event|known)$"), db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)) -> Product360Response:
    try:
        result = product360_service.product360(product_id, version_id, as_of, mode, ctx.tenant_id)
        _product360_audit(db, request, result, mode, as_of, request.headers.get("X-Correlation-ID") or str(uuid4()))
        return result
    except Product360Error as exc:
        raise product_error(exc) from exc


@app.get("/api/v1/products/{product_id}/timeline", response_model=TemporalRealityResponse)
def get_timeline(request: Request, product_id: str, version_id: str | None = None, as_of: datetime | None = None, mode: str = Query("event", pattern="^(event|known)$"), db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)) -> TemporalRealityResponse:
    try:
        result = product360_service.temporal_reality(product_id, version_id, as_of, mode, ctx.tenant_id)
        _product360_audit(db, request, product360_service.product360(product_id, version_id, as_of, mode), mode, as_of, request.headers.get("X-Correlation-ID") or str(uuid4()))
        return result
    except Product360Error as exc:
        raise product_error(exc) from exc
