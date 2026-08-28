"""Unit of Work — groups request-scoped repositories.

- ``PgUnitOfWork`` binds all repositories to one AsyncSession/transaction.
- ``InMemoryUnitOfWork`` backs the no-database dev mode: the data plane works
  against the seeded repos, while management repos raise ``DbRequired``.
"""

from __future__ import annotations

from ...core.errors import DbRequired
from ...domain.entities import LogEntry
from .repositories import (
    PgApiKeyAdminRepository,
    PgApiKeyRepository,
    PgLogRepository,
    PgMembershipRepository,
    PgProjectRepository,
    PgProjectRuntimeRepository,
    PgProtectRuleRepository,
    PgProviderRepository,
)


class PgUnitOfWork:
    def __init__(self, session) -> None:
        self.session = session
        self.api_keys = PgApiKeyRepository(session)
        self.runtime = PgProjectRuntimeRepository(session)
        self.memberships = PgMembershipRepository(session)
        self.projects = PgProjectRepository(session)
        self.providers = PgProviderRepository(session)
        self.api_key_admin = PgApiKeyAdminRepository(session)
        self.rules = PgProtectRuleRepository(session)
        self.logs = PgLogRepository(session)

    async def commit(self) -> None:
        await self.session.commit()


class _NoOpLogRepository:
    async def write(self, **_kwargs) -> None:
        return None

    async def list_by_project(self, project_id: str, limit: int = 50) -> list[LogEntry]:
        return []


class _RequiresDb:
    def __getattr__(self, _name: str):
        async def _raise(*_args, **_kwargs):
            raise DbRequired("This endpoint requires a database (set SECUREAI_DATABASE_URL).")

        return _raise


class InMemoryUnitOfWork:
    def __init__(self, api_key_repo, runtime_repo) -> None:
        self.api_keys = api_key_repo
        self.runtime = runtime_repo
        self.logs = _NoOpLogRepository()
        self.memberships = _RequiresDb()
        self.projects = _RequiresDb()
        self.providers = _RequiresDb()
        self.api_key_admin = _RequiresDb()
        self.rules = _RequiresDb()

    async def commit(self) -> None:
        return None
