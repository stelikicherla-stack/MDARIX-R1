# MDARIX R1 Temporal Reality Implementation

## Purpose

Temporal Reality distinguishes what happened, when it became effective, when it was recorded, and when MDARIX learned it.

## Time Dimensions

- Event time: when the lifecycle event occurred.
- Effective time: when a state became true.
- Recorded time: when a source recorded it.
- Knowledge/ingestion time: when MDARIX received or could use it.

## Timeline Events

Day 7 implements `TimelineEvent` with controlled categories:

- PRODUCT
- DESIGN
- COMPONENT
- SUPPLIER
- MANUFACTURING
- FIELD
- INVESTIGATION
- RISK
- EVIDENCE

## Event-As-Of

`mode=event` filters by event/effective semantics. It answers what had happened by time T.

## Known-As-Of

`mode=known` filters by knowledge availability, recorded time, or event time fallback. It answers what MDARIX could know by time T.

## Late-Arriving Evidence

Events mark `late_arriving=true` when evidence/source time precedes MDARIX knowledge time. This preserves VS005/VS007 temporal behavior.

## Historical Configuration

Product versions remain distinct. Rev C and Rev D views are not collapsed.

## Limitations

Day 7 does not infer root cause, risk ranking, CAPA need, or regulatory conclusions.
