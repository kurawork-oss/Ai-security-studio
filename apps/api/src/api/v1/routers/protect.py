from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ....domain.value_objects import KeyType
from ...deps import AuthContext, effective_rules, get_container, guard_text_size, require_key
from ..schemas import EntitySpan, ProtectRequest, ProtectResponse

router = APIRouter(tags=["data-plane"])


@router.post("/protect", response_model=ProtectResponse)
async def protect(
    payload: ProtectRequest,
    request: Request,
    auth: AuthContext = Depends(require_key(KeyType.PROTECT)),
) -> ProtectResponse:
    container = get_container(request)
    guard_text_size(payload.text, container.settings)

    options = payload.options
    rules = effective_rules(auth.runtime, options.rules if options else None)
    result = container.protect_uc.execute(payload.text, rules)

    entities = None
    if options and options.returnEntities:
        entities = [EntitySpan(**s.public_dict()) for s in result.spans]

    return ProtectResponse(
        maskedText=result.masked_text,
        requestId=request.state.request_id,
        entities=entities,
    )
