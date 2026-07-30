"""SecureAI Studio Python SDK — a thin, typed wrapper over the REST API.

    from secureai import SecureAI
    client = SecureAI(api_key=os.environ["SECUREAI_PROTECT_KEY"])
    masked = client.protect("田中太郎 090-1234-5678").masked_text
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx

from .errors import SecureAIError

DEFAULT_BASE_URL = "https://api.secureai.studio"


@dataclass
class Entity:
    entity_type: str
    start: int
    end: int
    score: float


@dataclass
class ProtectResult:
    masked_text: str
    request_id: str
    entities: list[Entity] = field(default_factory=list)


@dataclass
class DetectResult:
    entities: list[Entity]
    entity_counts: dict[str, int]
    request_id: str


@dataclass
class AnalyzeResult:
    analysis: str
    request_id: str
    input_tokens: int = 0
    output_tokens: int = 0


def _entities(raw: Any) -> list[Entity]:
    return [
        Entity(e["entityType"], e["start"], e["end"], e["score"]) for e in (raw or [])
    ]


class SecureAI:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            headers={"Authorization": f"Bearer {api_key}"},
            transport=transport,
        )

    # ── context manager ──
    def __enter__(self) -> "SecureAI":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    # ── API ──
    def protect(
        self,
        text: str,
        *,
        return_entities: bool = False,
        rules: dict[str, bool] | None = None,
    ) -> ProtectResult:
        body = self._post(
            "/v1/protect",
            {"text": text, "options": {"returnEntities": return_entities, "rules": rules}},
        )
        return ProtectResult(
            masked_text=body["maskedText"],
            request_id=body.get("requestId", ""),
            entities=_entities(body.get("entities")),
        )

    def detect(self, text: str, *, rules: dict[str, bool] | None = None) -> DetectResult:
        body = self._post("/v1/detect", {"text": text, "options": {"rules": rules}})
        return DetectResult(
            entities=_entities(body.get("entities")),
            entity_counts=body.get("entityCounts", {}),
            request_id=body.get("requestId", ""),
        )

    def analyze(
        self,
        text: str,
        *,
        provider_id: str | None = None,
        model: str | None = None,
        deanonymize: bool = False,
    ) -> AnalyzeResult:
        body = self._post(
            "/v1/analyze",
            {
                "text": text,
                "options": {
                    "providerId": provider_id,
                    "model": model,
                    "deanonymize": deanonymize,
                },
            },
        )
        usage = body.get("usage", {})
        return AnalyzeResult(
            analysis=body["analysis"],
            request_id=body.get("requestId", ""),
            input_tokens=usage.get("inputTokens", 0),
            output_tokens=usage.get("outputTokens", 0),
        )

    # ── internals ──
    def _post(self, path: str, json: dict) -> dict:
        try:
            resp = self._client.post(path, json=json)
        except httpx.HTTPError as exc:  # network-level failure
            raise SecureAIError(str(exc), code="NETWORK_ERROR") from exc
        if resp.status_code >= 400:
            self._raise(resp)
        return resp.json()

    @staticmethod
    def _raise(resp: httpx.Response) -> None:
        try:
            err = resp.json().get("error", {})
        except Exception:
            err = {}
        raise SecureAIError(
            err.get("message", f"Request failed ({resp.status_code})"),
            code=err.get("code", "ERROR"),
            status=resp.status_code,
            request_id=err.get("requestId"),
        )
