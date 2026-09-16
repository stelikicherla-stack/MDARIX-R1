import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text

from backend.app.db.session import engine


REQUIRED_TABLES = {
    "tenants",
    "source_records",
    "products",
    "product_versions",
    "components",
    "suppliers",
    "manufacturing_sites",
    "lot_batches",
    "requirements",
    "changes",
    "complaints",
    "investigations",
    "risks",
    "failure_modes",
    "controls",
    "evidence",
    "hypotheses",
    "unknowns",
    "failure_chains",
    "failure_chain_nodes",
    "failure_chain_edges",
    "scenarios",
    "decisions",
    "ai_executions",
    "human_reviews",
    "reality_relationships",
    "product_components",
    "product_suppliers",
    "component_suppliers",
    "lot_components",
    "investigation_complaints",
    "investigation_evidence",
    "hypothesis_evidence",
    "evidence_embeddings",
    "audit_events",
    "alembic_version",
}


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    with engine.connect() as conn:
        database, user, version = conn.execute(
            text("SELECT current_database(), current_user, current_setting('server_version')")
        ).one()
        print(f"database={database}")
        print(f"user={user}")
        print(f"postgres={version}")
        check(database == "mdarix_r1", "Unexpected database")
        check(user == "mdarix_app", "Unexpected database user")
        check(str(version).startswith("16."), "PostgreSQL 16 required")

        vector = conn.execute(text("SELECT extversion FROM pg_extension WHERE extname='vector'")).scalar_one_or_none()
        print(f"pgvector={vector}")
        check(vector is not None, "pgvector extension missing")

        cfg = Config("alembic.ini")
        head = ScriptDirectory.from_config(cfg).get_current_head()
        current = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        print(f"alembic_current={current}")
        print(f"alembic_head={head}")
        check(current == head, "Database is not at Alembic head")

        inspector = inspect(conn)
        tables = set(inspector.get_table_names())
        missing = sorted(REQUIRED_TABLES - tables)
        print(f"required_tables={len(REQUIRED_TABLES)}")
        check(not missing, f"Missing required tables: {missing}")

        evidence_cols = {column["name"] for column in inspector.get_columns("evidence")}
        ai_cols = {column["name"] for column in inspector.get_columns("ai_executions")}
        embedding_type = conn.execute(
            text("SELECT udt_name FROM information_schema.columns WHERE table_name='evidence_embeddings' AND column_name='embedding'")
        ).scalar_one()
        check("fact_type" in evidence_cols, "Evidence fact_type column missing")
        check("chain_of_thought" not in ai_cols, "AIExecution must not store hidden chain-of-thought")
        check(embedding_type == "vector", "Evidence embedding vector column missing")

    print("DAY 2 DATABASE VALIDATION = PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"DAY 2 DATABASE VALIDATION = FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
