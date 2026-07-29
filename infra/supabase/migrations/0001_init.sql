-- SecureAI Studio — initial schema
-- Matches docs/architecture/03-database-design.md
-- PostgreSQL / Supabase. RLS is enabled on tenant tables.

create extension if not exists pgcrypto;

-- ─────────────────────────────────────────────────────────────
-- Identity / tenancy
-- ─────────────────────────────────────────────────────────────

-- Profile mirror of auth.users (Supabase Auth is the source of truth).
create table if not exists public.users (
    id           uuid primary key references auth.users (id) on delete cascade,
    email        text,
    display_name text,
    created_at   timestamptz not null default now()
);

create table if not exists public.organizations (
    id         uuid primary key default gen_random_uuid(),
    name       text not null,
    slug       text not null unique,
    owner_id   uuid references public.users (id) on delete set null,
    plan       text not null default 'free' check (plan in ('free', 'pro', 'enterprise')),
    created_at timestamptz not null default now()
);

create table if not exists public.memberships (
    id         uuid primary key default gen_random_uuid(),
    org_id     uuid not null references public.organizations (id) on delete cascade,
    user_id    uuid not null references public.users (id) on delete cascade,
    role       text not null default 'member'
                 check (role in ('owner', 'admin', 'member', 'viewer')),
    created_at timestamptz not null default now(),
    unique (org_id, user_id)
);
create index if not exists idx_memberships_user on public.memberships (user_id);

create table if not exists public.projects (
    id          uuid primary key default gen_random_uuid(),
    org_id      uuid not null references public.organizations (id) on delete cascade,
    name        text not null,
    slug        text not null,
    description text,
    environment text not null default 'dev' check (environment in ('dev', 'prod')),
    status      text not null default 'active' check (status in ('active', 'archived')),
    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now(),
    unique (org_id, slug)
);

-- ─────────────────────────────────────────────────────────────
-- Providers & credentials
-- ─────────────────────────────────────────────────────────────

create table if not exists public.providers (
    id            uuid primary key default gen_random_uuid(),
    project_id    uuid not null references public.projects (id) on delete cascade,
    provider_type text not null
                    check (provider_type in
                      ('gemini', 'claude', 'openai', 'deepseek', 'grok', 'local', 'echo')),
    display_name  text not null default '',
    default_model text,
    base_url      text,
    settings      jsonb not null default '{}',
    is_active     boolean not null default true,
    created_at    timestamptz not null default now(),
    updated_at    timestamptz not null default now()
);
create index if not exists idx_providers_project on public.providers (project_id);

-- Provider API keys are encrypted at rest (AES-256-GCM). Rotatable.
create table if not exists public.provider_keys (
    id            uuid primary key default gen_random_uuid(),
    provider_id   uuid not null references public.providers (id) on delete cascade,
    alias         text not null default 'default',
    encrypted_key bytea not null,
    key_hint      text,                    -- last 4 chars only (plaintext)
    status        text not null default 'active' check (status in ('active', 'revoked')),
    created_at    timestamptz not null default now(),
    rotated_at    timestamptz,
    expires_at    timestamptz
);
create index if not exists idx_provider_keys_provider on public.provider_keys (provider_id);

-- ─────────────────────────────────────────────────────────────
-- SecureAI-issued API keys (Protect / Analyze separated, rotatable)
-- ─────────────────────────────────────────────────────────────

create table if not exists public.api_keys (
    id              uuid primary key default gen_random_uuid(),
    project_id      uuid not null references public.projects (id) on delete cascade,
    name            text not null default '',
    key_type        text not null check (key_type in ('protect', 'analyze')),
    key_prefix      text not null,
    key_hash        text not null unique,   -- raw key never stored
    status          text not null default 'active' check (status in ('active', 'revoked')),
    rotated_from_id uuid references public.api_keys (id) on delete set null,
    last_used_at    timestamptz,
    expires_at      timestamptz,
    created_at      timestamptz not null default now(),
    revoked_at      timestamptz
);
create index if not exists idx_api_keys_project on public.api_keys (project_id, key_type, status);

-- ─────────────────────────────────────────────────────────────
-- Protect rules (fully data-driven, extensible with custom / org rules)
-- ─────────────────────────────────────────────────────────────

-- Catalog of PII entity types. Builtin rows have org_id NULL; org-scoped
-- custom types set org_id and must use a globally-unique code (e.g. prefixed).
create table if not exists public.pii_entity_types (
    code          text primary key,
    org_id        uuid references public.organizations (id) on delete cascade,
    label         text not null,
    category      text not null,
    default_regex text,
    is_builtin    boolean not null default false,
    created_at    timestamptz not null default now()
);
create index if not exists idx_pii_entity_types_org on public.pii_entity_types (org_id);

create table if not exists public.protect_rules (
    id                 uuid primary key default gen_random_uuid(),
    project_id         uuid not null references public.projects (id) on delete cascade,
    entity_type        text not null,          -- soft ref to pii_entity_types.code
    enabled            boolean not null default true,
    action             text not null default 'mask'
                         check (action in ('mask', 'redact', 'hash', 'replace', 'tokenize')),
    placeholder_format text not null default '<{type}_{n}>',
    config             jsonb not null default '{}',  -- score/regex/allow/deny
    priority           integer not null default 100,
    created_at         timestamptz not null default now(),
    updated_at         timestamptz not null default now(),
    unique (project_id, entity_type)
);

-- ─────────────────────────────────────────────────────────────
-- Logs & analytics (metadata only — no raw PII)
-- ─────────────────────────────────────────────────────────────

create table if not exists public.logs (
    id            uuid primary key default gen_random_uuid(),
    project_id    uuid not null references public.projects (id) on delete cascade,
    api_key_id    uuid references public.api_keys (id) on delete set null,
    provider_id   uuid references public.providers (id) on delete set null,
    endpoint      text not null check (endpoint in ('protect', 'analyze', 'detect')),
    request_id    text,
    status_code   integer,
    latency_ms    integer,
    input_chars   integer,
    entity_counts jsonb not null default '{}',
    token_usage   jsonb,
    error_code    text,
    ip_hash       text,
    created_at    timestamptz not null default now()
);
create index if not exists idx_logs_project_time on public.logs (project_id, created_at desc);
create index if not exists idx_logs_endpoint on public.logs (endpoint);

create table if not exists public.analytics_daily (
    id             uuid primary key default gen_random_uuid(),
    project_id     uuid not null references public.projects (id) on delete cascade,
    day            date not null,
    endpoint       text not null,
    request_count  integer not null default 0,
    error_count    integer not null default 0,
    protect_count  integer not null default 0,
    entity_counts  jsonb not null default '{}',
    provider_usage jsonb not null default '{}',
    avg_latency_ms integer,
    p95_latency_ms integer,
    token_total    bigint not null default 0,
    unique (project_id, day, endpoint)
);

-- ─────────────────────────────────────────────────────────────
-- Plugins & Export (future capability, provisioned now)
-- ─────────────────────────────────────────────────────────────

create table if not exists public.plugins (
    id            uuid primary key default gen_random_uuid(),
    plugin_key    text not null unique,
    category      text not null
                    check (category in ('extractor', 'augmentation', 'delivery', 'protocol')),
    version       text not null default '0.1.0',
    is_builtin    boolean not null default false,
    config_schema jsonb not null default '{}',
    created_at    timestamptz not null default now()
);

create table if not exists public.project_plugins (
    id         uuid primary key default gen_random_uuid(),
    project_id uuid not null references public.projects (id) on delete cascade,
    plugin_id  uuid not null references public.plugins (id) on delete cascade,
    enabled    boolean not null default false,
    config     jsonb not null default '{}',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (project_id, plugin_id)
);

create table if not exists public.export_templates (
    id         uuid primary key default gen_random_uuid(),
    project_id uuid references public.projects (id) on delete cascade,  -- NULL = global
    target_id  text not null
                 check (target_id in ('claude_code', 'codex', 'cursor', 'windsurf')),
    language   text not null default 'typescript',
    body       text not null,
    version    integer not null default 1,
    is_builtin boolean not null default false,
    created_at timestamptz not null default now()
);
create index if not exists idx_export_templates_lookup
    on public.export_templates (project_id, target_id, language);

-- ─────────────────────────────────────────────────────────────
-- Audit log
-- ─────────────────────────────────────────────────────────────

create table if not exists public.audit_logs (
    id             uuid primary key default gen_random_uuid(),
    org_id         uuid references public.organizations (id) on delete cascade,
    actor_user_id  uuid references public.users (id) on delete set null,
    action         text not null,
    resource_type  text not null,
    resource_id    uuid,
    metadata       jsonb not null default '{}',
    ip             text,
    created_at     timestamptz not null default now()
);
create index if not exists idx_audit_logs_org_time on public.audit_logs (org_id, created_at desc);

-- ─────────────────────────────────────────────────────────────
-- updated_at trigger
-- ─────────────────────────────────────────────────────────────

create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

create trigger trg_projects_updated before update on public.projects
    for each row execute function public.set_updated_at();
create trigger trg_providers_updated before update on public.providers
    for each row execute function public.set_updated_at();
create trigger trg_protect_rules_updated before update on public.protect_rules
    for each row execute function public.set_updated_at();
create trigger trg_project_plugins_updated before update on public.project_plugins
    for each row execute function public.set_updated_at();

-- On new auth user: create profile + a personal organization + owner membership.
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer as $$
declare
    new_org_id uuid;
begin
    insert into public.users (id, email) values (new.id, new.email)
        on conflict (id) do nothing;
    insert into public.organizations (name, slug, owner_id)
        values ('Personal', 'org-' || replace(new.id::text, '-', ''), new.id)
        returning id into new_org_id;
    insert into public.memberships (org_id, user_id, role)
        values (new_org_id, new.id, 'owner');
    return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
    after insert on auth.users
    for each row execute function public.handle_new_user();
