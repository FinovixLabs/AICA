from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import time

from app.core.config import get_settings
from app.core.db import get_db
from app.api.routes import auth, clients, documents, filing, chat, notices, dashboard, recon

settings = get_settings()
settings.upload_root_path.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="AICA API", version="0.1.0", docs_url="/api/docs", redoc_url="/api/redoc")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(clients.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(filing.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(notices.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(recon.router, prefix="/api")

_start_time = time.time()

@app.get("/ping")
async def ping():
    return "pong"

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "uptime_seconds": round(time.time() - _start_time),
        "version": "0.1.0",
        "storage_writable": os.access(settings.upload_root_path, os.W_OK),
    }


@app.get("/api/ready")
def readiness(db=Depends(get_db)):
    if not os.access(settings.upload_root_path, os.W_OK):
        raise HTTPException(status_code=503, detail="Persistent upload storage is not writable")
    cur = db.cursor()
    cur.execute(
        "SELECT to_regclass(%s), to_regclass(%s), to_regclass(%s), "
        "to_regclass(%s), to_regclass(%s)",
        (
            "public.cas",
            "public.clients",
            "public.documents",
            "recon.runs",
            "recon.results",
        ),
    )
    if any(item is None for item in cur.fetchone()):
        raise HTTPException(status_code=503, detail="Required database migrations are missing")
    return {"status": "ready"}

# Serve React build in production
FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")

if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API route not found")
        index = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.exists(index):
            return FileResponse(index)
        return {"error": "Frontend not built"}
