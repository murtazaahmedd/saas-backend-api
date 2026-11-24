CREATE OR REPLACE FUNCTION api.signup(p_org_name text, p_email text, p_password_hash text)
RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE v_org uuid; v_user uuid;
BEGIN
    IF EXISTS (SELECT 1 FROM users WHERE lower(email) = lower(p_email)) THEN
        RAISE EXCEPTION 'email % is already registered', p_email USING ERRCODE = 'P0409';
    END IF;
    INSERT INTO organizations (name) VALUES (p_org_name) RETURNING id INTO v_org;
    INSERT INTO users (organization_id, email, password_hash, role)
        VALUES (v_org, lower(p_email), p_password_hash, 'admin') RETURNING id INTO v_user;
    RETURN jsonb_build_object('organization_id', v_org, 'user_id', v_user, 'role', 'admin');
END $$;

CREATE OR REPLACE FUNCTION api.user_create(p_org_id uuid, p_email text, p_password_hash text, p_role text)
RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE v_row users%ROWTYPE;
BEGIN
    IF EXISTS (SELECT 1 FROM users WHERE lower(email) = lower(p_email)) THEN
        RAISE EXCEPTION 'email % is already registered', p_email USING ERRCODE = 'P0409';
    END IF;
    INSERT INTO users (organization_id, email, password_hash, role)
        VALUES (p_org_id, lower(p_email), p_password_hash, p_role) RETURNING * INTO v_row;
    RETURN jsonb_build_object('id', v_row.id, 'email', v_row.email, 'role', v_row.role, 'created_at', v_row.created_at);
END $$;

-- Login lookup. Returns NULL for an unknown email so the caller can give the same answer as a bad password.
CREATE OR REPLACE FUNCTION api.user_credentials(p_email text)
RETURNS jsonb LANGUAGE sql STABLE AS $$
    WITH u AS (SELECT id, organization_id, password_hash, role FROM users WHERE email = lower(p_email))
    SELECT to_jsonb(u) FROM u;
$$;
