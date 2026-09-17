# R1 Integration Validation Evidence

| Case | Expected | Actual | Result |
|---|---|---|---|
| Customer A/B/C shared connector | Same connector, semantic canonical output | `FileConnector` used for all three configurations | PASS |
| Declarative mapping | Different source names map to canonical fields | Complaint identifier/product/version/event normalized | PASS |
| Unsupported target mapping | Block before ingestion | Validation returns mapping error | PASS |
| Transformation failure | Record visible and accounted | Partial preview with transformation failure | PASS |
| Ambiguous identity | No silent merge | `AMBIGUOUS` controlled result | PASS |
| Reconciliation | Every source record accounted | Count equation enforced | PASS |
| Secret handling | No credential values exposed | Credential reference only | PASS |

Connector/configuration versions and source lineage are retained in the gateway contracts. This artifact is internal engineering validation, not a commercial connector certification.
