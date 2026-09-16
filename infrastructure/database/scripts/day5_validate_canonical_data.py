import sys
from pathlib import Path

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.db.session import engine


TENANT_KEY = "ACME_CARE_SYNTHETIC"


def fail(message: str) -> None:
    raise SystemExit(f"DAY 5 CANONICAL DATA VALIDATION = FAIL\n{message}")


def scalar(conn, sql: str, **params):
    return conn.execute(text(sql), params).scalar_one()


def main() -> int:
    with engine.connect() as conn:
        tenant_id = scalar(conn, "SELECT id FROM tenants WHERE tenant_key=:tenant_key", tenant_key=TENANT_KEY)
        run = conn.execute(
            text(
                "SELECT * FROM normalization_runs WHERE tenant_id=:tenant_id AND status in ('COMPLETED','COMPLETED_WITH_WARNINGS') "
                "ORDER BY completed_at DESC LIMIT 1"
            ),
            {"tenant_id": tenant_id},
        ).mappings().one_or_none()
        if not run:
            fail("No completed Day 5 normalization run found.")
        run_id = run["id"]

        checks = {
            "products": scalar(conn, "SELECT count(*) FROM products WHERE tenant_id=:tenant_id", tenant_id=tenant_id),
            "product_versions": scalar(conn, "SELECT count(*) FROM product_versions WHERE tenant_id=:tenant_id", tenant_id=tenant_id),
            "components": scalar(conn, "SELECT count(*) FROM components WHERE tenant_id=:tenant_id", tenant_id=tenant_id),
            "suppliers": scalar(conn, "SELECT count(*) FROM suppliers WHERE tenant_id=:tenant_id", tenant_id=tenant_id),
            "sites": scalar(conn, "SELECT count(*) FROM manufacturing_sites WHERE tenant_id=:tenant_id", tenant_id=tenant_id),
            "lots": scalar(conn, "SELECT count(*) FROM lot_batches WHERE tenant_id=:tenant_id", tenant_id=tenant_id),
            "requirements": scalar(conn, "SELECT count(*) FROM requirements WHERE tenant_id=:tenant_id", tenant_id=tenant_id),
            "changes": scalar(conn, "SELECT count(*) FROM changes WHERE tenant_id=:tenant_id", tenant_id=tenant_id),
            "complaints": scalar(conn, "SELECT count(*) FROM complaints WHERE tenant_id=:tenant_id", tenant_id=tenant_id),
            "investigations": scalar(conn, "SELECT count(*) FROM investigations WHERE tenant_id=:tenant_id", tenant_id=tenant_id),
            "evidence": scalar(conn, "SELECT count(*) FROM evidence WHERE tenant_id=:tenant_id", tenant_id=tenant_id),
            "links": scalar(conn, "SELECT count(*) FROM source_canonical_links WHERE tenant_id=:tenant_id AND normalization_run_id=:run_id", tenant_id=tenant_id, run_id=run_id),
            "rules": scalar(conn, "SELECT count(*) FROM identity_rules WHERE active=true"),
            "relationships": scalar(conn, "SELECT count(*) FROM canonical_relationships WHERE tenant_id=:tenant_id", tenant_id=tenant_id),
            "ground_truth_links": scalar(conn, "SELECT count(*) FROM source_canonical_links WHERE provenance::text LIKE '%ground_truth%' AND provenance::text NOT LIKE '%ground_truth_used%false%'", tenant_id=tenant_id),
        }

        minimums = {
            "products": 2,
            "product_versions": 6,
            "components": 16,
            "suppliers": 5,
            "sites": 2,
            "lots": 18,
            "requirements": 24,
            "changes": 16,
            "complaints": 120,
            "investigations": 10,
            "evidence": 38,
            "links": 337,
            "rules": 12,
            "relationships": 18,
        }
        for key, expected in minimums.items():
            if checks[key] < expected:
                fail(f"{key} expected >= {expected}; observed {checks[key]}")
        if checks["ground_truth_links"] != 0:
            fail("Ground Truth appeared in normalization provenance.")

        product_version_links = scalar(
            conn,
            "SELECT count(*) FROM source_canonical_links l JOIN staged_source_records s ON s.id=l.staged_source_record_id "
            "WHERE l.tenant_id=:tenant_id AND l.normalization_run_id=:run_id AND s.raw_payload::text LIKE '%PRD100 Rev D%' "
            "AND l.canonical_entity_type='product_version' AND l.resolution_status='MATCHED'",
            tenant_id=tenant_id,
            run_id=run_id,
        )
        if product_version_links < 1:
            fail("PRD100 Rev D did not resolve to a canonical product version.")

        duplicate_canonicals = scalar(
            conn,
            "SELECT count(*) FROM (SELECT product_identifier, count(*) c FROM products WHERE tenant_id=:tenant_id GROUP BY product_identifier HAVING count(*) > 1) d",
            tenant_id=tenant_id,
        )
        if duplicate_canonicals:
            fail("Duplicate canonical products detected.")

        causal_edges = scalar(conn, "SELECT count(*) FROM canonical_relationships WHERE tenant_id=:tenant_id AND relationship_type ILIKE '%CAUSE%'", tenant_id=tenant_id)
        if causal_edges:
            fail("Day 5 created causal relationships.")

        print("DAY 5 CANONICAL DATA VALIDATION = PASS")
        print(f"normalization_run_id={run_id}")
        for key in sorted(checks):
            print(f"{key}={checks[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
