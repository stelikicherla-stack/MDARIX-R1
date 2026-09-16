from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import text

from backend.app.db.session import engine
from graph.schemas import GraphResponse, HealthResponse, RelationshipDetail
from graph.service import GraphError, RealityGraphService

app = FastAPI(title="MDARIX R1 API", version="0.6.0")
graph_service = RealityGraphService()


def graph_error(exc: GraphError) -> HTTPException:
    status = 404 if exc.code in {"NODE_NOT_FOUND", "RELATIONSHIP_NOT_FOUND", "PATH_NOT_FOUND"} else 400
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
