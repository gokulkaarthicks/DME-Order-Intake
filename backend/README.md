# DME Order Intake Backend

Python FastAPI foundation for the DME Order Intake MVP.

## Requirements

- Python 3.12+
- pip (or an equivalent installer such as uv)
- Docker Desktop (or Docker Engine + Compose) for local services
- `DEEPSEEK_API_KEY` for live PDF extraction

## Layout

```text
app/
  api/           # HTTP routes and FastAPI dependencies
  core/          # Settings, logging, error handlers, NPI helpers
  schemas/       # Pydantic request/response models
  services/      # Business logic (auth, orders, extraction)
  db/            # Engine, sessions, ORM models
  integrations/  # PDF processor and DeepSeek extraction adapter
  main.py        # Application entry point
alembic/         # Database migrations
```

## Local PostgreSQL (Docker)

From the repository root, start all services (see the root README for configuration):

```bash
docker compose up -d
docker compose ps
```

Defaults (override with a root `.env` if needed):

- User: `dme`
- Password: `dme`
- Database: `dme_order_intake`
- Host port: `127.0.0.1:5434` (localhost only; avoids a common clash with system Postgres on 5432)

Stop the services:

```bash
docker compose down
```

Data persists in the named Docker volume `postgres_data`. Use `docker compose down -v` only when you intend to delete local database data.

## Backend setup

From the `backend/` directory:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

Edit `.env` as needed. Keep `DATABASE_URL` aligned with the Compose credentials. Set `JWT_SECRET_KEY` and `DEEPSEEK_API_KEY`. Do not commit real secrets.

## Database migrations

With PostgreSQL running and the virtualenv active:

```bash
cd backend
alembic upgrade head
alembic current
```

Schema changes must go through Alembic. Compose runs `alembic upgrade head` before starting the API. The API does not call `create_all` on startup.

## Run the API (on the laptop, not in Docker)

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

PDF upload (authenticated):

```bash
curl -X POST http://127.0.0.1:8000/api/orders/upload \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@order.pdf;type=application/pdf"
```

Interactive docs (development): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Tests

Install test extras and run pytest from `backend/` (uses isolated DB `dme_order_intake_test` on port 5434):

```bash
pip install -e ".[test]"
pytest
```

DeepSeek calls are mocked in automated tests. Live model verification requires `DEEPSEEK_API_KEY`.

## Notes

- Auth endpoints: `POST /api/auth/register` and `POST /api/auth/login` accept JSON such as `{"username":"employee_1","password":"your-password"}`. Usernames are trimmed, lowercased, 3 to 32 ASCII letters, digits, or underscores, and unique case-insensitively.
- Existing accounts are migrated from email prefixes. Unsupported characters become underscores, short names are padded, and collisions receive numeric suffixes in user ID order. Ask an administrator for the assigned username if needed. Passwords and orders are preserved. The original email addresses are removed, so this migration cannot be downgraded without restoring a backup.
- Order endpoints: `GET /api/orders`, `GET/PATCH/DELETE /api/orders/{id}`, and `POST /api/orders/upload` (JWT required; ownership enforced). No standalone manual creation endpoint exists.
- PDF upload: `POST /api/orders/upload` extracts five fields via DeepSeek (`deepseek-flash`) and persists only when validation passes.
- Upload responses use `status=created` with `saved=true`, or `status=needs_review` with `saved=false`, field errors, and a short-lived review token. To submit corrections, send the original PDF as `file`, the token as `review_token`, and a JSON object with all five corrected fields as `corrections` in the same multipart upload. The token is bound to the authenticated user and PDF bytes and expires after 60 minutes. Re-upload if review expires. A review proof can be used only once, whether the user saves a review or submits an immediate correction.
- Original PDFs are processed in memory only and are not stored permanently.
- ORM models live in `app/db/models.py` and stay separate from API request/response schemas.
- SQLAlchemy 2.0 uses synchronous sessions with Psycopg 3. Request handlers obtain a session through `DbSessionDep`.
- Configuration is loaded via Pydantic Settings from environment variables and an optional `.env` file.

## Human review

For `needs_review`, `POST /api/reviews` accepts the returned `extracted` object and `review_token`. The server verifies the signed extraction result and recomputes errors. `GET /api/reviews` lists the authenticated user's pending items. `POST /api/reviews/{id}/resolve` accepts the five corrected fields and atomically creates a validated order and resolves the review. A repeat resolution returns 409. The original PDF is not stored and DeepSeek is not called again for saving or resolving a review.
