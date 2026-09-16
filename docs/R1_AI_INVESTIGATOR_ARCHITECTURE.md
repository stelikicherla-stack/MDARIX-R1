# MDARIX R1 AI Investigator Architecture

```text
Investigation Workspace UI
        |
        v
InvestigationAnalysis API
        |
        v
Day 10 InvestigationWorkspaceResponse
        |
        +--> Product / ProductVersion scope
        +--> Temporal context
        +--> Reality Graph context
        +--> Day 8 evidence observations and anchors
        +--> Day 9 retrieval context
        +--> Limitations and guardrails
        |
        v
Context Policy Layer
        |
        v
Controlled AI Investigator Provider
        |
        v
Structured InvestigationAnalysis
        |
        v
Grounding Validator
        |
   +----+----+
   |         |
Accepted  Rejected/Flagged
   |
   v
AIExecution Provenance
   |
   v
Investigation Workspace Presentation
```

## Tenant Boundary

Tenant scoping is resolved before workspace construction. Day 11 does not query arbitrary tenant data.

## Deterministic Authority

Product scope, version scope, temporal filtering, relationship identity, retrieval filtering, and source-anchor existence remain deterministic responsibilities.

## AI Responsibility

The investigator organizes observations, relationships, possible explanations, contradictions, missing information, questions, and limitations from controlled context.
