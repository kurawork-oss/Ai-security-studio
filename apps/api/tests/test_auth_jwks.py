"""JWT verification: RS256 via JWKS (production Supabase) + HS256 (legacy)."""

from __future__ import annotations

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from src.core.auth import JwtVerifier
from src.core.config import Settings
from src.core.errors import Unauthenticated

AUD = "authenticated"


def _rsa():
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return priv, priv.public_key()


class _StubKey:
    def __init__(self, key):
        self.key = key


class _StubJwkClient:
    """Stands in for PyJWKClient: returns a fixed public key for any token."""

    def __init__(self, public_key):
        self._key = public_key

    def get_signing_key_from_jwt(self, _token):
        return _StubKey(self._key)


def _verifier(*, jwk_client=None, secret=None):
    return JwtVerifier(
        Settings(supabase_jwt_audience=AUD, supabase_jwt_secret=secret),
        jwk_client=jwk_client,
    )


def test_rs256_via_jwks():
    priv, pub = _rsa()
    token = jwt.encode(
        {"sub": "user-rs", "email": "rs@example.com", "aud": AUD},
        priv,
        algorithm="RS256",
        headers={"kid": "k1"},
    )
    user = _verifier(jwk_client=_StubJwkClient(pub)).verify(token)
    assert user.id == "user-rs"
    assert user.email == "rs@example.com"


def test_rs256_bad_signature_rejected():
    priv, _pub = _rsa()
    _priv2, pub2 = _rsa()  # different keypair
    token = jwt.encode({"sub": "x", "aud": AUD}, priv, algorithm="RS256")
    with pytest.raises(Unauthenticated):
        _verifier(jwk_client=_StubJwkClient(pub2)).verify(token)


def test_rs256_wrong_audience_rejected():
    priv, pub = _rsa()
    token = jwt.encode({"sub": "x", "aud": "other"}, priv, algorithm="RS256")
    with pytest.raises(Unauthenticated):
        _verifier(jwk_client=_StubJwkClient(pub)).verify(token)


def test_hs256_still_supported():
    secret = "hs-secret-long-enough-000000000000"
    token = jwt.encode({"sub": "user-hs", "aud": AUD}, secret, algorithm="HS256")
    user = _verifier(secret=secret).verify(token)
    assert user.id == "user-hs"


def test_unsupported_algorithm_rejected():
    token = jwt.encode({"sub": "x", "aud": AUD}, "", algorithm="none")
    with pytest.raises(Unauthenticated):
        _verifier(secret="whatever").verify(token)


def test_missing_sub_rejected():
    secret = "hs-secret-long-enough-000000000000"
    token = jwt.encode({"aud": AUD}, secret, algorithm="HS256")
    with pytest.raises(Unauthenticated):
        _verifier(secret=secret).verify(token)
