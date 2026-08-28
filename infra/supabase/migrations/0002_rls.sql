-- SecureAI Studio — Row Level Security
-- Tenant isolation keyed to the authenticated user's org memberships.
-- The data plane writes (logs, analytics) run under the service role, which
-- bypasses RLS; the application still verifies project ownership in code.

-- ── Membership helpers ──
create or replace function public.is_org_member(p_org uuid)
returns boolean language sql stable security definer set search_path = public as $$
    select exists (
        select 1 from public.memberships m
        where m.org_id = p_org and m.user_id = auth.uid()
    );
$$;

create or replace function public.is_project_member(p_project uuid)
returns boolean language sql stable security definer set search_path = public as $$
    select exists (
        select 1
        from public.projects pr
        join public.memberships m on m.org_id = pr.org_id
        where pr.id = p_project and m.user_id = auth.uid()
    );
$$;

create or replace function public.is_provider_member(p_provider uuid)
returns boolean language sql stable security definer set search_path = public as $$
    select exists (
        select 1
        from public.providers pv
        join public.projects pr on pr.id = pv.project_id
        join public.memberships m on m.org_id = pr.org_id
        where pv.id = p_provider and m.user_id = auth.uid()
    );
$$;

-- ── Enable RLS ──
alter table public.users             enable row level security;
alter table public.organizations     enable row level security;
alter table public.memberships       enable row level security;
alter table public.projects          enable row level security;
alter table public.providers         enable row level security;
alter table public.provider_keys     enable row level security;
alter table public.api_keys          enable row level security;
alter table public.pii_entity_types  enable row level security;
alter table public.protect_rules     enable row level security;
alter table public.logs              enable row level security;
alter table public.analytics_daily   enable row level security;
alter table public.plugins           enable row level security;
alter table public.project_plugins   enable row level security;
alter table public.export_templates  enable row level security;
alter table public.audit_logs        enable row level security;

-- ── Policies ──
create policy users_self on public.users
    for select using (id = auth.uid());

create policy orgs_member_read on public.organizations
    for select using (is_org_member(id));

create policy memberships_member_read on public.memberships
    for select using (is_org_member(org_id));

create policy projects_member_all on public.projects
    for all using (is_org_member(org_id)) with check (is_org_member(org_id));

create policy providers_member_all on public.providers
    for all using (is_project_member(project_id)) with check (is_project_member(project_id));

create policy provider_keys_member_all on public.provider_keys
    for all using (is_provider_member(provider_id)) with check (is_provider_member(provider_id));

create policy api_keys_member_all on public.api_keys
    for all using (is_project_member(project_id)) with check (is_project_member(project_id));

-- Builtin catalog rows (org_id null) are visible to everyone; org rows scoped.
create policy pii_types_read on public.pii_entity_types
    for select using (org_id is null or is_org_member(org_id));
create policy pii_types_write on public.pii_entity_types
    for all using (org_id is not null and is_org_member(org_id))
    with check (org_id is not null and is_org_member(org_id));

create policy protect_rules_member_all on public.protect_rules
    for all using (is_project_member(project_id)) with check (is_project_member(project_id));

create policy logs_member_read on public.logs
    for select using (is_project_member(project_id));

create policy analytics_member_read on public.analytics_daily
    for select using (is_project_member(project_id));

-- Plugin catalog is readable by any authenticated user; writes are admin/service.
create policy plugins_read on public.plugins
    for select using (auth.uid() is not null);

create policy project_plugins_member_all on public.project_plugins
    for all using (is_project_member(project_id)) with check (is_project_member(project_id));

create policy export_templates_read on public.export_templates
    for select using (project_id is null or is_project_member(project_id));
create policy export_templates_write on public.export_templates
    for all using (project_id is not null and is_project_member(project_id))
    with check (project_id is not null and is_project_member(project_id));

create policy audit_logs_member_read on public.audit_logs
    for select using (is_org_member(org_id));
