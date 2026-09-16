# MDARIX R1 Hypothesis Edge Case Matrix

| Case | Expected Behavior |
| --- | --- |
| One plausible hypothesis | Preserve as testable explanation |
| Two/three hypotheses | Preserve competition |
| Multiple causes | Multi-factor hypothesis allowed |
| No viable hypothesis | `NO_CURRENTLY_SUPPORTABLE_HYPOTHESIS` |
| Strong support + contradiction | `MIXED_EVIDENCE` |
| Missing evidence | Evidence gaps explicit |
| Incomplete traceability | Contextual/gap relationship |
| Pre-change complaints | Contradiction/temporal nuance |
| Historical root cause | Source attributed only |
| Retrieval score | Not used as strength/probability |
| Graph path | Not used as causality |
| Leading prompt | Does not force single cause |
| Prompt injection | Treated as evidence data |
| Current vs known-as-of | Future evidence excluded in known view |
| Correct abstention | PASS behavior |
