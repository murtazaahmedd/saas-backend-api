# SaaS Backend API

A **multi-tenant SaaS backend** in FastAPI and PostgreSQL, built the way production control planes are built:
strict layers, dependency injection, and every database operation behind a versioned `api.*` SQL function.
It covers the parts that are easy to get wrong: tenant isolation, role-based access, rate limiting, idempotent
retries, stable pagination and safe authentication.

## Architecture

```text
client
  │
  ▼
Router (app/routers)            endpoints, schema binding; no logic
  │  @http_error_handler        AppError -> JSON {error, detail} with the right status
  │  @enforce(permission)       JWT -> api.enforce(): membership + RBAC + rate limit, one DB round trip
  ▼
Schemas (app/schemas)           Pydantic request/response models, validation by field constraints
  ▼
ServiceContainer (app/services) business rules: idempotency, cursors, login
  ▼
RepositoryContainer (app/repositories)   calls api.* functions only (no inline SQL)
  ▼
PostgreSQL (db/)                tables, constraints, api.* PL/pgSQL functions
```

Dependencies only point downward. Services and repositories are created once in the composition root
(`app/main/app.py`) through lazily-loaded containers and injected via interfaces (`app/interfaces`), so every
layer can be tested with a fake of the one below it.

## What it handles

| Concern | How |
|---|---|
| **Tenant isolation** | The organization id comes only from the verified token, and every `api.*` function filters by it. Another tenant's project returns 404, not 403, so ids can't be probed. |
| **Role-based access** | `admin`, `member`, `viewer` mapped to `resource.action` permissions in `role_permissions`. Roles are re-checked in the database on every request, so demoting a user works immediately, even with an old token. |
| **Rate limiting** | Token bucket per user, refilled continuously at the plan's requests-per-minute, updated atomically inside `api.enforce`. Over the limit returns 429. |
| **Idempotent retries** | `Idempotency-Key` header on `POST /projects`: a retry returns the stored response (`Idempotent-Replayed: true`); reusing a key with a different body returns 409. |
| **Pagination** | Keyset (cursor) pagination on `(created_at, id)`: no skipped or duplicated rows under concurrent writes, constant cost at any depth. |
| **Authentication** | scrypt password hashes, short-lived HS256 JWTs, constant-time comparison, and identical responses for an unknown email and a wrong password. |
| **Data integrity** | Constraints in the database (checks, unique project name per tenant, case-insensitive), soft delete with a partial unique index so a deleted name can be reused. |
| **Errors** | One taxonomy (`app/errors`). SQL functions raise custom SQLSTATE codes (P0403, P0404, P0409, P0429) that map to HTTP statuses. |

## API

| Method | Path | Permission |
|---|---|---|
| `POST` | `/auth/signup` | public: creates an organization and its admin |
| `POST` | `/auth/token` | public: email + password -> access token |
| `POST` | `/users` | `user.create` (admin): invite a user with a role |
| `GET` | `/users/me` | `user.read` |
| `POST` | `/projects` | `project.create`, optional `Idempotency-Key` |
| `GET` | `/projects?status=&cursor=&limit=` | `project.read` |
| `GET` / `PATCH` / `DELETE` | `/projects/{id}` | `project.read` / `project.update` / `project.delete` (admin) |

Interactive docs at `/docs`.

## Run it

```bash
docker compose up --build            # Postgres + API, migrations applied on start
open http://localhost:8000/docs
```

Without Docker: start Postgres, then `pip install -r requirements.txt`, `DATABASE_URL=... python -m db.udf_load`,
and `DATABASE_URL=... JWT_SECRET=... make run`.

## Tests

12 integration tests run against a real PostgreSQL (a throwaway database per run; CI uses a Postgres service
container):

```bash
TEST_ADMIN_DSN=postgresql://postgres:postgres@localhost:5432/postgres make test
```

They cover signup and login, token tampering, validation, CRUD and soft delete, case-insensitive uniqueness,
tenant isolation, every role boundary, pagination across pages, idempotent replay and misuse, rate limiting, and
immediate effect of a role change.

## Project layout

```text
app/
  routers/        auth, users, projects
  decorators/     http_error_handler, enforce
  schemas/        Pydantic models
  services/       auth, users, projects + ServiceContainer
  repositories/   Database (api.* calls only) + repositories + RepositoryContainer
  interfaces/     ABCs for every repository and service
  utilities/      password hashing, JWT
  constants/      permission names
  errors/         error taxonomy and SQLSTATE mapping
  main/           composition root
db/
  schema.sql      tables, constraints, seed permissions and plan limits
  udf/api/        enforce, users, projects, idempotency functions
  udf_load.py     idempotent migration
```
