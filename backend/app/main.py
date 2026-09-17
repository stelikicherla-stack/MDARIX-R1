from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import text

from backend.app.db.session import engine
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
from graph.schemas import GraphResponse, HealthResponse, RelationshipDetail
from graph.service import GraphError, RealityGraphService

app = FastAPI(title="MDARIX R1 API", version="0.8.0")
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


@app.get("/api/v1/graph/nodes/{entity_type}/{entity_id}")
def get_node(entity_type: str, entity_id: str):
    try:
        return graph_service.get_node(entity_type, entity_id)
    except GraphError as exc:
        raise graph_error(exc) from exc


@app.get("/api/v1/graph/nodes/{entity_type}/{entity_id}/neighbors", response_model=GraphResponse)
def get_neighbors(entity_type: str, entity_id: str, depth: int = Query(1, ge=0, le=3), direction: str = "both", relationship_type: str | None = None, target_entity_type: str | None = None) -> GraphResponse:
    try:
        return graph_service.get_neighbors(entity_type, entity_id, depth, direction, relationship_type, target_entity_type)
    except GraphError as exc:
        raise graph_error(exc) from exc


@app.get("/api/v1/graph/products/{product_id}", response_model=GraphResponse)
def get_product_graph(product_id: str, depth: int = Query(2, ge=0, le=3)) -> GraphResponse:
    try:
        return graph_service.get_product_graph(product_id, depth)
    except GraphError as exc:
        raise graph_error(exc) from exc


@app.get("/api/v1/graph/investigations/{investigation_id}", response_model=GraphResponse)
def get_investigation_graph(investigation_id: str, depth: int = Query(2, ge=0, le=3)) -> GraphResponse:
    try:
        return graph_service.get_investigation_graph(investigation_id, depth)
    except GraphError as exc:
        raise graph_error(exc) from exc


@app.get("/api/v1/graph/relationships/{relationship_id}", response_model=RelationshipDetail)
def get_relationship(relationship_id: str) -> RelationshipDetail:
    try:
        return graph_service.get_relationship_detail(relationship_id)
    except GraphError as exc:
        raise graph_error(exc) from exc


@app.get("/api/v1/graph/paths", response_model=GraphResponse)
def get_path(source_type: str, source_id: str, target_type: str, target_id: str, max_depth: int = Query(4, ge=0, le=5)) -> GraphResponse:
    try:
        return graph_service.get_path(source_type, source_id, target_type, target_id, max_depth)
    except GraphError as exc:
        raise graph_error(exc) from exc


@app.get("/api/v1/products", response_model=list[ProductSummary])
def list_products() -> list[ProductSummary]:
    return product360_service.list_products()


@app.get("/api/v1/products/{product_id}/investigations")
def list_product_investigations(product_id: str) -> list[dict]:
    try:
        return product360_service.list_product_investigations(product_id)
    except Product360Error as exc:
        raise product_error(exc) from exc


@app.get("/api/v1/products/{product_id}/product-360", response_model=Product360Response)
def get_product360(product_id: str, version_id: str | None = None, as_of: datetime | None = None, mode: str = Query("current", pattern="^(current|event|known)$")) -> Product360Response:
    try:
        return product360_service.product360(product_id, version_id, as_of, mode)
    except Product360Error as exc:
        raise product_error(exc) from exc


@app.get("/api/v1/products/{product_id}/timeline", response_model=TemporalRealityResponse)
def get_timeline(product_id: str, version_id: str | None = None, as_of: datetime | None = None, mode: str = Query("event", pattern="^(event|known)$")) -> TemporalRealityResponse:
    try:
        return product360_service.temporal_reality(product_id, version_id, as_of, mode)
    except Product360Error as exc:
        raise product_error(exc) from exc
