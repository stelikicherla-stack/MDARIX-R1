# MDARIX R1 Security Baseline

## Status

PROPOSED for Day 1 architecture freeze.

## Scope

R1 is local development, but architecture must not create an enterprise security dead end.

## Tenant Isolation

Every persisted business object has tenant context. APIs derive tenant context from authenticated session or service context. Cross-tenant leakage target is zero.

## Authentication and Authorization

Authentication is required for product workflows. Authorization uses RBAC and least privilege. Material decision actions require authorized roles.

## Secrets

Secrets are not hardcoded. `.env` remains local and ignored. Example files use placeholders only.

## Data Protection

Use encryption in transit for deployed environments. Encryption at rest is an infrastructure assumption for production. Local R1 development documents the boundary but does not implement production deployment.

## Input and File Validation

All API inputs and uploaded files require validation. Evidence extraction must retain source references and reject unsupported file assumptions.

## Prompt Injection and AI Data Leakage

AI tools receive constrained context. Prompts must not allow retrieved evidence to override system policy. Tool boundaries enforce tenant, investigation, and permission scope.

## Audit and Provenance

Material reads, writes, AI executions, brief generation, and human decisions emit audit/provenance records.

## Tests

R1 test architecture includes cross-tenant isolation tests, authorization tests, audit/provenance tests, and secret-exclusion checks.
