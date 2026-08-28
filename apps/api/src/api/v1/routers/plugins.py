from __future__ import annotations

from fastapi import APIRouter, Request

from ...deps import get_container
from ..schemas import PluginOut

router = APIRouter(tags=["meta"])


@router.get("/plugins", response_model=list[PluginOut])
async def list_plugins(request: Request) -> list[PluginOut]:
    container = get_container(request)
    return [PluginOut(**m.public_dict()) for m in container.plugins.manifests()]
