from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Request

from ....domain.value_objects import KeyType
from ...deps import AuthContext, get_container, get_uow, guard_text_size, require_key
from ..schemas import (
    AnalyzeOptions,
    BatchAnalyzeItem,
    BatchAnalyzeRequest,
    BatchAnalyzeResponse,
    Usage,
)

router = APIRouter(tags=["data-plane"])


@router.post("/batch/analyze", response_model=BatchAnalyzeResponse)
async def batch_analyze(
    payload: BatchAnalyzeRequest,
    request: Request,
    auth: AuthContext = Depends(require_key(KeyType.ANALYZE)),
    uow=Depends(get_uow),
) -> BatchAnalyzeResponse:
    container = get_container(request)
    for t in payload.texts:
        guard_text_size(t, container.settings)

    options = payload.options or AnalyzeOptions()
    selected = auth.runtime.provider(options.providerId)

    start = time.perf_counter()
    results: list[BatchAnalyzeItem] = []
    total_in = total_out = 0
    counts: dict[str, int] = {}
    for t in payload.texts:
        outcome = await container.analyze_uc.execute(
            t,
            auth.runtime,
            provider_id=options.providerId,
            model=options.model,
            deanonymize_response=options.deanonymize,
        )
        results.append(
            BatchAnalyzeItem(
                analysis=outcome.analysis,
                usage=Usage(
                    inputTokens=outcome.usage.input_tokens,
                    outputTokens=outcome.usage.output_tokens,
                ),
            )
        )
        total_in += outcome.usage.input_tokens
        total_out += outcome.usage.output_tokens
        for code, n in outcome.protection.entity_counts.items():
            counts[str(code)] = counts.get(str(code), 0) + n
    latency_ms = int((time.perf_counter() - start) * 1000)

    await uow.logs.write(
        project_id=auth.runtime.project.id,
        endpoint="analyze",
        request_id=request.state.request_id,
        status_code=200,
        latency_ms=latency_ms,
        input_chars=sum(len(t) for t in payload.texts),
        entity_counts=counts,
        api_key_id=auth.key.id,
        provider_id=selected.id if selected else None,
        token_usage={"inputTokens": total_in, "outputTokens": total_out},
    )
    await uow.commit()

    return BatchAnalyzeResponse(results=results, requestId=request.state.request_id)
