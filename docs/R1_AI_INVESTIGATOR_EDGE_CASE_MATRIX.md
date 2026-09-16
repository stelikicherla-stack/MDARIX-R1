# MDARIX R1 AI Investigator Edge Case Matrix

| Case | Detection | Prevention | Test |
| --- | --- | --- | --- |
| Hallucinated evidence | Grounding validator | Reject ungrounded items | Day 11 grounding tests |
| Unsupported causal statement | Causal phrase scan | No causal conclusion guardrail | Leading-question tests |
| Contradiction omitted | Contradiction item count | Preserve tension-bearing evidence | Day 11 validator |
| Future evidence leakage | Known-as-of payload scan | Day 10 temporal context | Known-as-of test |
| Wrong version contamination | ProductVersion context | Day 10 scope | Regression |
| Wrong tenant evidence | Tenant filters | Default tenant scoping | Regression |
| Ground Truth leakage | Payload scan | Runtime path excludes ground_truth | Validator |
| Source root cause adopted | Source-attributed type | Historical conclusion rule | Historical conclusion test |
| Evidence prompt injection | Instruction-like content detection | Treat evidence as data | Prompt injection test |
| Leading question | Leading-term detection | Premise-resistant limitations | Leading question test |
| Retrieval rank as strength | Guardrail text | No strength conversion | Contract tests |
| Graph causality leap | Guardrail text | Relationship semantic type | Contract tests |
| Missing evidence treated as false | Limitation semantics | Missing-information type | Contract tests |
| Provider failure hidden | API error path | Structured error | Service errors |
| Provenance incomplete | AIExecution check | Persist structured output | Provenance test |
