"""Regex + validator based PII detector (the MVP default engine).

Implements the ``PiiDetector`` port. Only entity types with an *enabled* rule
are detected, and custom rules may contribute their own regex — so rules are
fully data-driven and extensible without code changes.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from ...domain.entities import ProtectRule
from ...domain.value_objects import PiiSpan
from .recognizers import Recognizer, builtin_recognizers


class RegexPiiDetector:
    name = "regex"

    def __init__(self, gazetteer: list[str] | None = None) -> None:
        self._builtins = builtin_recognizers(gazetteer)

    def detect(self, text: str, rules: Sequence[ProtectRule]) -> list[PiiSpan]:
        rules_by_type = {r.entity_type: r for r in rules if r.enabled}
        if not rules_by_type:
            return []

        recognizers = [r for r in self._builtins if r.entity_type in rules_by_type]
        recognizers.extend(self._custom_recognizers(rules_by_type))

        spans: list[PiiSpan] = []
        seen: set[tuple[str, int, int]] = set()
        for rec in recognizers:
            rule = rules_by_type[rec.entity_type]
            for m in rec.regex.finditer(text):
                try:
                    value = m.group(rec.group)
                    start, end = m.span(rec.group)
                except IndexError:
                    continue
                if not value:
                    continue
                if rec.validator and not rec.validator(value):
                    continue
                if rec.score < rule.score_threshold:
                    continue
                dedup = (rec.entity_type, start, end)
                if dedup in seen:
                    continue
                seen.add(dedup)
                spans.append(
                    PiiSpan(
                        entity_type=rec.entity_type,
                        start=start,
                        end=end,
                        score=rec.score,
                        text=value,
                    )
                )
        return spans

    @staticmethod
    def _custom_recognizers(rules_by_type: dict[str, ProtectRule]) -> list[Recognizer]:
        out: list[Recognizer] = []
        for entity_type, rule in rules_by_type.items():
            if not rule.regex:
                continue
            try:
                pattern = re.compile(rule.regex)
            except re.error:
                continue  # invalid custom regex is ignored, never crashes detection
            out.append(Recognizer(entity_type, pattern, score=0.9))
        return out
