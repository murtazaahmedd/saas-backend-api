import psycopg


def make(client, headers, name, **extra):
    return client.post("/projects", json={"name": name, **extra}, headers=headers)


def test_signup_login_and_me(client, tenant):
    token = client.post("/auth/token", json={"email": tenant["email"], "password": "correct-horse-battery"})
    assert token.status_code == 200
    me = client.get("/users/me", headers={"Authorization": f"Bearer {token.json()['access_token']}"}).json()
    assert me["role"] == "admin" and me["organization_id"] == tenant["organization_id"]


def test_wrong_password_and_unknown_email_get_the_same_answer(client, tenant):
    a = client.post("/auth/token", json={"email": tenant["email"], "password": "wrong-password-123"})
    b = client.post("/auth/token", json={"email": "nobody@example.com", "password": "wrong-password-123"})
    assert a.status_code == b.status_code == 401 and a.json() == b.json()


def test_missing_and_tampered_tokens_are_rejected(client, tenant):
    assert client.get("/projects").status_code == 401
    bad = {"Authorization": tenant["headers"]["Authorization"][:-2] + "xx"}
    assert client.get("/projects", headers=bad).json()["detail"] == "invalid access token"


def test_validation_errors_are_422(client, tenant):
    assert make(client, tenant["headers"], "").status_code == 422
    assert make(client, tenant["headers"], "ok", owner="me").status_code == 422     # extra fields forbidden


def test_crud_and_soft_delete(client, tenant):
    h = tenant["headers"]
    pid = make(client, h, "Apollo", description="moon").json()["id"]
    assert client.patch(f"/projects/{pid}", json={"status": "paused"}, headers=h).json()["status"] == "paused"
    assert client.delete(f"/projects/{pid}", headers=h).json() == {"message": "Deleted successfully"}
    assert client.get(f"/projects/{pid}", headers=h).status_code == 404
    assert make(client, h, "Apollo").status_code == 201        # name is free again after soft delete


def test_duplicate_name_is_a_conflict(client, tenant):
    make(client, tenant["headers"], "Gemini")
    r = make(client, tenant["headers"], "gemini")             # case-insensitive
    assert r.status_code == 409


def test_tenants_are_isolated(client, tenant):
    other = client.post("/auth/signup", json={"organization_name": "Other Org", "email": "other-" + tenant["email"],
                                              "password": "correct-horse-battery"}).json()
    pid = make(client, tenant["headers"], "Secret").json()["id"]
    other_h = {"Authorization": f"Bearer {other['access_token']}"}
    assert client.get(f"/projects/{pid}", headers=other_h).status_code == 404
    assert client.delete(f"/projects/{pid}", headers=other_h).status_code == 404
    assert client.get("/projects", headers=other_h).json()["items"] == []


def test_role_based_access(client, tenant, invite):
    viewer, member = invite(tenant, "viewer"), invite(tenant, "member")
    assert make(client, viewer, "Nope").status_code == 403
    pid = make(client, member, "Member project").json()["id"]
    assert client.get(f"/projects/{pid}", headers=viewer).status_code == 200
    assert client.delete(f"/projects/{pid}", headers=member).status_code == 403
    assert client.post("/users", json={"email": "x@example.com", "password": "correct-horse-battery"},
                       headers=member).status_code == 403


def test_keyset_pagination_walks_every_row_once(client, tenant):
    h = tenant["headers"]
    names = {f"P{i:02d}" for i in range(23)}
    for n in names:
        make(client, h, n)
    seen, cursor, pages = [], None, 0
    while True:
        page = client.get("/projects", params={"limit": 10, **({"cursor": cursor} if cursor else {})}, headers=h).json()
        seen += [p["name"] for p in page["items"]]
        pages += 1
        cursor = page["next_cursor"]
        if not cursor:
            break
    assert pages == 3 and sorted(seen) == sorted(names)
    assert client.get("/projects", params={"cursor": "garbage"}, headers=h).status_code == 400


def test_idempotency_key_replays_and_detects_misuse(client, tenant):
    h = {**tenant["headers"], "Idempotency-Key": "create-artemis-1"}
    first = client.post("/projects", json={"name": "Artemis"}, headers=h)
    again = client.post("/projects", json={"name": "Artemis"}, headers=h)
    assert first.status_code == 201 and again.headers["Idempotent-Replayed"] == "true"
    assert first.json()["id"] == again.json()["id"]
    assert client.post("/projects", json={"name": "Different"}, headers=h).status_code == 409


def test_rate_limit_returns_429_when_bucket_is_empty(client, tenant, dsn):
    client.get("/projects", headers=tenant["headers"])          # creates the bucket
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute("UPDATE rate_buckets SET tokens = 0, refilled_at = now() WHERE user_id = %s", [tenant["user_id"]])
    r = client.get("/projects", headers=tenant["headers"])
    assert r.status_code == 429 and r.json()["error"] == "rate_limited"


def test_revoked_access_takes_effect_immediately(client, tenant, invite, dsn):
    member = invite(tenant, "member")
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute("UPDATE users SET role = 'viewer' WHERE email LIKE 'member-%%' AND organization_id = %s",
                     [tenant["organization_id"]])
    assert make(client, member, "After demotion").status_code == 403    # same token, new role
