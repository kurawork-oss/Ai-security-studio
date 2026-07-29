"""Envelope-style encryption for provider secrets (AES-256-GCM).

The data-encryption key is derived from a KEK obtained via a ``KeyProvider``.
For development the KEK comes from an environment variable; production swaps in
a KMS-backed provider (AWS KMS / GCP KMS / Vault) without changing callers.
"""

from __future__ import annotations

import hashlib
import os
from typing import Protocol

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_NONCE_BYTES = 12


class KeyProvider(Protocol):
    def data_key(self) -> bytes:
        """Return a 32-byte AES-256 key."""
        ...


class EnvKeyProvider:
    """Derives a 32-byte key from the configured KEK (development / self-host)."""

    def __init__(self, kek: str) -> None:
        if not kek or len(kek) < 16:
            raise ValueError("ENCRYPTION_KEK must be set and at least 16 chars")
        self._key = hashlib.sha256(kek.encode("utf-8")).digest()

    def data_key(self) -> bytes:
        return self._key


class AesGcmCipher:
    def __init__(self, provider: KeyProvider) -> None:
        self._provider = provider

    def encrypt(self, plaintext: str) -> bytes:
        aes = AESGCM(self._provider.data_key())
        nonce = os.urandom(_NONCE_BYTES)
        return nonce + aes.encrypt(nonce, plaintext.encode("utf-8"), None)

    def decrypt(self, blob: bytes) -> str:
        aes = AESGCM(self._provider.data_key())
        nonce, ct = blob[:_NONCE_BYTES], blob[_NONCE_BYTES:]
        return aes.decrypt(nonce, ct, None).decode("utf-8")


def build_cipher(kms_provider: str, kek: str) -> AesGcmCipher:
    # Only the env provider is wired for the MVP; the abstraction leaves room
    # for aws / gcp / vault implementations.
    provider: KeyProvider = EnvKeyProvider(kek)
    return AesGcmCipher(provider)
