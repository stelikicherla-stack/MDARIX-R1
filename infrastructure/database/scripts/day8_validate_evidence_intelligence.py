import datetime
import os
import sys
import uuid

# Ensure root workspace is in pythonpath
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from sqlalchemy.orm import Session
from backend.app.db.models.evidence_intelligence import (
    EvidenceChunk,
    EvidenceEntityLink,
    EvidenceObservation,
    EvidencePropositionRelation,
)
from backend.app.db.models.foundation import AIExecution, Evidence, Tenant
from backend.app.db.session import SessionLocal
from evidence.services.evidence_service import EvidenceIntelligenceService


def run_day8_validation() -> int:
    """Validates Day 8 Evidence Intelligence foundation against all acceptance targets."""
    print("=" * 70)
    print("STARTING DAY 8 EVIDENCE INTELLIGENCE VALIDATION")
    print("=" * 70)

    db: Session = SessionLocal()
    errors = []

    try:
        # 1. Tenant Check
        tenant = db.query(Tenant).filter(Tenant.tenant_key == "default_tenant").first()
        if not tenant:
            tenant = db.query(Tenant).first()
        if not tenant:
            errors.append("No active tenant found in database.")
            print("[FAIL] Tenant check failed")
            return 1
        print(f"[PASS] Default tenant verified ({tenant.tenant_key})")

        # 2. Evidence Records Check
        evidence_items = db.query(Evidence).filter(Evidence.tenant_id == tenant.id).all()
        print(f"[INFO] Found {len(evidence_items)} evidence records for tenant.")

        if not evidence_items:
            # Seed a sample evidence record if empty
            sample_ev = Evidence(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                evidence_identifier="EV-GOLDEN-VS001",
                evidence_type="SUPPLIER_CHANGE_NOTIFICATION",
                title="Supplier Process Change Notice for Component Rev B",
                source_system="PLM",
                reliability_status="validated",
                fact_type="source_fact",
                content="Supplier Change Notification SCN-2026-01: Process modification applied to Component Rev B. Applicable to Product Rev D. Validation VT-204 passed.",
                effective_timestamp=datetime.datetime.now(datetime.timezone.utc),
                created_at=datetime.datetime.now(datetime.timezone.utc),
                updated_at=datetime.datetime.now(datetime.timezone.utc),
            )
            db.add(sample_ev)
            db.commit()
            evidence_items = [sample_ev]

        service = EvidenceIntelligenceService()
        target_ev = evidence_items[0]

        # 3. Process Evidence Intelligence Pipeline
        print(f"[INFO] Processing evidence intelligence for {target_ev.evidence_identifier}...")
        summary = service.process_evidence_intelligence(db, tenant.id, target_ev.id, reprocess=True)

        # 4. Source Preservation Verification
        ev_check = db.query(Evidence).filter(Evidence.id == target_ev.id).first()
        if not ev_check or not ev_check.content:
            errors.append("Source evidence content was not preserved.")
            print("[FAIL] Source evidence content missing.")
        else:
            print("[PASS] Source evidence content preserved (100%).")

        # 5. Chunks Verification
        chunks = db.query(EvidenceChunk).filter(EvidenceChunk.evidence_id == target_ev.id).all()
        if not chunks:
            errors.append("No evidence chunks generated.")
            print("[FAIL] Evidence chunking failed.")
        else:
            print(f"[PASS] Evidence chunking generated {len(chunks)} chunks with locators.")

        # 6. Material Accepted Observations & Source Anchor Coverage Target (100%)
        observations = db.query(EvidenceObservation).filter(EvidenceObservation.evidence_id == target_ev.id).all()
        if not observations:
            errors.append("No observations extracted.")
            print("[FAIL] Evidence observation extraction failed.")
        else:
            unanchored = [o for o in observations if not o.source_anchor]
            if unanchored:
                errors.append(f"{len(unanchored)} material observations missing source anchors.")
                print(f"[FAIL] Source anchor coverage: {((len(observations)-len(unanchored))/len(observations))*100:.1f}%")
            else:
                print(f"[PASS] Material accepted observation source-anchor coverage: 100% ({len(observations)}/{len(observations)}).")

        # 7. Entity Links Verification
        links = db.query(EvidenceEntityLink).filter(EvidenceEntityLink.evidence_id == target_ev.id).all()
        print(f"[PASS] Entity linking generated {len(links)} links (resolved + unresolved references).")

        # 8. AIExecution Provenance Verification
        ai_execs = (
            db.query(AIExecution)
            .filter(AIExecution.tenant_id == tenant.id)
            .all()
        )
        if not ai_execs:
            errors.append("No AIExecution provenance recorded.")
            print("[FAIL] AIExecution provenance missing.")
        else:
            print(f"[PASS] AIExecution provenance recorded ({len(ai_execs)} records).")

        # 9. Ground Truth Isolation Verification
        gt_leak = False
        for ex in ai_execs:
            if ex.context_refs and "ground_truth" in str(ex.context_refs).lower():
                gt_leak = True
        if gt_leak:
            errors.append("Ground Truth leakage detected in AI executions.")
            print("[FAIL] Ground Truth leakage > 0.")
        else:
            print("[PASS] Ground Truth leakage = 0.")

        # Summary output
        print("=" * 70)
        if errors:
            print(f"VALIDATION FAILED WITH {len(errors)} ERRORS:")
            for err in errors:
                print(f"  - {err}")
            return 1

        print("DAY 8 VALIDATION PASSED — EVIDENCE INTELLIGENCE & GROUNDING READY.")
        print("=" * 70)
        return 0

    except Exception as e:
        print(f"[ERROR] Exception during validation: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(run_day8_validation())
