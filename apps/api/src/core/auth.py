"""Supabase JWT verification for the control plane.

MVP verifies HS256 tokens signed with the project's JWT secret
(``SECUREAI_SUPABASE_JWT_SECRET``). Production can extend this to RS256 via
JWKS without changing callers.
"""

from __future__ import annotations

from dataclasses import dataclass

import jwt

from .config import Settings
from .errors import Unauthenticated


@dataclass(frozen=True)
class AuthUser:
    id: str
    email: str | None = None


class JwtVerifier:
    def __init__(self, settings: Settings) -> None:
        self._secret = settings.supabase_jwt_secret
        self._audience = settings.supabase_jwt_audience

    @property
    def configured(self) -> bool:
        return bool(self._secret)

    def verify(self, token: str) -> AuthUser:
        if not self._secret:
            raise Unauthenticated("Control plane auth is not configured")
        try:
            claims = jwt.decode(
                token,
                self._secret,
                algorithms=["HS256"],
                audience=self._audience,
                options={"verify_aud": True},
            )
        except jwt.PyJWTError as exc:
            raise Unauthenticated("Invalid or expired token") from exc
        sub = claims.get("sub")
        if not sub:
            raise Unauthenticated("Token is missing subject (sub)")
        return AuthUser(id=str(sub), email=claims.get("email"))
