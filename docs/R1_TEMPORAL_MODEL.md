# MDARIX R1 Temporal Model

## Status

PROPOSED for Day 1 architecture freeze.

## Principle

Time is a first-class architecture concern. MDARIX must answer what was believed to be true at decision time and what became known later.

## Timestamp Types

- Source timestamp
- Event timestamp
- Effective timestamp
- Recorded timestamp
- Ingestion timestamp
- Investigation timestamp
- AI execution timestamp
- Decision timestamp

Do not collapse temporal reality into only `created_at` and `updated_at`.

## Temporal Rules

Source timestamps come from external records. Event timestamps describe when the lifecycle event occurred. Effective timestamps describe when a state became true. Recorded timestamps describe when a source system recorded the state. Ingestion timestamps describe when MDARIX received it. Investigation timestamps describe investigation actions. AI execution timestamps describe model/tool activity. Decision timestamps describe human authority.

## Temporal Contradictions

The system must detect and preserve incorrect timelines, late-arriving evidence, and evidence that changes the interpretation of an earlier decision.
