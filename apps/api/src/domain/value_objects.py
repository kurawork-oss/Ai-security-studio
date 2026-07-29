"""Value objects — immutable domain types shared across layers.

Entity types are plain string codes (not a closed enum) so that custom /
enterprise PII types can be added via the database without code changes
(see design doc ⑤ Protect Rules).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class BuiltinEntity(StrEnum):
    """The 12 default PII types seeded into the catalog."""

    PERSON = "PERSON"
    PHONE_NUMBER = "PHONE_NUMBER"
    EMAIL_ADDRESS = "EMAIL_ADDRESS"
    LOCATION = "LOCATION"
    JP_POSTAL_CODE = "JP_POSTAL_CODE"
    URL = "URL"
    IP_ADDRESS = "IP_ADDRESS"
    JP_BANK_ACCOUNT = "JP_BANK_ACCOUNT"
    CREDIT_CARD = "CREDIT_CARD"
    JP_MYNUMBER = "JP_MYNUMBER"
    JP_PASSPORT = "JP_PASSPORT"
    JP_CORPORATE_NUMBER = "JP_CORPORATE_NUMBER"


class AnonymizeAction(StrEnum):
    MASK = "mask"        # replace with a typed placeholder: <PERSON_1>
    REDACT = "redact"    # replace with a fixed token: [REDACTED]
    HASH = "hash"        # replace with a short deterministic hash
    REPLACE = "replace"  # replace with a rule-provided constant


class KeyType(StrEnum):
    PROTECT = "protect"
    ANALYZE = "analyze"


@dataclass(frozen=True)
class PiiSpan:
    """A detected PII occurrence.

    ``text`` is the matched substring, kept only in memory during a single
    request for anonymization; it is never logged or persisted.
    """

    entity_type: str
    start: int
    end: int
    score: float
    text: str

    def public_dict(self) -> dict:
        """Metadata only — excludes the raw matched value."""
        return {
            "entityType": self.entity_type,
            "start": self.start,
            "end": self.end,
            "score": round(self.score, 3),
        }


@dataclass(frozen=True)
class ProtectionResult:
    """Outcome of detecting + anonymizing a piece of text."""

    masked_text: str
    entity_counts: dict[str, int]
    spans: list[PiiSpan] = field(default_factory=list)
    # placeholder -> original value. In-memory only, used for optional Analyze
    # de-anonymization. NEVER persisted or logged.
    mapping: dict[str, str] = field(default_factory=dict)

    @property
    def total_entities(self) -> int:
        return sum(self.entity_counts.values())


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass(frozen=True)
class LlmRequest:
    """Provider-agnostic request. ``prompt`` is ALWAYS already anonymized."""

    prompt: str
    model: str | None = None
    system: str | None = None
    max_tokens: int | None = None
    temperature: float | None = None


@dataclass(frozen=True)
class LlmResponse:
    text: str
    model: str
    usage: TokenUsage = TokenUsage()


@dataclass(frozen=True)
class ProviderCapabilities:
    streaming: bool = False
    batch: bool = False
    vision: bool = False
    default_model: str | None = None
