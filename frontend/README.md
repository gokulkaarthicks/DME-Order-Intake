# DME Order Intake Frontend

React + TypeScript + Vite UI for DME employee order intake.

## Setup

```bash
cd frontend
npm install
cp .env.example .env
```

## Development

Start the FastAPI backend on port 8001, then:

```bash
npm run dev
```

Vite proxies `/api` and `/health` to `http://127.0.0.1:8001`.

## Scripts

```bash
npm run typecheck
npm run test
npm run build
```

## Notes

- JWT access tokens are stored in `sessionStorage` for the browser session only.
- PDF upload uses `POST /api/orders/upload`. When the response status is `created`, the order is already saved. When status is `needs_review`, the UI opens a correction form and saves through `POST /api/orders`.
- DeepSeek credentials stay on the backend. The frontend never receives API keys.
