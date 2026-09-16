# MDARIX R1 Day 2 Implementation Contract

## Status

PROPOSED for Day 1 architecture freeze.

## Day 2 Scope

Day 2 is PostgreSQL foundation plus initial canonical schema. Day 2 may create migrations and initial schema, but Day 1 does not execute it.

## Table Candidates

Tenant, Product, ProductVersion, Component, Supplier, ManufacturingSite, LotBatch, Requirement, Change, Complaint, Investigation, Risk, FailureMode, Control, Evidence, Hypothesis, Unknown, FailureChain, Scenario, Decision, AIExecution, HumanReview, and selected relationship tables.

## Primary Keys

Use UUID-style primary keys. Avoid source-system IDs as primary keys.

## Tenant Strategy

Every tenant-owned table includes `tenant_id`. Foreign keys preserve tenant-scoped integrity. Cross-tenant joins require explicit service-layer authorization.

## Timestamps

Use explicit temporal fields: source, event, effective, recorded, ingestion, investigation, AI execution, and decision timestamps as applicable.

## Provenance and Audit

Source-derived records support source system, source record ID/version, raw payload reference, checksum, and data quality status. Material changes create audit records.

## Relationship Strategy

Use explicit relationship tables when relationships need evidence, confidence, effective dates, provenance, contradiction status, or lifecycle meaning.

## JSONB Usage

Use JSONB for raw payload references, structured extraction payloads, and provider-specific metadata where strict columns would create churn. Do not hide canonical fields in JSONB.

## Vector Strategy

Use pgvector for embeddings associated with evidence, excerpts, or retrieval units. Store embedding model metadata and evidence references.

## Indexes

Index tenant IDs, source IDs, investigation IDs, product IDs, relationship endpoints, temporal query fields, and vector retrieval columns where needed.

## Foreign Keys

Prefer explicit foreign keys for canonical relationships. Avoid circular dependencies by using link tables and nullable review references where necessary.

## Migration Strategy

Use Alembic. Migrations must be deterministic, reviewed, reversible where practical, and tested against the Day 0 PostgreSQL container.

## Seed/Reference Data

Seed only controlled reference data or Golden Dataset fixtures when explicitly in scope. Do not seed production-like secrets.

## Extensions

Required extension: `vector`.

## Database Test Strategy

Use pytest to verify migrations, extension availability, empty baseline state, tenant isolation constraints, relationship provenance, and vector table readiness.
