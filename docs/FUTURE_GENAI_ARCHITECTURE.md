# Stage 3 Governed GenAI

GenAI outputs are drafts and are labelled as AI-generated. Inputs are tenant-scoped structured records plus authorized evidence. Each execution must retain tenant, actor, Case Context, model, prompt/configuration version, evidence references, limitations, guardrail outcome, and correlation ID. AI may summarize, compare, identify gaps, and suggest next steps; it cannot approve, reject, declare root cause, or modify approved records.

The MVP provider boundary is a `ModelProvider` contract. Provider credentials remain server-side and are never returned to clients.
