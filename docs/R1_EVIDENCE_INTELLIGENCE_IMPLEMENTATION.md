# MDARIX R1 Evidence Intelligence Implementation Specification

## 1. Executive Summary & Purpose

Evidence Intelligence in MDARIX R1 provides **Traceable Evidence Understanding**. Evidence is a **first-class MDARIX lifecycle object** with full identity, source preservation, temporal metadata, semantic chunks, precise source anchors, canonical entity links, and audit provenance.

## 2. Evidence Architecture & Domain Model

- **First-Class Identity**: Identity is established via stable UUIDs and source references. Evidence is not reduced to a text field or vector embedding.
- **Source Preservation**: Original content, raw payloads, document references, and metadata are retained immutably. Derived extractions never overwrite source evidence.
- **Controlled Evidence Vocabulary**: Includes `VALIDATION_REPORT`, `SUPPLIER_CHANGE_NOTIFICATION`, `MANUFACTURING_RECORD`, `ENGINEERING_CHANGE_RECORD`, `COMPLAINT_ATTACHMENT`, `INVESTIGATION_RECORD`, `TEST_RESULT`, `RISK_RECORD`, `CONTROL_EVIDENCE`, `PRODUCT_CONFIGURATION_RECORD`.

## 3. Extraction Pipeline

```
SOURCE EVIDENCE
      ↓
CONTENT ACCESS & NORMALIZATION
      ↓
DETERMINISTIC EXTRACTION
      ↓
EVIDENCE CHUNKING
      ↓
GENAI NARRATIVE EXTRACTION (Pydantic Schema Validation)
      ↓
SOURCE ANCHORING & GROUNDING VALIDATION
      ↓
ENTITY LINKING (Canonical Lookup & Unresolved References)
      ↓
AI EXECUTION PROVENANCE (ai_executions)
      ↓
PERSISTENCE & EVALUATION
```

## 4. Grounding & Hallucination Defense

- **Source Anchor Mandatory Coverage**: 100% of material accepted observations must possess valid source locators (paragraph index, excerpt, or character range).
- **Prompt Injection Defense**: Evidence content is treated strictly as untrusted data input. Instruction markers (e.g. "ignore previous instructions") are neutralized and logged.
- **Ground Truth Isolation**: Ground Truth (`evaluation/ground_truth/`) remains 100% isolated to evaluation scripts. Ground Truth leakage = 0.

## 5. Support / Contradiction Semantics

Observations are linked to propositions using explicit relations:
- `SUPPORT`: Evidence statement confirms or provides positive evidence for a proposition.
- `CONTRADICT`: Evidence statement directly conflicts with or weakens a proposition.
- `NEUTRAL_CONTEXTUAL`: Evidence statement provides background without direct assertion.

## 6. Tenant Security & Content Access

Content access is strictly tenant-scoped via `tenant_id`. Filesystem references outside the tenant workspace trigger `ContentSecurityError` and are rejected.
