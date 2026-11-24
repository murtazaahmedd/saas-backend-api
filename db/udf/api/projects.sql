-- Every function takes the organization id from the verified auth context: tenants can never see each other.
CREATE OR REPLACE FUNCTION api.project_create(p_org_id uuid, p_user_id uuid, p_name text, p_description text)
RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE v projects%ROWTYPE;
BEGIN
    INSERT INTO projects (organization_id, name, description, created_by)
        VALUES (p_org_id, p_name, coalesce(p_description, ''), p_user_id) RETURNING * INTO v;
    RETURN to_jsonb(v) - 'deleted_at' - 'organization_id';
EXCEPTION WHEN unique_violation THEN
    RAISE EXCEPTION 'a project named % already exists', p_name USING ERRCODE = 'P0409';
END $$;

CREATE OR REPLACE FUNCTION api.project_get(p_org_id uuid, p_id uuid)
RETURNS jsonb LANGUAGE plpgsql STABLE AS $$
DECLARE v jsonb;
BEGIN
    WITH p AS (SELECT * FROM projects WHERE id = p_id AND organization_id = p_org_id AND deleted_at IS NULL)
    SELECT to_jsonb(p) - 'deleted_at' - 'organization_id' INTO v FROM p;
    IF v IS NULL THEN
        RAISE EXCEPTION 'project % not found', p_id USING ERRCODE = 'P0404';
    END IF;
    RETURN v;
END $$;

-- Keyset pagination: stable under concurrent inserts, O(limit) regardless of page depth.
CREATE OR REPLACE FUNCTION api.project_list(p_org_id uuid, p_status text, p_after_created timestamptz,
                                            p_after_id uuid, p_limit integer)
RETURNS jsonb LANGUAGE sql STABLE AS $$
    WITH page AS (
        SELECT * FROM projects
        WHERE organization_id = p_org_id AND deleted_at IS NULL
          AND (p_status IS NULL OR status = p_status)
          AND (p_after_created IS NULL OR (created_at, id) < (p_after_created, p_after_id))
        ORDER BY created_at DESC, id DESC
        LIMIT p_limit + 1
    ), numbered AS (
        SELECT *, row_number() OVER (ORDER BY created_at DESC, id DESC) AS rn FROM page
    )
    SELECT jsonb_build_object(
        'items', coalesce(jsonb_agg(to_jsonb(n) - 'deleted_at' - 'organization_id' - 'rn' ORDER BY rn)
                          FILTER (WHERE rn <= p_limit), '[]'::jsonb),
        'has_more', count(*) > p_limit)
    FROM numbered n;
$$;

CREATE OR REPLACE FUNCTION api.project_update(p_org_id uuid, p_id uuid, p_patch jsonb)
RETURNS jsonb LANGUAGE plpgsql AS $$
BEGIN
    UPDATE projects SET
        name        = coalesce(p_patch->>'name', name),
        description = coalesce(p_patch->>'description', description),
        status      = coalesce(p_patch->>'status', status),
        updated_at  = now()
    WHERE id = p_id AND organization_id = p_org_id AND deleted_at IS NULL;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'project % not found', p_id USING ERRCODE = 'P0404';
    END IF;
    RETURN api.project_get(p_org_id, p_id);
EXCEPTION WHEN unique_violation THEN
    RAISE EXCEPTION 'a project named % already exists', p_patch->>'name' USING ERRCODE = 'P0409';
END $$;

CREATE OR REPLACE FUNCTION api.project_soft_delete(p_org_id uuid, p_id uuid)
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
    UPDATE projects SET deleted_at = now() WHERE id = p_id AND organization_id = p_org_id AND deleted_at IS NULL;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'project % not found', p_id USING ERRCODE = 'P0404';
    END IF;
END $$;
