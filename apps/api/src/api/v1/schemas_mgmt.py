"""Pydantic DTOs for the Control Plane (management) API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


# ── Projects ──
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)


class ProjectOut(BaseModel):
    id: str
    name: str
    slug: str
    environment: str
    status: str
    createdAt: datetime | None = None


# ── Providers ──
class ProviderCreate(BaseModel):
    providerType: str
    displayName: str = ""
    defaultModel: str | None = None
    baseUrl: str | None = None
    apiKey: str | None = None  # provider credential; encrypted at rest, never returned


class ProviderOut(BaseModel):
    id: str
    providerType: str
    displayName: str
    defaultModel: str | None = None
    isActive: bool


# ── API keys ──
class ApiKeyCreate(BaseModel):
    keyType: str = Field(..., pattern="^(protect|analyze)$")
    name: str = ""


class ApiKeyOut(BaseModel):
    id: str
    name: str
    keyType: str
    keyPrefix: str
    status: str
    createdAt: datetime | None = None


class ApiKeyIssued(ApiKeyOut):
    apiKey: str  # raw key — shown only once at creation/rotation


# ── Protect rules ──
class RuleItem(BaseModel):
    entityType: str
    enabled: bool = True
    action: str = "mask"
    priority: int = 100


class RulesUpdate(BaseModel):
    rules: list[RuleItem]


class RuleOut(BaseModel):
    entityType: str
    enabled: bool
    action: str
    priority: int


# ── Logs & analytics ──
class LogOut(BaseModel):
    id: str
    endpoint: str
    statusCode: int | None = None
    latencyMs: int | None = None
    inputChars: int | None = None
    entityCounts: dict[str, int]
    createdAt: datetime | None = None


class AnalyticsSummaryOut(BaseModel):
    requests: int
    byEndpoint: dict[str, int]
    protectCount: int
    entityCounts: dict[str, int]
    avgLatencyMs: int


# ── Export ──
class ExportTargetOut(BaseModel):
    id: str
    label: str


class ExportRequest(BaseModel):
    targetId: str
    language: str = "typescript"
    pattern: str = Field("protect", pattern="^(protect|analyze)$")
    apiBaseUrl: str = "https://api.secureai.studio"


class ExportArtifactOut(BaseModel):
    targetId: str
    title: str
    content: str
    format: str
