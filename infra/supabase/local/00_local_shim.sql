-- LOCAL DEV ONLY — emulates the parts of Supabase's `auth` schema that the
-- migrations reference (auth.users, auth.uid()). A real Supabase project
-- already provides these, so DO NOT run this on Supabase.

create extension if not exists pgcrypto;

create schema if not exists auth;

create table if not exists auth.users (
    id    uuid primary key default gen_random_uuid(),
    email text
);

-- Emulates Supabase's auth.uid(): the authenticated user id from the JWT.
-- Locally derived from a session GUC (set by tests), else NULL.
create or replace function auth.uid()
returns uuid language sql stable as $$
    select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid;
$$;
