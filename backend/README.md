# DME Order Intake Backend

Python FastAPI foundation for the DME Order Intake MVP.

## Requirements

- Python 3.12+
- pip (or an equivalent installer such as uv)

## Layout

```text
app/
  api/           # HTTP routes and FastAPI dependencies
  core/          # Settings, logging, error handlers
  schemas/       # Pydantic request/response models
  services/      # Business logic (future)
  db/            # Database infrastructure (future)
  integrations/  # External adapters such as AI extraction (future)
  main.py        # Application entry point
```

## Setup

From the `backend/` directory:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

Edit `.env` as needed. Do not commit real secrets.

## Run

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

- Authentication, order CRUD, database models, and AI extraction are intentionally out of scope for this foundation slice.
- Configuration is loaded via Pydantic Settings from environment variables and an optional `.env` file.
