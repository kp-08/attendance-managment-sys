# Attendance + Phonebook — Backend

A focused, developer-friendly documentation for the Attendance + Phonebook service (Auth · Employees · Attendance · Holidays · Leave).
Designed for quick setup, testing, and handoff — not a marketing page.

---

# Project summary

This service provides backend APIs for:

- Email/password login (JWT)
- Employee management (create/list/get)
- Attendance: check-in / check-out, list with date filters
- Holidays: create & list
- Leave: apply / list / approve / reject, with per-year leave balances
- Pagination, search, filtering and sorting on list endpoints
- Alembic migrations and automated pytest suite

**Tech:** FastAPI, SQLAlchemy, PostgreSQL, Docker Compose, Alembic, pytest.

---

# Quick start (development)

These commands assume you are in the project root and have Docker & docker-compose installed.

1. Copy and edit environment variables:

```bash
cp .env.example .env
# open .env and set SECRET_KEY (see below)
```

2. Generate a SECRET_KEY (example):

```bash
openssl rand -hex 32
# paste value into SECRET_KEY in .env
```

3. Build & start services:

```bash
docker compose up -d --build
```

4. Seed initial data (admin user, leave types, department):

```bash
docker compose exec backend python seed_data.py
```

5. Open the API docs (interactive):

```
http://localhost:8000/docs
```

---

# .env (example)

Create a `.env` file with at least:

```
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=attendance_db
POSTGRES_HOST=db
POSTGRES_PORT=5432
DATABASE_URL=postgresql+psycopg2://postgres:postgres@db:5432/attendance_db

SECRET_KEY=<your-hex-secret>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

APP_ENV=development
```

> **Do not** commit `.env` to source control.

---

# Common commands

Start/stop:

```bash
docker compose up -d --build
docker compose down
```

Rebuild backend only:

```bash
docker compose up -d --build backend
```

Run seed:

```bash
docker compose exec backend python seed_data.py
```

Run tests:

```bash
docker compose exec backend pytest -q
```

Enter backend shell:

```bash
docker compose exec backend bash
```

Run alembic (inside backend container):

```bash
alembic revision --autogenerate -m "message"
alembic upgrade head
alembic stamp head
```

Inspect DB from host (psql inside container):

```bash
docker compose exec db psql -U postgres -d attendance_db
# then SQL or \dt
```

---

# API (short reference & examples)

> Base URL: `http://localhost:8000`

**Auth**

- `POST /auth/login` — form data: `username`, `password`

Example:

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -d "username=admin@example.com&password=adminpass"
```

Response: `{ "access_token": "...", "token_type": "bearer" }`

Use `Authorization: Bearer <token>` header for protected endpoints.

---

**Employees**

- `GET /employees/list` — supports `skip`, `limit`, `q`, `sort_by`, `order`
  Example: `/employees/list?skip=0&limit=20&q=rahul&sort_by=first_name&order=asc`
- `POST /employees/create` — admin only, JSON body with fields: `first_name`, `last_name`, `email`, `password`, `phone`, `designation`, `department_id`, `role`
- `GET /employees/{id}` — get employee detail

---

**Attendance**

- `POST /attendance/check-in` — current user checks in
- `POST /attendance/check-out` — current user checks out
- `GET /attendance/list` — supports `skip`, `limit`, `employee_id`, `start_date`, `end_date`, `sort_by`, `order`
  Example: `/attendance/list?employee_id=5&start_date=2026-02-01&end_date=2026-02-10&sort_by=date&order=desc`

---

**Holidays**

- `POST /holidays/create` — admin only (JSON: `name`, `date`, `description`)
- `GET /holidays/list`

---

**Leave**

- `POST /leave/apply` — JSON: `leave_type_id`, `start_date`, `end_date`, `reason`
- `GET /leave/list` — list leaves (admin/manager see more)
- `PUT /leave/{id}/approve` — admin/manager can approve (updates `leave_balance`)
- `PUT /leave/{id}/reject` — admin/manager can reject

---

# Testing strategy

- Automated tests with `pytest` live in `app/tests/`. Tests reset DB schema (drop/create) in the test fixtures; don't run tests against production DB.
- Run tests inside the backend container:

```bash
docker compose exec backend pytest -q
```

All core flows are covered: auth, employees, attendance, leave, pagination, search, sorting.

---

# Migrations (Alembic)

Alembic is configured to use the app SQLAlchemy metadata.

Typical workflow:
1. Inside backend container: `alembic revision --autogenerate -m "describe change"`
2. Review the generated file in `alembic/versions/`
3. Apply: `alembic upgrade head`

If you already used `Base.metadata.create_all()` earlier and want to bring the DB under Alembic control without losing data, use:

```bash
alembic stamp head
```

This marks the current DB state as having applied the current migration set (no SQL executed).

---

# pgAdmin (optional)

You can add a pgAdmin service to `docker-compose.yml` or use a local DB client.

Example pgAdmin service (dev only):

```yaml
pgadmin:
  image: dpage/pgadmin4:7
  restart: always
  environment:
    PGADMIN_DEFAULT_EMAIL: admin@local
    PGADMIN_DEFAULT_PASSWORD: adminpass
  ports:
    - "8080:80"
  depends_on:
    - db
```

Connect inside pgAdmin to host `db`, port `5432`, database `attendance_db`, user `postgres`, password from `.env`.

---

# Troubleshooting tips

- `docker compose logs -f backend` for backend errors (stack traces).
- If JWT errors occur: ensure `SECRET_KEY` in `.env` is set consistently.
- If tests fail due to import issues: ensure the test runner runs from project root or use the `sys.path` fix in `conftest.py` (already present).
- If Alembic autogenerate shows unexpected changes, verify all models are imported in `alembic/env.py`.

---

# Security & production notes (brief)

- Do not use `Base.metadata.create_all` in production. Use Alembic for controlled schema changes.
- Store secrets in a secure store (Vault, cloud secrets manager) in production — do not use `.env`.
- Use HTTPS and proper CORS / rate limiting for public deployments.
- Rotate `SECRET_KEY` only with careful token handling (or plan a re-auth flow).

---

# Next recommended small improvements

(ordered by impact)
1. **Transaction-safety for leave approval** — use DB row locking to avoid race conditions on leave balance.
2. **DB indexes** on `employees.email`, `employees.phone`, and `attendance_records.date` (add via Alembic).
3. **Minimal frontend** for a read-and-demo UI (React/Next) — login, employees list, check-in, leave apply.
4. **CI pipeline** to run tests on push (GitHub Actions).

If you want, I can implement any of these next — e.g., add transaction safety and the small Alembic migration for indexes. Which do you want me to pick next?

---

# Contact / author

Maintainer: Krish Patel (from project context) — if anything in this README is out of date for your repo, tell me what changed and I’ll update the doc.
