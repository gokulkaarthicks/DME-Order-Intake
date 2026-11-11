# DME Order Intake Frontend

React + TypeScript + Vite UI for DME employee order intake. Register and sign in with a username and password.

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

Vite proxies `/api` and `/health` to `http://127.0.0.1:8001` locally. Under Compose, `VITE_PROXY_TARGET` directs the proxy to `http://backend:8001`. See the root README for full-stack Docker startup.

## Scripts

```bash
npm run typecheck
npm run test
npm run build
```

## Notes

- JWT access tokens are stored in `sessionStorage` for the browser session only.
- PDF upload uses `POST /api/orders/upload`. When the response status is `created`, the order is already saved. When status is `needs_review`, the UI opens a correction form and resubmits corrected fields and the original PDF to `POST /api/orders/upload` using the short-lived review token.
- DeepSeek credentials stay on the backend. The frontend never receives API keys.

- Unresolved extractions can be saved for human review without filling missing fields. The dashboard lists pending reviews and validated orders. Pending reviews survive logout and can be corrected later.
