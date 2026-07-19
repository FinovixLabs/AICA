# AICA — AI CA Assistant

GST compliance workspace for Indian Chartered Accountants.

## Stack

- **Frontend:** React 18 + Vite + TypeScript + Tailwind CSS
- **Backend:** FastAPI + Uvicorn + psycopg2
- **DB:** Supabase PostgreSQL + pgvector
- **AI:** OpenAI GPT-4o-mini + text-embedding-3-small + BM25 hybrid search
- **Themes:** Light (Option B — forest green) + Dark (Option C — gold/saffron)

## Folder structure

```
aica/
├── frontend/          # React + Vite
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── lib/
│   │   ├── store/
│   │   └── types/
│   └── dist/          # built by npm run build
└── backend/           # FastAPI
    ├── app/
    │   ├── api/routes/
    │   ├── core/
    │   ├── filing/
    │   │   └── gstr1/   # deterministic classifier + JSON builder
    │   ├── models/
    │   └── services/
    └── migrations/
```

## Local dev

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # fill in your keys
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm ci
npm run dev                # runs on :5173, proxies /api to :8000
```

Open `http://localhost:5173`

## Production build

```bash
# Reproducible monolith image: frontend build + FastAPI runtime
docker build -t aica .
docker run --env-file backend/.env.production \
  -p 8000:8000 -v aica-uploads:/data/uploads aica
```

See [`DEPLOYMENT.md`](DEPLOYMENT.md) for the pre-deploy gate, migrations,
persistent uploads, authentication setup, and split-host configuration.

## Deploy to Render (recommended)

**Option 1: Split deploy (Vercel + Render)**
- Frontend → Vercel (`frontend/` folder, `npm run build`, publish `dist/`)
- Backend → Render Web Service (`backend/` folder, `uvicorn app.main:app --host 0.0.0.0 --port $PORT`)
- Set `CORS_ORIGINS=https://your-vercel-app.vercel.app` in Render env vars
- Set `VITE_API_BASE_URL=https://your-backend.render.com` in Vercel env vars (if using split)

**Option 2: Monolith on Render**
- Build command: `pip install -r backend/requirements.txt && npm ci --prefix frontend && npm run build --prefix frontend`
- Start command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## Environment variables (backend/.env)

```
SUPABASE_DATABASE_URL=postgresql://...
SUPABASE_SERVICE_KEY=eyJ...
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_JWT_SECRET=...
OPENAI_API_KEY=sk-...
OPENAI_CHAT_MODEL=gpt-4o-mini
CORS_ORIGINS=http://localhost:5173,https://yourdomain.com
UPLOAD_ROOT=uploads
MAX_UPLOAD_MB=25
```

## GSTR-1 Pipeline

1. CA uploads sales register CSV via Documents page
2. Click "Run GSTR-1 Classification" on Filing page
3. Backend: parses CSV → normalises headers → classifies each row deterministically
   - B2B: GSTIN present on buyer
   - B2CL: inter-state, unregistered, value > ₹2.5L
   - B2CS: intra-state or value ≤ ₹2.5L (summary)
   - EXP: export type flag or POS = 96
   - CDNR/CDNUR: credit/debit notes by buyer GSTIN
   - HSN: auto-accumulated from all rows
4. GSTR-1 JSON built to portal schema
5. CA reviews table-by-table, downloads JSON + CSV
6. CA uploads JSON to GST portal manually (AICA never auto-submits)
