# MDARIX R1 — Day 26 Ask MDARIX Foundation Report

## Scope

Day 26 introduces a controlled, deterministic natural-language interpretation
foundation. It is an investigation interface, not an unrestricted chatbot and
does not implement Day 27 cross-system causality or an NL engine.

## Implemented

- Typed `InvestigationSession`, `InvestigationQuery`, and
  `InvestigationSpecification` contracts.
- Deterministic query normalization and a deliberately small intent vocabulary.
- Explicit `READY`, `REQUIRES_CLARIFICATION`, `NOT_FOUND`, and `INVALID` outcomes.
- ProductVersion references are retained when present; comparison requests
  require two versions instead of guessing.
- Explicit `CURRENT`, `EVENT_AS_OF`, and `KNOWN_AS_OF` temporal modes.
- Server-date-relative windows and invalid date-range rejection.
- Retrieval-scope contract requiring tenant scoping, authorization, and AI-safe
  field filtering before any future retrieval/model execution.
- Untrusted question text cannot grant authority or widen scope.

## Validation

`tests/test_day26_query_interpreter.py`: **4 passed**.

Python compilation and `git diff --check` also pass. The implementation is a
foundation only: authenticated API orchestration, database persistence,
authorized product/version resolution, retrieval execution, and UI wiring remain
subsequent Day 26 work and are not falsely represented as complete here.

