from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Request

from ....domain.value_objects import KeyType
from ...deps import (
    AuthContext,
    effective_rules,
    get_container,
    get_uow,
    guard_text_size,
    require_key,
)
from ..schemas import EntitySpan, ProtectRequest, ProtectResponse

router = APIRouter(tags=["data-plane"])


@router.post("/protect", response_model=ProtectResponse)
async def protect(
    payload: ProtectRequest,
    request: Request,
    auth: AuthContext = Depends(require_key(KeyType.PROTECT)),
    uow=Depends(get_uow),
) -> ProtectResponse:
    container = get_container(request)
    guard_text_size(payload.text, container.settings)

    options = payload.options
    rules = effective_rules(auth.runtime, options.rules if options else None)

    start = time.perf_counter()
    result = container.protect_uc.execute(payload.text, rules)
    latency_ms = int((time.perf_counter() - start) * 1000)

    await uow.logs.write(
        project_id=auth.runtime.project.id,
        endpoint="protect",
        request_id=request.state.request_id,
        status_code=200,
        latency_ms=latency_ms,
        input_chars=len(payload.text),
        entity_counts=dict(result.entity_counts),
        api_key_id=auth.key.id,
    )
    await uow.commit()

    entities = None
    if options and options.returnEntities:
        entities = [EntitySpan(**s.public_dict()) for s in result.spans]

    return ProtectResponse(
        maskedText=result.masked_text,
        requestId=request.state.request_id,
        entities=entities,
    )
