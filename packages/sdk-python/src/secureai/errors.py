from __future__ import annotations


class SecureAIError(Exception):
    """Raised for any non-2xx response from the SecureAI API."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "ERROR",
        status: int | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status
        self.request_id = request_id

    def __repr__(self) -> str:  # pragma: no cover - repr convenience
        return f"SecureAIError(code={self.code!r}, status={self.status}, message={self.message!r})"
