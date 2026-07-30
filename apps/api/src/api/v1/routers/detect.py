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
from ..schemas import DetectRequest, DetectResponse, EntitySpan

router = APIRouter(tags=["data-plane"])


@router.post("/detect", response_model=DetectResponse)
async def detect(
    payload: DetectRequest,
    request: Request,
    auth: AuthContext = Depends(require_key(KeyType.PROTECT)),
    uow=Depends(get_uow),
) -> DetectResponse:
    container = get_container(request)
    guard_text_size(payload.text, container.settings)

    options = payload.options
    rules = effective_rules(auth.runtime, options.rules if options else None)

    start = time.perf_counter()
    spans = container.detect_uc.execute(payload.text, rules)
    latency_ms = int((time.perf_counter() - start) * 1000)

    counts: dict[str, int] = {}
    for span in spans:
        counts[span.entity_type] = counts.get(span.entity_type, 0) + 1

    await uow.logs.write(
        project_id=auth.runtime.project.id,
        endpoint="detect",
        request_id=request.state.request_id,
        status_code=200,
        latency_ms=latency_ms,
        input_chars=len(payload.text),
        entity_counts=counts,
        api_key_id=auth.key.id,
    )
    await uow.commit()

    return DetectResponse(
        entities=[EntitySpan(**s.public_dict()) for s in spans],
        entityCounts=counts,
        requestId=request.state.request_id,
    )
