from types import SimpleNamespace
from uuid import uuid4

from backend.app.governance_router import ASK_FEATURE, FEATURE, bootstrap
from backend.app.db.models.foundation import FeatureEntitlement, PlanDefinition, TenantPlanAssignment, ApprovalAuthority, SegregationOfDutiesPolicy


class _Query:
    def __init__(self, rows): self.rows=rows; self.criteria={}
    def filter_by(self, **criteria): self.criteria=criteria; return self
    def first(self): return next((row for row in self.rows if all(getattr(row,key,None)==value for key,value in self.criteria.items())), None)


class _DB:
    def __init__(self, plan): self.rows={PlanDefinition:[plan],FeatureEntitlement:[],TenantPlanAssignment:[],ApprovalAuthority:[],SegregationOfDutiesPolicy:[]}; self.commits=0
    def query(self, model): return _Query(self.rows[model])
    def add(self, row): self.rows[type(row)].append(row)
    def flush(self): return None
    def commit(self): self.commits += 1


def test_r1_governance_bootstrap_provisions_ask_idempotently():
    plan=SimpleNamespace(id=uuid4(), code="R1_GOVERNANCE_DEMO")
    tenant=SimpleNamespace(id=uuid4())
    db=_DB(plan)
    bootstrap(db,tenant)
    bootstrap(db,tenant)
    ask=[row for row in db.rows[FeatureEntitlement] if row.feature_code==ASK_FEATURE]
    signature=[row for row in db.rows[FeatureEntitlement] if row.feature_code==FEATURE]
    assignments=db.rows[TenantPlanAssignment]
    assert len(ask)==1 and ask[0].enabled is True and ask[0].status=="ACTIVE"
    assert len(signature)==1 and len(assignments)==1
    assert db.commits==1
