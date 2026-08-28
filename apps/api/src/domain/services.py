"""Pure domain services — no framework, DB, or network dependencies.

The Anonymizer turns detected spans into masked text. It is deterministic
within a request: the same original value gets the same placeholder, which also
enables optional de-anonymization of Analyze responses.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence

from .entities import ProtectRule
from .value_objects import AnonymizeAction, PiiSpan, ProtectionResult


def resolve_overlaps(
    spans: Sequence[PiiSpan], rules_by_type: dict[str, ProtectRule]
) -> list[PiiSpan]:
    """Keep a non-overlapping set of spans.

    On overlap, prefer the rule with the lower ``priority`` value, then the
    higher detection score, then the longer span.
    """

    def rank(s: PiiSpan) -> tuple[int, float, int]:
        rule = rules_by_type.get(s.entity_type)
        priority = rule.priority if rule else 100
        return (priority, -s.score, -(s.end - s.start))

    chosen: list[PiiSpan] = []
    for span in sorted(spans, key=rank):
        if any(not (span.end <= c.start or span.start >= c.end) for c in chosen):
            continue  # overlaps an already-chosen span
        chosen.append(span)
    return sorted(chosen, key=lambda s: s.start)


class Anonymizer:
    def anonymize(
        self, text: str, spans: Sequence[PiiSpan], rules: Sequence[ProtectRule]
    ) -> ProtectionResult:
        rules_by_type = {r.entity_type: r for r in rules}
        resolved = resolve_overlaps(spans, rules_by_type)

        counts: dict[str, int] = {}
        counters: dict[str, int] = {}
        value_to_token: dict[tuple[str, str], str] = {}
        mapping: dict[str, str] = {}

        # Replace from right to left so earlier indices stay valid.
        out = text
        for span in sorted(resolved, key=lambda s: s.start, reverse=True):
            rule = rules_by_type.get(span.entity_type) or ProtectRule.default_for(
                span.entity_type
            )
            key = (span.entity_type, span.text)
            token = value_to_token.get(key)
            if token is None:
                counters[span.entity_type] = counters.get(span.entity_type, 0) + 1
                token = self._token(rule, span, counters[span.entity_type])
                value_to_token[key] = token
                mapping[token] = span.text
                counts[span.entity_type] = counts.get(span.entity_type, 0) + 1
            out = out[: span.start] + token + out[span.end :]

        return ProtectionResult(
            masked_text=out,
            entity_counts=counts,
            spans=resolved,
            mapping=mapping,
        )

    @staticmethod
    def _token(rule: ProtectRule, span: PiiSpan, n: int) -> str:
        if rule.action is AnonymizeAction.REDACT:
            return "[REDACTED]"
        if rule.action is AnonymizeAction.REPLACE:
            return rule.replacement or f"<{span.entity_type}>"
        if rule.action is AnonymizeAction.HASH:
            digest = hashlib.sha256(span.text.encode("utf-8")).hexdigest()[:8]
            return f"<{span.entity_type}_{digest}>"
        # default: MASK with a typed, numbered placeholder
        return rule.placeholder_format.format(type=span.entity_type, n=n)


def deanonymize(text: str, mapping: dict[str, str]) -> str:
    """Restore original values in an LLM response (optional, in-memory only)."""
    out = text
    # Longest tokens first to avoid partial replacements.
    for token in sorted(mapping, key=len, reverse=True):
        out = out.replace(token, mapping[token])
    return out
