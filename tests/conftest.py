import os
import uuid

import psycopg
from psycopg.conninfo import make_conninfo
import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from db.udf_load import migrate

ADMIN_DSN = os.getenv("TEST_ADMIN_DSN", "postgresql://postgres@/postgres?host=/tmp")


@pytest.fixture(scope="session")
def dsn():
    name = f"saas_test_{uuid.uuid4().hex[:8]}"
    with psycopg.connect(ADMIN_DSN, autocommit=True) as conn:
        conn.execute(f"CREATE DATABASE {name}")
    test_dsn = make_conninfo(ADMIN_DSN, dbname=name)
    migrate(test_dsn)
    yield test_dsn
    with psycopg.connect(ADMIN_DSN, autocommit=True) as conn:
        conn.execute(f"DROP DATABASE {name} WITH (FORCE)")


@pytest.fixture(scope="session")
def client(dsn):
    with TestClient(create_app(dsn, "test-secret-" + "x" * 32)) as c:
        yield c


@pytest.fixture
def tenant(client):
    """A fresh organization with an admin token."""
    email = f"admin-{uuid.uuid4().hex[:8]}@example.com"
    body = client.post("/auth/signup", json={"organization_name": "Org " + email[:12], "email": email,
                                             "password": "correct-horse-battery"}).json()
    return {"email": email, "headers": {"Authorization": f"Bearer {body['access_token']}"}, **body}


@pytest.fixture
def invite(client):
    def _invite(tenant, role):
        email = f"{role}-{uuid.uuid4().hex[:8]}@example.com"
        client.post("/users", json={"email": email, "password": "correct-horse-battery", "role": role},
                    headers=tenant["headers"])
        token = client.post("/auth/token", json={"email": email, "password": "correct-horse-battery"}).json()
        return {"Authorization": f"Bearer {token['access_token']}"}
    return _invite
