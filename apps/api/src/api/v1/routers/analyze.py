from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ....domain.value_objects import KeyType
from ...deps import AuthContext, get_container, guard_text_size, require_key
from ..schemas import AnalyzeOptions, AnalyzeRequest, AnalyzeResponse, Usage

router = APIRouter(tags=["data-plane"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    payload: AnalyzeRequest,
    request: Request,
    auth: AuthContext = Depends(require_key(KeyType.ANALYZE)),
) -> AnalyzeResponse:
    container = get_container(request)
    guard_text_size(payload.text, container.settings)

    options = payload.options or AnalyzeOptions()
    outcome = await container.analyze_uc.execute(
        payload.text,
        auth.runtime,
        provider_id=options.providerId,
        model=options.model,
        deanonymize_response=options.deanonymize,
    )

    return AnalyzeResponse(
        analysis=outcome.analysis,
        requestId=request.state.request_id,
        usage=Usage(
            inputTokens=outcome.usage.input_tokens,
            outputTokens=outcome.usage.output_tokens,
        ),
    )
