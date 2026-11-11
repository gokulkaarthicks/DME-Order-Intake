# DME Order Intake

Run PostgreSQL, FastAPI, and React locally with Docker Compose. Docker Desktop or Docker Engine with Compose is required.

## Setup and start

1. Copy `backend/.env.example` to `backend/.env` if it does not already exist. Set a private `JWT_SECRET_KEY` of at least 32 characters and set `DEEPSEEK_API_KEY` for live PDF extraction. Keep this file private and do not commit it.
2. From the repository root, run:

```bash
docker compose up -d --build
```

Open [http://localhost:5173](http://localhost:5173). The API is at [http://localhost:8001](http://localhost:8001), with documentation at `/docs`. PostgreSQL is available on `127.0.0.1:5434`. The frontend uses a same-origin Vite proxy to reach the backend. The backend waits for PostgreSQL health and runs Alembic migrations before accepting requests. A migration failure prevents the API from starting.

The Compose database URL uses `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` from the shell or root Compose `.env`, with the existing Compose defaults. Use URL-safe database credentials for this URL. Existing volume credentials do not change when these variables change. `DATABASE_URL` in `backend/.env` is overridden inside Compose so the container connects to `postgres:5432`.

Backend application and migration code, frontend source, public assets, and Vite config are bind mounted for development reload. Rebuild after changing dependency manifests. The installed dependencies stay inside the images. The frontend image uses `npm install` because the current lockfile is missing platform-specific entries required by `npm ci`; dependency resolution is therefore not strictly reproducible until the lockfile is repaired.

## Operations

```bash
docker compose ps
docker compose logs -f backend frontend postgres
docker compose down
```

`down` preserves the existing named PostgreSQL volume. Do not use `down -v` if the data must be retained.

## Troubleshooting

- Check `docker compose ps` and service logs if startup fails. Ensure Docker is running and ports 5173, 8001, and 5434 are free.
- If the database is unhealthy or authentication fails, check that the configured PostgreSQL credentials match those used when the existing volume was initialized.
- If the backend exits, check its logs for a migration or configuration error. Confirm `backend/.env` exists and the JWT secret is set.
- If API requests fail in the browser, check backend health at [http://localhost:8001/health](http://localhost:8001/health) and proxy health at [http://localhost:5173/health](http://localhost:5173/health). Keep `VITE_API_BASE_URL` empty for same-origin requests.
- Real PDF extraction additionally requires a working DeepSeek API key. No credentials belong in frontend variables or images.

Orders are created by PDF upload. If extraction needs review, save it for human review and return later, or correct the fields immediately and resubmit with the original PDF. Saved reviews do not retain the PDF. Existing orders can still be edited or deleted.

See [backend/README.md](backend/README.md) and [frontend/README.md](frontend/README.md) for application and test details.
