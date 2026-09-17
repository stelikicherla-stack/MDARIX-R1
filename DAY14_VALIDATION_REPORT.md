# MDARIX R1 Day 14 Validation Report

Day 14 implemented the controlled Unknowns Radar and Failure Chain layers over the persisted Day 12–13 outputs.

Validated capabilities:

- material unknown detection and deduplication
- explicit unknown/absence semantics
- contradiction and temporal metadata preservation
- broken-chain and abstention behavior
- epistemic link status preservation
- graph-path safety: a graph path is not causal proof
- tenant-scoped persistence and API routes

The live remediation also established that the seven AsterFlow investigations (`INV-001` through `INV-007`) are correctly associated in PostgreSQL. Product 360 historical Event-as-of views may correctly show zero investigations before their opening dates; the live tenant-scoped investigation access route preserves access to the actual associated records.

Day 14 implementation details are documented in [docs/R1_DAY14_VALIDATION_REPORT.md](docs/R1_DAY14_VALIDATION_REPORT.md), [docs/R1_DAY14_UNKNOWNS_FAILURE_CHAIN_IMPLEMENTATION.md](docs/R1_DAY14_UNKNOWNS_FAILURE_CHAIN_IMPLEMENTATION.md), and the live UI validation checklist.
