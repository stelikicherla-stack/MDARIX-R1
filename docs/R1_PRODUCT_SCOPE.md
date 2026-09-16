# MDARIX R1 Product Scope

## Status

PROPOSED for Day 1 architecture freeze.

## Positioning

MDARIX R1 is a Medical Device Lifecycle Investigation & Decision Intelligence foundation. It is the first three-week working vertical slice of MDARIX, not a commercial release.

MDARIX helps regulated healthcare and medical-device companies investigate what happened, understand what changed, challenge why it happened, and determine what could happen next.

## Core Promise

- Understand what happened.
- Challenge why it happened.
- Determine what could happen next.

## R1 Objective

Can MDARIX correctly reconstruct a medical-device investigation and produce a trustworthy Reality Investigation Brief?

## Product Principle

MDARIX is not another QMS or PLM. MDARIX is the intelligence layer connecting enterprise systems.

R1 is a system of intelligence, not a system of record.

## Core Object

Product is the highest-level business object. Complaints, investigations, changes, risks, components, suppliers, lots, evidence, hypotheses, unknowns, and decisions connect back to product reality.

## Primary User

The primary R1 user is an authorized medical-device investigation lead or quality/regulatory decision reviewer responsible for understanding investigation evidence and recording a human decision.

## Primary Journey

User opens investigation -> selects product -> reviews Product 360 -> MDARIX reconstructs lifecycle timeline -> evidence is retrieved -> relationships are displayed in the Reality Graph -> AI Investigator identifies patterns -> hypotheses are generated -> evidence and contradictions are mapped -> AI Challenger challenges the leading hypothesis -> Unknowns Radar identifies missing information -> Failure Chain is constructed -> constrained scenario is explored -> Reality Investigation Brief is generated -> authorized human reviews -> human decision is recorded -> provenance and audit are retained.

## R1 Investigation Lifecycle

CONNECT -> RECONSTRUCT -> RELATE -> INVESTIGATE -> CHALLENGE -> IDENTIFY UNKNOWNS -> BUILD FAILURE CHAIN -> EXPLORE CONSTRAINED SCENARIOS -> DECIDE.

## Must-Have Capability Boundaries

R1 defines architecture for multi-source ingestion, canonical lifecycle modeling, normalization, identity resolution, evidence storage, Product 360, Reality Graph, temporal intelligence, evidence intelligence, investigation workspace, AI Investigator, hypotheses, AI Challenger, Unknowns Radar, failure-chain intelligence, constrained counterfactuals, Decision Center, Reality Investigation Brief, human review, provenance, Golden Dataset, Ground Truth, evaluation harness, REST API, MCP-ready tool boundaries, RBAC, tenant isolation, observability, and CI/CD foundation.

## Out of Scope

- Full enterprise QMS replacement
- PLM, ERP, or MES replacement
- Autonomous regulatory, CAPA, recall, safety, product release, risk acceptance, or investigation closure decisions
- Unrestricted AI actions
- Production live enterprise connectors
- Full multi-agent swarm
- Neo4j on Day 1
- Advanced digital twin
- Unrestricted simulation
- Full global regulatory automation
- Production-scale enterprise deployment
- All later commercial-release roadmap capabilities

## Human Authority

AI recommends. Authorized humans decide.

AI may retrieve, correlate, reconstruct, summarize, generate and challenge hypotheses, identify missing evidence, identify contradictions, suggest failure chains, explore constrained scenarios, and draft investigation briefs.

AI must not autonomously make final material regulated decisions.

## Primary Example

Primary R1 walkthrough question: Why did intermittent device shutdown complaints increase after Product Rev D was introduced?

The architecture must support a conclusion such as: Component/supplier change is the leading hypothesis, but causality is not established.
