# Stage 2 — Data platform foundation

PostgreSQL/pgvector remains the system of record. Stage 2 introduces the durable transactional-outbox table and model without adding Kafka, Neo4j, or OpenSearch. Object storage, search, graph, analytics, workflow, model, and email capabilities remain explicit service ports for later adapters.
