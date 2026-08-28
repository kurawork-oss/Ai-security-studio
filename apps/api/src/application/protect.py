"""Protect use case — detect + anonymize PII in text."""

from __future__ import annotations

from collections.abc import Sequence

from ..core.errors import AnonymizationFailed
from ..domain.entities import ProtectRule
from ..domain.ports import PiiDetector
from ..domain.services import Anonymizer
from ..domain.value_objects import ProtectionResult


class ProtectTextUseCase:
    def __init__(self, detector: PiiDetector, anonymizer: Anonymizer) -> None:
        self._detector = detector
        self._anonymizer = anonymizer

    def execute(self, text: str, rules: Sequence[ProtectRule]) -> ProtectionResult:
        try:
            spans = self._detector.detect(text, rules)
            return self._anonymizer.anonymize(text, spans, rules)
        except Exception as exc:  # fail-closed: never leak partially-processed text
            raise AnonymizationFailed("PII anonymization failed") from exc
