-- Control-plane schema. Every tenant-owned row carries organization_id; every read goes through api.* functions.
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE SCHEMA IF NOT EXISTS api;

CREATE TABLE IF NOT EXISTS organizations (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name        text NOT NULL CHECK (length(name) BETWEEN 2 AND 80),
    plan        text NOT NULL DEFAULT 'free' CHECK (plan IN ('free', 'pro')),
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS users (
    id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id  uuid NOT NULL REFERENCES organizations(id),
    email            text NOT NULL UNIQUE CHECK (email ~* '^[^@\s]+@[^@\s]+\.[^@\s]+$'),
    password_hash    text NOT NULL,
    role             text NOT NULL CHECK (role IN ('admin', 'member', 'viewer')),
    created_at       timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role        text NOT NULL,
    permission  text NOT NULL,
    PRIMARY KEY (role, permission)
);

CREATE TABLE IF NOT EXISTS plan_limits (
    plan                text PRIMARY KEY,
    requests_per_minute integer NOT NULL
);

CREATE TABLE IF NOT EXISTS rate_buckets (
    user_id      uuid PRIMARY KEY REFERENCES users(id),
    tokens       double precision NOT NULL,
    refilled_at  timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
    id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id  uuid NOT NULL REFERENCES organizations(id),
    name             text NOT NULL CHECK (length(name) BETWEEN 1 AND 120),
    description      text NOT NULL DEFAULT '',
    status           text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'paused', 'done')),
    created_by       uuid NOT NULL REFERENCES users(id),
    created_at       timestamptz NOT NULL DEFAULT now(),
    updated_at       timestamptz NOT NULL DEFAULT now(),
    deleted_at       timestamptz
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_projects_org_name ON projects (organization_id, lower(name)) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS ix_projects_org_page ON projects (organization_id, created_at DESC, id DESC) WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS idempotency_keys (
    organization_id  uuid NOT NULL,
    key              text NOT NULL,
    request_hash     text NOT NULL,
    response         jsonb NOT NULL,
    status_code      integer NOT NULL,
    created_at       timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (organization_id, key)
);

INSERT INTO role_permissions VALUES
    ('admin', 'project.read'), ('admin', 'project.create'), ('admin', 'project.update'), ('admin', 'project.delete'),
    ('admin', 'user.create'), ('admin', 'user.read'),
    ('member', 'project.read'), ('member', 'project.create'), ('member', 'project.update'), ('member', 'user.read'),
    ('viewer', 'project.read')
ON CONFLICT DO NOTHING;
INSERT INTO plan_limits VALUES ('free', 60), ('pro', 600) ON CONFLICT DO NOTHING;
