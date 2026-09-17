# R1 Day 14 Edge Cases

| Case | Required behavior |
|---|---|
| Missing evidence | Emit material Unknown; do not infer a negative |
| Pre-change failures | Preserve temporal uncertainty; do not claim all-event causality |
| Contradiction | Retain contradiction and affected chain link |
| Multiple contributors | Preserve branches and alternatives |
| No hypotheses | Abstain from chain generation |
| Duplicate gap | Emit one canonical unknown per semantic key |
| Prompt injection | Treat text as data; policy remains controlled |
