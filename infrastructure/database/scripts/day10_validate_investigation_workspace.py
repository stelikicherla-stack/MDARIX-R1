import datetime as dt
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from backend.app.db.models.foundation import Investigation, Tenant
from backend.app.db.session import SessionLocal
from investigation_workspace.schemas import InvestigationWorkspaceRequest
from investigation_workspace.service import InvestigationWorkspaceService
from retrieval.service import TrustedRetrievalService


def run_day10_validation() -> int:
    print("=" * 72)
    print("STARTING DAY 10 INVESTIGATION WORKSPACE VALIDATION")
    print("=" * 72)

    db = SessionLocal()
    errors: list[str] = []

    try:
        tenant = db.query(Tenant).filter(Tenant.tenant_key == "ACME_CARE_SYNTHETIC").first() or db.query(Tenant).first()
        if not tenant:
            print("[FAIL] No tenant available.")
            return 1
        print(f"[PASS] Tenant scope verified ({tenant.tenant_key})")

        investigation = (
            db.query(Investigation)
            .filter(Investigation.tenant_id == tenant.id, Investigation.investigation_identifier == "INV-001")
            .first()
        )
        if not investigation:
            print("[FAIL] INV-001 not found.")
            return 1
        print(f"[PASS] Investigation found ({investigation.investigation_identifier})")

        TrustedRetrievalService().index_evidence_chunks(db, tenant.id)
        service = InvestigationWorkspaceService()
        view = service.workspace(
            db,
            InvestigationWorkspaceRequest(
                tenant_id=tenant.id,
                investigation_id=investigation.id,
                retrieval_top_k=8,
            ),
        )

        if view.product_context["product"]["product_identifier"] != "PRD-ASTER-100":
            errors.append("Product context did not resolve to PRD-ASTER-100.")
            print("[FAIL] Product context mismatch.")
        else:
            print("[PASS] Product context resolved.")

        if not view.relationship_context["nodes"]:
            errors.append("Relationship context is empty.")
            print("[FAIL] Relationship context empty.")
        else:
            print(f"[PASS] Relationship context available ({len(view.relationship_context['nodes'])} nodes).")

        if not view.evidence_context:
            errors.append("Evidence context is empty.")
            print("[FAIL] Evidence context empty.")
        else:
            print(f"[PASS] Evidence context available ({len(view.evidence_context)} records).")

        unanchored = [
            evidence["evidence_identifier"]
            for evidence in view.evidence_context
            if not any(chunk["source_anchor"] for chunk in evidence["chunks"])
        ]
        if unanchored:
            errors.append(f"Evidence records missing source anchors: {unanchored}")
            print("[FAIL] Evidence source-anchor coverage below 100%.")
        else:
            print("[PASS] Evidence source-anchor coverage: 100%.")

        if view.retrieval_context is None:
            errors.append("Retrieval context missing.")
            print("[FAIL] Retrieval context missing.")
        else:
            print(f"[PASS] Retrieval context status: {view.retrieval_context.status}.")

        as_of = dt.datetime(2026, 2, 15, tzinfo=dt.timezone.utc)
        known = service.workspace(
            db,
            InvestigationWorkspaceRequest(
                tenant_id=tenant.id,
                investigation_id=investigation.id,
                temporal_mode="known",
                as_of=as_of,
            ),
        )
        future = [
            evidence["evidence_identifier"]
            for evidence in known.evidence_context
            if evidence["temporal"]["ingestion_timestamp"]
            and dt.datetime.fromisoformat(evidence["temporal"]["ingestion_timestamp"]) > as_of
        ]
        if future:
            errors.append(f"Known-as-of workspace leaked future evidence: {future}")
            print("[FAIL] Known-as-of future evidence leakage detected.")
        else:
            print("[PASS] Known-as-of future evidence leakage: 0.")

        payload = view.model_dump_json().lower()
        if "actual_root_cause" in payload or view.guardrails["generates_causality"] is not False:
            errors.append("Workspace generated or leaked causal conclusion semantics.")
            print("[FAIL] Causality guardrail failed.")
        else:
            print("[PASS] No causal conclusion generated.")

        if view.metadata["ground_truth_used"] is not False:
            errors.append("Ground Truth flag is not false.")
            print("[FAIL] Ground Truth isolation failed.")
        else:
            print("[PASS] Ground Truth used: false.")

        print("=" * 72)
        if errors:
            print(f"DAY 10 VALIDATION FAILED WITH {len(errors)} ERROR(S):")
            for error in errors:
                print(f"  - {error}")
            return 1

        print("DAY 10 VALIDATION PASSED - INVESTIGATION WORKSPACE READY.")
        print("=" * 72)
        return 0
    except Exception as exc:
        print(f"[ERROR] Exception during Day 10 validation: {exc}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(run_day10_validation())
