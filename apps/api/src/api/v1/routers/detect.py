from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ....domain.value_objects import KeyType
from ...deps import AuthContext, effective_rules, get_container, guard_text_size, require_key
from ..schemas import DetectRequest, DetectResponse, EntitySpan

router = APIRouter(tags=["data-plane"])


@router.post("/detect", response_model=DetectResponse)
async def detect(
    payload: DetectRequest,
    request: Request,
    auth: AuthContext = Depends(require_key(KeyType.PROTECT)),
) -> DetectResponse:
    container = get_container(request)
    guard_text_size(payload.text, container.settings)

    options = payload.options
    rules = effective_rules(auth.runtime, options.rules if options else None)
    spans = container.detect_uc.execute(payload.text, rules)

    counts: dict[str, int] = {}
    for span in spans:
        counts[span.entity_type] = counts.get(span.entity_type, 0) + 1

    return DetectResponse(
        entities=[EntitySpan(**s.public_dict()) for s in spans],
        entityCounts=counts,
        requestId=request.state.request_id,
    )
