-- Authorisation and rate limiting in one atomic call: membership, RBAC, then a token bucket per user.
-- Raises P0401 (unknown user), P0403 (missing permission), P0429 (rate limited).
CREATE OR REPLACE FUNCTION api.enforce(p_user_id uuid, p_org_id uuid, p_permission text)
RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE
    v_user   users%ROWTYPE;
    v_plan   text;
    v_rpm    integer;
    v_tokens double precision;
BEGIN
    SELECT * INTO v_user FROM users WHERE id = p_user_id AND organization_id = p_org_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'user % is not a member of organization %', p_user_id, p_org_id USING ERRCODE = 'P0401';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM role_permissions WHERE role = v_user.role AND permission = p_permission) THEN
        RAISE EXCEPTION 'role % lacks permission %', v_user.role, p_permission USING ERRCODE = 'P0403';
    END IF;

    SELECT o.plan, l.requests_per_minute INTO v_plan, v_rpm
    FROM organizations o JOIN plan_limits l ON l.plan = o.plan WHERE o.id = p_org_id;

    INSERT INTO rate_buckets AS b (user_id, tokens, refilled_at) VALUES (p_user_id, v_rpm, now())
    ON CONFLICT (user_id) DO UPDATE
        SET tokens = LEAST(v_rpm, b.tokens + extract(epoch FROM now() - b.refilled_at) * v_rpm / 60.0),
            refilled_at = now()
    RETURNING tokens INTO v_tokens;
    IF v_tokens < 1 THEN
        RAISE EXCEPTION 'rate limit of % requests per minute exceeded', v_rpm USING ERRCODE = 'P0429';
    END IF;
    UPDATE rate_buckets SET tokens = tokens - 1 WHERE user_id = p_user_id;

    RETURN jsonb_build_object('user_id', v_user.id, 'organization_id', v_user.organization_id,
                              'role', v_user.role, 'plan', v_plan, 'remaining', floor(v_tokens - 1));
END $$;
