from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from ....domain.value_objects import KeyType
from ...deps import (
    AuthContext,
    get_container,
    guard_text_size,
    require_key,
    resolve_input_text,
)
from ..schemas import AnalyzeOptions, AnalyzeRequest

router = APIRouter(tags=["data-plane"])


@router.post("/analyze/stream")
async def analyze_stream(
    payload: AnalyzeRequest,
    request: Request,
    auth: AuthContext = Depends(require_key(KeyType.ANALYZE)),
):
    container = get_container(request)
    text = resolve_input_text(
        container,
        text=payload.text,
        content_type=payload.contentType,
        content_base64=payload.contentBase64,
    )
    guard_text_size(text, container.settings)

    options = payload.options or AnalyzeOptions()
    # Anonymization happens eagerly inside stream() — a failure raises here
    # (before any bytes are sent), preserving fail-closed semantics.
    generator = await container.analyze_uc.stream(
        text, auth.runtime, provider_id=options.providerId, model=options.model
    )
    return StreamingResponse(
        generator,
        media_type="text/plain; charset=utf-8",
        headers={"X-Request-Id": request.state.request_id},
    )
