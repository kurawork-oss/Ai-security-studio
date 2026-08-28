"""Detect use case — return detected PII spans (metadata) without masking.

Used by the Playground to highlight matches. Response never includes raw values.
"""

from __future__ import annotations

from collections.abc import Sequence

from ..domain.entities import ProtectRule
from ..domain.ports import PiiDetector
from ..domain.value_objects import PiiSpan


class DetectUseCase:
    def __init__(self, detector: PiiDetector) -> None:
        self._detector = detector

    def execute(self, text: str, rules: Sequence[ProtectRule]) -> list[PiiSpan]:
        return self._detector.detect(text, rules)
