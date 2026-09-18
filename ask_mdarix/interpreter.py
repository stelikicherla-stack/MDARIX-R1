import re
from datetime import date, timedelta

from .models import InvestigationSpecification, InterpretationStatus, TemporalMode


_INTENT_PATTERNS = (
    ("COMPARE_PRODUCT_VERSIONS", re.compile(r"\b(compare|versus|vs\.?|difference between)\b")),
    ("RETRIEVE_EVIDENCE_CONTEXT", re.compile(r"\b(evidence|proof|records?)\b")),
    ("IDENTIFY_MISSING_INFORMATION", re.compile(r"\b(what (don'?t|do not) we know|missing|unknowns?)\b")),
    ("INVESTIGATE_TIME_WINDOW", re.compile(r"\b(before|after|between|since|as of|last \d+ days?)\b")),
    ("INVESTIGATE_COMPLAINT_SIGNAL", re.compile(r"\b(complaints?|shutdown|increased|increase|signal)\b")),
)


class QueryInterpreter:
    """Deterministic, non-authorizing interpreter for controlled questions."""

    def __init__(self, *, server_today: date | None = None):
        self.server_today = server_today or date.today()

    @staticmethod
    def normalize(question: str) -> str:
        value = re.sub(r"\s+", " ", question.strip().lower())
        return value.rstrip("?.!")

    def interpret(self, question: str) -> InvestigationSpecification:
        normalized = self.normalize(question)
        if not normalized:
            return InvestigationSpecification(status=InterpretationStatus.INVALID, normalized_question="", limitations=["Question is required"])

        version_queries = re.findall(r"\b(?:rev(?:ision)?|version)\s*([a-z0-9][a-z0-9._-]*)", normalized)
        product_query = self._product_phrase(normalized)
        intent = "INVESTIGATE_COMPLAINT_SIGNAL" if "complaint" in normalized or "shutdown" in normalized else next((name for name, pattern in _INTENT_PATTERNS if pattern.search(normalized)), "RETRIEVE_INVESTIGATION_CONTEXT")
        temporal_mode, start, end, knowledge, temporal_error = self._temporal(normalized)
        ambiguities = []
        if intent == "COMPARE_PRODUCT_VERSIONS" and len(version_queries) < 2:
            ambiguities.append("A comparison requires two ProductVersion references")
        if product_query in {"pump", "model x"}:
            ambiguities.append("The product reference may match more than one authorized product")
        if temporal_error:
            return InvestigationSpecification(status=InterpretationStatus.INVALID, normalized_question=normalized, intent=intent, product_query=product_query, version_queries=version_queries, temporal_mode=temporal_mode, limitations=[temporal_error])
        return InvestigationSpecification(
            status=InterpretationStatus.REQUIRES_CLARIFICATION if ambiguities else InterpretationStatus.READY,
            normalized_question=normalized, intent=intent, product_query=product_query,
            version_queries=version_queries, temporal_mode=temporal_mode,
            event_start=start, event_end=end, knowledge_time=knowledge,
            requested_entities=self._entities(normalized),
            requested_metrics=["complaint_count"] if "complaint" in normalized else [],
            ambiguities=ambiguities,
            limitations=["Interpretation does not establish causality or authorization"],
            retrieval_scope={"tenant_scoped": True, "authorized_only": True, "ai_safe_fields_only": True},
        )

    @staticmethod
    def _product_phrase(question: str) -> str | None:
        match = re.search(r"(?:for|about|after)\s+([a-z0-9][a-z0-9 -]{1,60}?)(?:\s+rev(?:ision)?\s*[a-z0-9]|\s+between\b|\s+as of\b|$)", question)
        return match.group(1).strip() if match else None

    @staticmethod
    def _entities(question: str) -> list[str]:
        return [entity for token, entity in (("complaint", "Complaint"), ("evidence", "Evidence"), ("unknown", "Unknown"), ("change", "Change")) if token in question]

    def _temporal(self, question: str):
        by_date = re.search(r"\bby\s+(\d{4}-\d{2}-\d{2})", question)
        if by_date:
            parsed = self._parse_date(by_date.group(1))
            if not parsed:
                return TemporalMode.EVENT_AS_OF, None, None, None, "A valid event date is required"
            return TemporalMode.EVENT_AS_OF, None, parsed, None, None
        if "did we know" in question or "known" in question or "available" in question:
            parsed = self._date_after(question, "as of") or self._date_after(question, "on")
            return TemporalMode.KNOWN_AS_OF, None, None, parsed, None if parsed else "A valid knowledge date is required"
        if "event" in question and ("as of" in question or "on" in question):
            parsed = self._date_after(question, "as of") or self._date_after(question, "on")
            return TemporalMode.EVENT_AS_OF, None, parsed, None, None if parsed else "A valid event date is required"
        match = re.search(r"between\s+(\d{4}-\d{2}-\d{2})\s+and\s+(\d{4}-\d{2}-\d{2})", question)
        if match:
            start, end = self._parse_date(match.group(1)), self._parse_date(match.group(2))
            if not start or not end:
                return TemporalMode.EVENT_AS_OF, None, None, None, "A valid temporal date range is required"
            if end < start:
                return TemporalMode.EVENT_AS_OF, start, end, None, "Temporal range end precedes start"
            return TemporalMode.EVENT_AS_OF, start, end, None, None
        relative = re.search(r"last\s+(\d+)\s+days?", question)
        if relative:
            return TemporalMode.EVENT_AS_OF, self.server_today - timedelta(days=int(relative.group(1))), self.server_today, None, None
        if re.search(r"\b(then|that time|when the investigation was opened|when this started)\b", question):
            return TemporalMode.CURRENT, None, None, None, "A resolvable historical time reference is required"
        return TemporalMode.CURRENT, None, None, None, None

    def _date_after(self, question: str, marker: str):
        match = re.search(re.escape(marker) + r"\s+(\d{4}-\d{2}-\d{2})", question)
        return self._parse_date(match.group(1)) if match else None

    @staticmethod
    def _parse_date(value: str) -> date | None:
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
