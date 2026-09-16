# MDARIX R1 Evidence Claim Semantics

## 1. Controlled Vocabulary

To prevent confusion between raw data, extracted statements, and derived hypotheses, MDARIX enforces strict claim vocabulary:

1. **`SOURCE CONTENT`**: Original text/document content as ingested from source system.
2. **`EXPLICIT SOURCE STATEMENT`**: Verbatim statement directly present in source text (e.g. "Validation VT-204 passed").
3. **`STRUCTURED EXTRACTION`**: Field key-value pair extracted deterministically (e.g., `date = 2026-02-10`).
4. **`AI-EXTRACTED OBSERVATION`**: Statement extracted via narrative AI model with Pydantic validation.
5. **`DETERMINISTIC DERIVATION`**: Computed relationship or metadata assertion derived by rule code.
6. **`SUPPORT`**: Evidence relation strengthening an explicit test proposition.
7. **`CONTRADICTION`**: Evidence relation incompatible with or weakening a proposition.
8. **`NEUTRAL_CONTEXTUAL`**: Background context providing situational information.
9. **`LIMITATION`**: Explicitly documented missing field or traceability gap.
10. **`UNKNOWN`**: Explicit missing knowledge node.
11. **`HYPOTHESIS`**: Proposed causal explanation (Week 2 Day 12).
12. **`HUMAN DECISION`**: Regulatory disposition authorized by a human reviewer.
