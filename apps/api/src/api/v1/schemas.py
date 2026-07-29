"""Pydantic request/response DTOs for the v1 Data Plane API."""

from __future__ import annotations

from pydantic import BaseModel, Field


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
    text: str = Field(..., min_length=1)
    options: ProtectOptions | None = None


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
    text: str = Field(..., min_length=1)
    options: AnalyzeOptions | None = None


class Usage(BaseModel):
    inputTokens: int
    outputTokens: int


class AnalyzeResponse(BaseModel):
    analysis: str
    requestId: str
    usage: Usage
