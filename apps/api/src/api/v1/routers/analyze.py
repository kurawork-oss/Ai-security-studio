from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Request

from ....domain.value_objects import KeyType
from ...deps import (
    AuthContext,
    get_container,
    get_uow,
    guard_text_size,
    require_key,
    resolve_input_text,
)
from ..schemas import AnalyzeOptions, AnalyzeRequest, AnalyzeResponse, Usage

router = APIRouter(tags=["data-plane"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    payload: AnalyzeRequest,
    request: Request,
    auth: AuthContext = Depends(require_key(KeyType.ANALYZE)),
    uow=Depends(get_uow),
) -> AnalyzeResponse:
    container = get_container(request)
    text = resolve_input_text(
        container,
        text=payload.text,
        content_type=payload.contentType,
        content_base64=payload.contentBase64,
    )
    guard_text_size(text, container.settings)

    options = payload.options or AnalyzeOptions()
    selected = auth.runtime.provider(options.providerId)

    start = time.perf_counter()
    outcome = await container.analyze_uc.execute(
        text,
        auth.runtime,
        provider_id=options.providerId,
        model=options.model,
        deanonymize_response=options.deanonymize,
    )
    latency_ms = int((time.perf_counter() - start) * 1000)

    await uow.logs.write(
        project_id=auth.runtime.project.id,
        endpoint="analyze",
        request_id=request.state.request_id,
        status_code=200,
        latency_ms=latency_ms,
        input_chars=len(text),
        entity_counts=dict(outcome.protection.entity_counts),
        api_key_id=auth.key.id,
        provider_id=selected.id if selected else None,
        token_usage={
            "inputTokens": outcome.usage.input_tokens,
            "outputTokens": outcome.usage.output_tokens,
        },
    )
    await uow.commit()

    return AnalyzeResponse(
        analysis=outcome.analysis,
        requestId=request.state.request_id,
        usage=Usage(
            inputTokens=outcome.usage.input_tokens,
            outputTokens=outcome.usage.output_tokens,
        ),
    )
