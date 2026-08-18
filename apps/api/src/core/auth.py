"""Supabase JWT verification for the control plane.

Supports both Supabase JWT modes:
- **RS256 / ES256 (production)** — asymmetric keys served via JWKS. The signing
  key is resolved from the token's ``kid`` against the project's JWKS endpoint.
- **HS256 (legacy / dev)** — symmetric, verified with the project JWT secret.

The algorithm is chosen from the token header, so both work without config
changes on the client side.
"""

from __future__ import annotations

from dataclasses import dataclass

import jwt

from .config import Settings
from .errors import Unauthenticated

_ASYMMETRIC_PREFIXES = ("RS", "ES", "PS")


@dataclass(frozen=True)
class AuthUser:
    id: str
    email: str | None = None


class JwtVerifier:
    def __init__(self, settings: Settings, *, jwk_client: object | None = None) -> None:
        self._secret = settings.supabase_jwt_secret
        self._audience = settings.supabase_jwt_audience
        self._jwks_url = settings.jwks_url
        # Injectable for tests; otherwise a PyJWKClient is created lazily.
        self._jwk_client = jwk_client

    @property
    def configured(self) -> bool:
        return bool(self._secret or self._jwks_url or self._jwk_client)

    def verify(self, token: str) -> AuthUser:
        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError as exc:
            raise Unauthenticated("Malformed token") from exc

        alg = header.get("alg", "")
        try:
            if alg.startswith(_ASYMMETRIC_PREFIXES):
                key = self._signing_key(token)
                claims = jwt.decode(token, key, algorithms=[alg], audience=self._audience)
            elif alg == "HS256":
                if not self._secret:
                    raise Unauthenticated("HS256 token but no JWT secret configured")
                claims = jwt.decode(
                    token, self._secret, algorithms=["HS256"], audience=self._audience
                )
            else:
                raise Unauthenticated(f"Unsupported token algorithm '{alg}'")
        except jwt.PyJWTError as exc:
            raise Unauthenticated("Invalid or expired token") from exc

        sub = claims.get("sub")
        if not sub:
            raise Unauthenticated("Token is missing subject (sub)")
        return AuthUser(id=str(sub), email=claims.get("email"))

    def _signing_key(self, token: str):
        client = self._jwk_client
        if client is None:
            if not self._jwks_url:
                raise Unauthenticated("Asymmetric token but no JWKS endpoint configured")
            client = self._jwk_client = jwt.PyJWKClient(self._jwks_url)
        return client.get_signing_key_from_jwt(token).key
