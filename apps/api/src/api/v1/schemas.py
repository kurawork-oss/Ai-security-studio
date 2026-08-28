"""Pydantic request/response DTOs for the v1 Data Plane API."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class EntitySpan(BaseModel):
    entityType: str
    start: int
    end: int
    score: float


# ── Protect ──
class ProtectOptions(BaseModel):
    returnEntities: bool = False
    # Per-request rule toggles (used by the Playground); does not persist.
    rules: dict[str, bool] | None = None


class ProtectRequest(BaseModel):
    # Provide either `text`, or a file via contentType + contentBase64
    # (extracted to text by a plugin, then protected).
    text: str | None = None
    contentType: str | None = None
    contentBase64: str | None = None
    options: ProtectOptions | None = None

    @model_validator(mode="after")
    def _require_source(self) -> "ProtectRequest":
        if not self.text and not self.contentBase64:
            raise ValueError("Provide either 'text' or 'contentBase64'")
        return self


class ProtectResponse(BaseModel):
    maskedText: str
    requestId: str
    entities: list[EntitySpan] | None = None


# ── Detect ──
class DetectRequest(BaseModel):
    text: str = Field(..., min_length=1)
    options: ProtectOptions | None = None


class DetectResponse(BaseModel):
    entities: list[EntitySpan]
    entityCounts: dict[str, int]
    requestId: str


# ── Analyze ──
class AnalyzeOptions(BaseModel):
    providerId: str | None = None
    model: str | None = None
    deanonymize: bool = False


class AnalyzeRequest(BaseModel):
    text: str | None = None
    contentType: str | None = None
    contentBase64: str | None = None
    options: AnalyzeOptions | None = None

    @model_validator(mode="after")
    def _require_source(self) -> "AnalyzeRequest":
        if not self.text and not self.contentBase64:
            raise ValueError("Provide either 'text' or 'contentBase64'")
        return self


class Usage(BaseModel):
    inputTokens: int
    outputTokens: int


class AnalyzeResponse(BaseModel):
    analysis: str
    requestId: str
    usage: Usage


# ── Extract (extractor plugins; returns MASKED text — never raw PII) ──
class ExtractRequest(BaseModel):
    contentType: str
    contentBase64: str = Field(..., min_length=1)
    options: ProtectOptions | None = None


class ExtractResponse(BaseModel):
    maskedText: str
    requestId: str
    entities: list[EntitySpan] | None = None


# ── Batch analyze ──
class BatchAnalyzeRequest(BaseModel):
    texts: list[str] = Field(..., min_length=1, max_length=100)
    options: AnalyzeOptions | None = None


class BatchAnalyzeItem(BaseModel):
    analysis: str
    usage: Usage


class BatchAnalyzeResponse(BaseModel):
    results: list[BatchAnalyzeItem]
    requestId: str


# ── Plugins ──
class PluginOut(BaseModel):
    key: str
    category: str
    version: str
    description: str
    contentTypes: list[str]
    available: bool
