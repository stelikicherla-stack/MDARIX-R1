# MDARIX R1 Evidence Temporal Model Diagram

```mermaid
timeline
    title Evidence Timeline Semantics vs Knowledge Availability
    2026-02-10 : Event Occurred (event_timestamp)
    2026-02-12 : Evidence Document Created (recorded_timestamp)
    2026-02-15 : Investigation Closed
    2026-02-20 : Evidence Received / Ingested into MDARIX (ingestion_timestamp / known_as_of)
```

**Key Principle**:
Late-arriving evidence (`received_date` > `investigation_closed_date`) does NOT backdate knowledge. Historical queries using `known_as_of = 2026-02-15` will correctly exclude evidence received on `2026-02-20`.
