# Deployment gate

Run these checks before every deployment:

```powershell
& .\.venv\Scripts\python.exe -m pip check
& .\.venv\Scripts\python.exe -m pytest -q backend\tests
npm.cmd ci --prefix frontend
npm.cmd run build --prefix frontend
npm.cmd audit --prefix frontend
git diff --check
git status --short
```

The frontend build includes TypeScript checking. Do not deploy with modified or
untracked application files: Git-based hosts only receive committed files.

## Required production configuration

Copy `backend/.env.example` into the hosting provider's secret/environment
settings. Do not upload a populated `.env` file.

Required values:

- `APP_ENV=production`
- `SUPABASE_DATABASE_URL`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `OPENAI_API_KEY` for AI-backed features
- `CORS_ORIGINS` as a comma-separated list of exact frontend origins
- `UPLOAD_ROOT` as an absolute path on a persistent disk or mounted volume

Production startup rejects wildcard CORS and rejects an unspecified upload
directory. The Docker image defaults `UPLOAD_ROOT` to `/data/uploads`; mount a
persistent volume there.

## Current login behavior

The application retains its original demo login and does not enforce backend
authentication. If the site is exposed publicly, protect it at the hosting or
reverse-proxy layer until an authentication design is selected and implemented.

## Database migrations

Apply these files to the target Supabase project in order before enabling the
reconciliation pages:

1. `backend/migrations/004_create_recon_schema.sql`
2. `backend/migrations/005_add_recon_doc_types.sql` by itself, outside a wrapping transaction
3. `backend/migrations/006_add_ims_inward_action_status.sql`

The destructive uninstall lives at
`backend/migrations/manual/999_drop_recon.sql`, outside the ordered migration
glob. Never execute it during deployment.

## Existing documents

Database rows store paths relative to `UPLOAD_ROOT`. Copy the contents of the
current `backend/uploads/` directory into the production persistent mount while
preserving each client subdirectory. A database-only deployment will list the
documents but cannot preview, reconcile, or download them.

## Deployment shapes

### Monolith container

```bash
docker build -t aica .
docker run --env-file backend/.env.production \
  -p 8000:8000 -v aica-uploads:/data/uploads aica
```

The FastAPI process serves the built React app and API. Use `/api/health` for
liveness and `/api/ready` for the database-migration and persistent-storage
readiness check.

### Split frontend and backend

For the frontend, set the project root to `frontend`, build with `npm ci && npm
run build`, publish `dist`, and set:

```text
VITE_API_BASE_URL=https://api.yourdomain.com
```

For the backend, set the exact frontend origin in `CORS_ORIGINS`. The frontend
uses `BrowserRouter`; keep `frontend/vercel.json` on Vercel or configure the
equivalent `index.html` fallback on another static host.
