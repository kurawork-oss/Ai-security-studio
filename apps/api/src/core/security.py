"""API key generation, hashing and verification.

SecureAI-issued keys are shown once at creation and only their SHA-256 hash is
stored. Keys are typed (protect / analyze) so a project can separate the two
concerns and rotate them independently.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

from ..domain.value_objects import KeyType

_PREFIX_LEN = 16


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def verify_api_key(raw_key: str, key_hash: str) -> bool:
    return hmac.compare_digest(hash_api_key(raw_key), key_hash)


def key_prefix(raw_key: str) -> str:
    return raw_key[:_PREFIX_LEN]


def generate_api_key(key_type: KeyType) -> tuple[str, str, str]:
    """Return ``(raw_key, prefix, key_hash)``. The raw key is shown only once."""
    raw = f"sk_{key_type.value}_{secrets.token_hex(20)}"
    return raw, key_prefix(raw), hash_api_key(raw)
