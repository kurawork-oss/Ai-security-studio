from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ....application.management.service import ManagementService
from ....core.auth import AuthUser
from ....domain.entities import ProtectRule
from ....domain.value_objects import AnonymizeAction, KeyType
from ...deps import get_container, get_uow, require_user
from ..schemas_mgmt import (
    AnalyticsSummaryOut,
    ApiKeyCreate,
    ApiKeyIssued,
    ApiKeyOut,
    LogOut,
    ProjectCreate,
    ProjectOut,
    ProviderCreate,
    ProviderOut,
    RuleOut,
    RulesUpdate,
)

router = APIRouter(tags=["management"])


def get_service(request: Request, uow=Depends(get_uow)) -> ManagementService:
    return ManagementService(uow, get_container(request).cipher)


def _project_out(p) -> ProjectOut:
    return ProjectOut(
        id=p.id, name=p.name, slug=p.slug, environment=p.environment,
        status=p.status, createdAt=p.created_at,
    )


def _key_out(k) -> ApiKeyOut:
    return ApiKeyOut(
        id=k.id, name=k.name, keyType=k.key_type.value, keyPrefix=k.key_prefix,
        status=k.status, createdAt=k.created_at,
    )


# ── Projects ──
@router.get("/projects", response_model=list[ProjectOut])
async def list_projects(user: AuthUser = Depends(require_user), svc: ManagementService = Depends(get_service)):
    return [_project_out(p) for p in await svc.list_projects(user)]


@router.post("/projects", response_model=ProjectOut, status_code=201)
async def create_project(payload: ProjectCreate, user: AuthUser = Depends(require_user), svc: ManagementService = Depends(get_service)):
    return _project_out(await svc.create_project(user, payload.name))


@router.get("/projects/{project_id}", response_model=ProjectOut)
async def get_project(project_id: str, user: AuthUser = Depends(require_user), svc: ManagementService = Depends(get_service)):
    return _project_out(await svc.get_project(user, project_id))


# ── Providers ──
@router.get("/projects/{project_id}/providers", response_model=list[ProviderOut])
async def list_providers(project_id: str, user: AuthUser = Depends(require_user), svc: ManagementService = Depends(get_service)):
    return [
        ProviderOut(id=p.id, providerType=p.provider_type, displayName=p.display_name,
                    defaultModel=p.default_model, isActive=p.is_active)
        for p in await svc.list_providers(user, project_id)
    ]


@router.post("/projects/{project_id}/providers", response_model=ProviderOut, status_code=201)
async def create_provider(project_id: str, payload: ProviderCreate, user: AuthUser = Depends(require_user), svc: ManagementService = Depends(get_service)):
    p = await svc.create_provider(
        user, project_id,
        provider_type=payload.providerType, display_name=payload.displayName,
        default_model=payload.defaultModel, base_url=payload.baseUrl, api_key=payload.apiKey,
    )
    return ProviderOut(id=p.id, providerType=p.provider_type, displayName=p.display_name,
                       defaultModel=p.default_model, isActive=p.is_active)


# ── API keys ──
@router.get("/projects/{project_id}/api-keys", response_model=list[ApiKeyOut])
async def list_api_keys(project_id: str, user: AuthUser = Depends(require_user), svc: ManagementService = Depends(get_service)):
    return [_key_out(k) for k in await svc.list_api_keys(user, project_id)]


@router.post("/projects/{project_id}/api-keys", response_model=ApiKeyIssued, status_code=201)
async def issue_api_key(project_id: str, payload: ApiKeyCreate, user: AuthUser = Depends(require_user), svc: ManagementService = Depends(get_service)):
    key, raw = await svc.issue_api_key(user, project_id, KeyType(payload.keyType), payload.name)
    return ApiKeyIssued(**_key_out(key).model_dump(), apiKey=raw)


@router.post("/api-keys/{key_id}/rotate", response_model=ApiKeyIssued)
async def rotate_api_key(key_id: str, user: AuthUser = Depends(require_user), svc: ManagementService = Depends(get_service)):
    key, raw = await svc.rotate_api_key(user, key_id)
    return ApiKeyIssued(**_key_out(key).model_dump(), apiKey=raw)


@router.post("/api-keys/{key_id}/revoke", status_code=204)
async def revoke_api_key(key_id: str, user: AuthUser = Depends(require_user), svc: ManagementService = Depends(get_service)):
    await svc.revoke_api_key(user, key_id)


# ── Protect rules ──
@router.get("/projects/{project_id}/protect-rules", response_model=list[RuleOut])
async def list_rules(project_id: str, user: AuthUser = Depends(require_user), svc: ManagementService = Depends(get_service)):
    return [
        RuleOut(entityType=r.entity_type, enabled=r.enabled, action=r.action.value, priority=r.priority)
        for r in await svc.list_rules(user, project_id)
    ]


@router.put("/projects/{project_id}/protect-rules", response_model=list[RuleOut])
async def update_rules(project_id: str, payload: RulesUpdate, user: AuthUser = Depends(require_user), svc: ManagementService = Depends(get_service)):
    rules = [
        ProtectRule(entity_type=i.entityType, enabled=i.enabled,
                    action=AnonymizeAction(i.action), priority=i.priority)
        for i in payload.rules
    ]
    updated = await svc.update_rules(user, project_id, rules)
    return [
        RuleOut(entityType=r.entity_type, enabled=r.enabled, action=r.action.value, priority=r.priority)
        for r in updated
    ]


# ── Logs & analytics ──
@router.get("/projects/{project_id}/logs", response_model=list[LogOut])
async def list_logs(project_id: str, limit: int = 50, user: AuthUser = Depends(require_user), svc: ManagementService = Depends(get_service)):
    return [
        LogOut(id=e.id, endpoint=e.endpoint, statusCode=e.status_code, latencyMs=e.latency_ms,
               inputChars=e.input_chars, entityCounts=e.entity_counts, createdAt=e.created_at)
        for e in await svc.list_logs(user, project_id, limit)
    ]


@router.get("/projects/{project_id}/analytics/summary", response_model=AnalyticsSummaryOut)
async def analytics_summary(project_id: str, user: AuthUser = Depends(require_user), svc: ManagementService = Depends(get_service)):
    return AnalyticsSummaryOut(**await svc.analytics_summary(user, project_id))
