# Stage 3 Controlled Agents

The agent catalog contains Product Intelligence, Complaint Signal, Investigation, Evidence, Hypothesis, Challenger, Traceability, and Decision Brief agents. Agents are read/analyze/summarize/suggest only. Approval, rejection, regulatory conclusions, cross-tenant retrieval, and writes to signed records require explicit human authority and are blocked by policy.

The authenticated `/api/v1/ai/agents/catalog` contract exposes these guardrails to the application without exposing implementation secrets.
