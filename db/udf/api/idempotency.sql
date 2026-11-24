-- Idempotency keys: a retried POST with the same key returns the stored response instead of acting twice.
CREATE OR REPLACE FUNCTION api.idempotency_get(p_org_id uuid, p_key text)
RETURNS jsonb LANGUAGE sql STABLE AS $$
    WITH k AS (SELECT request_hash, response, status_code FROM idempotency_keys
               WHERE organization_id = p_org_id AND key = p_key AND created_at > now() - interval '24 hours')
    SELECT to_jsonb(k) FROM k;
$$;

CREATE OR REPLACE FUNCTION api.idempotency_put(p_org_id uuid, p_key text, p_hash text, p_response jsonb, p_status integer)
RETURNS void LANGUAGE sql AS $$
    INSERT INTO idempotency_keys (organization_id, key, request_hash, response, status_code)
    VALUES (p_org_id, p_key, p_hash, p_response, p_status)
    ON CONFLICT (organization_id, key) DO NOTHING;
$$;
