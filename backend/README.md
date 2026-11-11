# DME Order Intake Backend

Python FastAPI foundation for the DME Order Intake MVP.

## Requirements

- Python 3.12+
- pip (or an equivalent installer such as uv)
- Docker Desktop (or Docker Engine + Compose) for local PostgreSQL only

## Layout

```text
app/
  api/           # HTTP routes and FastAPI dependencies
  core/          # Settings, logging, error handlers
  schemas/       # Pydantic request/response models
  services/      # Business logic (future)
  db/            # Database engine and session helpers
  integrations/  # External adapters such as AI extraction (future)
  main.py        # Application entry point
```

## Local PostgreSQL (Docker)

From the repository root, start only PostgreSQL:

```bash
docker compose up -d
docker compose ps
```

Defaults (override with a root `.env` if needed):

- User: `dme`
- Password: `dme`
- Database: `dme_order_intake`
- Host port: `127.0.0.1:5432` (localhost only)

Stop PostgreSQL:

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

Edit `.env` as needed. Keep `DATABASE_URL` aligned with the Compose credentials. Do not commit real secrets.

## Run the API (on the laptop, not in Docker)

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Interactive docs (development): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Notes

- Authentication, order CRUD, database models/migrations, and AI extraction are intentionally out of scope for this slice.
- SQLAlchemy 2.0 uses synchronous sessions with Psycopg 3. Request handlers obtain a session through `DbSessionDep`.
- Configuration is loaded via Pydantic Settings from environment variables and an optional `.env` file.
