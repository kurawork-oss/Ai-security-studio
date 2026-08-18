"""Application configuration.

All settings come from environment variables (prefix ``SECUREAI_``) and are
validated at startup. Nothing is hardcoded; missing/invalid values fail fast.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SECUREAI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── App ──
    environment: str = "development"
    log_level: str = "info"
    api_text_max_bytes: int = 102_400

    # ── CORS ──
    cors_origins: str = "http://localhost:3000"

    # ── Providers ──
    default_provider: str = "gemini"
    gemini_api_base: str = "https://generativelanguage.googleapis.com"
    gemini_default_model: str = "gemini-1.5-flash"
    # Claude / OpenAI. Default models are intentionally empty — set them via env
    # or per-provider (DB) so no model id is hardcoded here.
    claude_api_base: str = "https://api.anthropic.com"
    claude_api_version: str = "2023-06-01"
    claude_default_model: str = ""
    openai_api_base: str = "https://api.openai.com"
    openai_default_model: str = ""

    # ── Persistence ──
    # When set, Postgres (Supabase) is used; otherwise the in-memory dev seed.
    database_url: str | None = None

    # ── Auth (Supabase JWT for the control plane) ──
    supabase_jwt_secret: str | None = None       # HS256 secret (dev / legacy)
    supabase_jwt_audience: str = "authenticated"
    # Production Supabase uses asymmetric keys (RS256/ES256) served via JWKS.
    supabase_url: str | None = None              # to derive the JWKS URL
    supabase_jwt_jwks_url: str | None = None     # explicit override

    @property
    def jwks_url(self) -> str | None:
        if self.supabase_jwt_jwks_url:
            return self.supabase_jwt_jwks_url
        if self.supabase_url:
            return f"{self.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
        return None

    # ── Crypto / KMS ──
    kms_provider: str = "env"
    encryption_kek: str = "dev-only-change-me-0123456789abcdef0123456789abcdef"

    # ── Dev seed (never enable in production) ──
    dev_seed: bool = True
    dev_protect_key: str = "sk_protect_dev_0000000000000000"
    dev_analyze_key: str = "sk_analyze_dev_0000000000000000"
    dev_provider_type: str = "echo"
    dev_gemini_key: str = ""

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}

    @property
    def use_postgres(self) -> bool:
        return bool(self.database_url)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @field_validator("api_text_max_bytes")
    @classmethod
    def _positive_max_bytes(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("api_text_max_bytes must be positive")
        return v

    def enforce_production_safety(self) -> None:
        """Guard rails so dev conveniences never ship to production."""
        if self.is_production and self.dev_seed:
            raise ValueError("SECUREAI_DEV_SEED must be false in production")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.enforce_production_safety()
    return settings
