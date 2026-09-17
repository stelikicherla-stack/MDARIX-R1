from __future__ import annotations
import csv, hashlib, io, json
from dataclasses import dataclass, field, asdict
from datetime import datetime

FAILURE_CATEGORIES = {"AUTHENTICATION", "CONNECTIVITY", "TIMEOUT", "SOURCE_SCHEMA", "MAPPING", "TRANSFORMATION", "IDENTITY", "TEMPORAL", "CANONICAL_VALIDATION", "DATABASE", "RATE_LIMIT", "UNKNOWN"}

@dataclass(frozen=True)
class ConnectionConfig:
    tenant_id: str; connection_id: str; name: str; connector_type: str; source_system_type: str; endpoint: str | None = None; authentication_type: str = "NONE"; credential_ref: str | None = None; configuration_version: str = "v1"; status: str = "DRAFT"
    def safe_dict(self): return {"tenant_id":self.tenant_id,"connection_id":self.connection_id,"name":self.name,"connector_type":self.connector_type,"source_system_type":self.source_system_type,"endpoint":self.endpoint,"authentication_type":self.authentication_type,"credential_ref":self.credential_ref,"configuration_version":self.configuration_version,"status":self.status}

class Connector:
    def __init__(self, config: ConnectionConfig, records=None): self.config=config; self.records=records or []
    def validate_configuration(self):
        if self.config.connector_type not in {"FILE","REST","DATABASE"}: return {"status":"INVALID_CONFIGURATION","category":"SOURCE_SCHEMA"}
        return {"status":"VALID","category":None}
    def test_connection(self): return {"status":"SUCCESS","connector_type":self.config.connector_type}
    def discover_schema(self):
        sample=self.records[0] if self.records else {}; return {"fields": {k:type(v).__name__ for k,v in sample.items()},"source_object":self.config.source_system_type}
    def read_records(self): return list(self.records)
    def read_incremental(self, watermark=None): return list(self.records)
    def get_health(self): return {"status":"HEALTHY","last_failure":None,"records_processed":len(self.records)}
    def get_source_metadata(self): return {"source_system_type":self.config.source_system_type,"connector_type":self.config.connector_type}

class FileConnector(Connector):
    @classmethod
    def from_csv(cls, config, text): return cls(config, list(csv.DictReader(io.StringIO(text))))
    @classmethod
    def from_json(cls, config, text): return cls(config, json.loads(text))

class RestConnector(Connector): pass
class DatabaseConnector(Connector): pass

@dataclass
class MappingDefinition:
    source_object: str; target_entity: str; mapping_version: str; rules: dict[str, dict]; status: str = "DRAFT"
    def fingerprint(self): return hashlib.sha256(json.dumps(asdict(self),sort_keys=True).encode()).hexdigest()

def transform(value, operation=None):
    if value is None: return None
    if operation in (None, "identity"): return value
    if operation == "trim": return str(value).strip()
    if operation == "lower": return str(value).lower()
    if operation == "upper": return str(value).upper()
    if operation == "string": return str(value)
    if operation == "date": return datetime.fromisoformat(str(value).replace("Z", "+00:00")).isoformat()
    if operation == "boolean": return str(value).lower() in {"true","1","yes","y"}
    raise ValueError(f"unsupported transformation: {operation}")

def validate_mapping(mapping: MappingDefinition):
    errors=[]
    for source, rule in mapping.rules.items():
        target=rule.get("target_field","")
        if not target or not target.startswith(mapping.target_entity + ".") or (mapping.target_entity == "Complaint" and target.endswith(".id")): errors.append({"category":"MAPPING","source_field":source,"message":"Target is incompatible with the declared canonical entity"})
        if rule.get("transform") not in {None,"identity","trim","lower","upper","string","date","boolean"}: errors.append({"category":"TRANSFORMATION","source_field":source,"message":"Transformation is not controlled"})
    return {"status":"VALID" if not errors else "INVALID","errors":errors}

def preview(records, mapping: MappingDefinition):
    validation=validate_mapping(mapping)
    if validation["status"] != "VALID": return {"status":"BLOCKED","errors":validation["errors"],"records":[]}
    result=[]; failures=[]
    for index, record in enumerate(records):
        canonical={}; record_failures=[]
        for source, rule in mapping.rules.items():
            if rule.get("required") and source not in record: record_failures.append({"category":"MAPPING","record":index,"field":source,"message":"Required field missing"}); continue
            try: canonical[rule["target_field"]]=transform(record.get(source),rule.get("transform"))
            except (ValueError, TypeError) as exc: record_failures.append({"category":"TRANSFORMATION","record":index,"field":source,"message":str(exc)})
        if record_failures: failures.extend(record_failures)
        else: result.append(canonical)
    return {"status":"VALID" if not failures else "PARTIAL","records":result,"failures":failures}

def reconcile(source_count, accepted, rejected, unresolved, duplicates, persisted, errors):
    accounted=accepted+rejected+unresolved+duplicates
    return {"source_count":source_count,"accepted":accepted,"rejected":rejected,"unresolved":unresolved,"duplicates":duplicates,"persisted":persisted,"errors":errors,"accounted":accounted,"status":"COMPLETE" if accounted==source_count else "RECONCILIATION_ERROR"}

def resolve_identity(value, candidates):
    matches=[candidate for candidate in candidates if candidate.get("key") == value]
    return {"status":"RESOLVED","match":matches[0]} if len(matches)==1 else {"status":"AMBIGUOUS" if len(matches)>1 else "UNRESOLVED","match":None}

CONNECTOR_STATES = {"HEALTHY", "DEGRADED", "FAILED", "STALE", "DISABLED", "UNKNOWN"}

def source_record_fingerprint(tenant_id: str, source_system: str, source_record_id: str, source_record_version: str | None, record: dict) -> str:
    payload = json.dumps({"tenant_id": tenant_id, "source_system": source_system, "source_record_id": source_record_id, "source_record_version": source_record_version, "record": record}, sort_keys=True, default=str).encode()
    return hashlib.sha256(payload).hexdigest()

@dataclass
class ConnectorRun:
    tenant_id: str; connection_id: str; run_id: str; state: str = "UNKNOWN"; processed: int = 0; accepted: int = 0; rejected: int = 0; duplicates: int = 0; failures: list[dict] = field(default_factory=list); seen_fingerprints: set[str] = field(default_factory=set)
    def __post_init__(self):
        if self.state not in CONNECTOR_STATES: raise ValueError("unsupported connector state")
    def ingest(self, records: list[dict], *, source_system: str, required_fields: set[str]) -> dict:
        accepted = []
        for record in records:
            self.processed += 1
            missing = sorted(required_fields - set(record))
            if missing:
                self.rejected += 1; self.failures.append({"category":"MAPPING","reason":"REQUIRED_FIELD_MISSING","fields":missing}); continue
            fp = source_record_fingerprint(self.tenant_id, source_system, str(record.get("source_record_id")), str(record.get("source_record_version")), record)
            if fp in self.seen_fingerprints:
                self.duplicates += 1; continue
            self.seen_fingerprints.add(fp); self.accepted += 1; accepted.append(record)
        self.state = "DEGRADED" if self.failures else "HEALTHY"
        return {"status":"PARTIAL" if self.failures and accepted else "FAILED" if self.failures and not accepted else "COMPLETE", "accepted":accepted, "processed":self.processed, "duplicates":self.duplicates, "failures":self.failures, "state":self.state}

def detect_schema_drift(expected_fields: set[str], actual_fields: set[str]) -> dict:
    missing = sorted(expected_fields - actual_fields); added = sorted(actual_fields - expected_fields)
    return {"status":"DRIFT" if missing or added else "MATCH", "missing":missing, "added":added}
