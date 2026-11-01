"""
CareerPilot AI - FastAPI application entry point.

Run (dev):   uvicorn app.main:app --reload --port 8000
API docs:    http://localhost:8000/docs   (generated automatically by FastAPI)
"""
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.config import settings
from app.db import SessionLocal
from app.routers import (assistant, auth, companies, dashboard, interviews, plan, privacy, profile, progress, questions,
                         resume, skills, tests)
from app.services import llm

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("careerpilot")
VERSION = "2.0.0"


def init_db() -> None:
    """Apply Alembic migrations (creates tables on first run), then load reference content."""
    from alembic import command
    from alembic.config import Config

    from app.services.seed import seed_all

    backend = Path(__file__).resolve().parent.parent
    cfg = Config(str(backend / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend / "alembic"))
    command.upgrade(cfg, "head")
    with SessionLocal() as db:
        log.info("Seed: %s", seed_all(db))


@asynccontextmanager
async def lifespan(_: FastAPI):
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    init_db()
    ai = llm.status()
    log.info("CareerPilot AI %s ready (%s). AI: %s", VERSION, settings.environment,
             f"{ai['provider']} / {ai['model']}" if ai["configured"] else "not configured (rule-based engines, labelled in the UI)")
    yield


app = FastAPI(title="CareerPilot AI API", version=VERSION, lifespan=lifespan,
              description="Placement preparation platform: resume -> skills -> roles -> company -> plan -> practice -> interview.")
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
                   allow_credentials=True, allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
                   allow_headers=["Content-Type", "Authorization", "X-Requested-With"])


@app.middleware("http")
async def security_and_logging(request: Request, call_next):
    started = time.monotonic()
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    if settings.is_production:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
    if request.url.path.startswith("/api/"):
        response.headers.setdefault("Cache-Control", "no-store")
        ms = (time.monotonic() - started) * 1000
        log.info("%s %s -> %s (%.0f ms)", request.method, request.url.path, response.status_code, ms)
    return response


for r in (auth, profile, resume, skills, companies, plan, questions, tests, interviews, progress, dashboard, assistant, privacy):
    app.include_router(r.router)


@app.get("/api/health", tags=["system"])
def health():
    """For uptime checks and Render/Railway health checks: also verifies the database."""
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return {"status": "ok", "version": VERSION, "database": "ok"}
    except Exception as exc:  # pragma: no cover
        log.error("Health check failed: %s", exc)
        return JSONResponse(status_code=503, content={"status": "error", "database": "unreachable"})


@app.get("/api/meta", tags=["system"])
def meta():
    """Tells the UI whether AI is configured, so every feature can label its engine honestly."""
    ai = llm.status()
    return {"ai_configured": ai["configured"], "ai_provider": ai["provider"] if ai["configured"] else None,
            "ai_model": ai["model"], "github_api": settings.github_enabled, "max_upload_mb": settings.max_upload_mb,
            "code_runner": {"language": "python", "timeout_seconds": settings.code_timeout_seconds}, "version": VERSION}


@app.exception_handler(Exception)
async def unhandled(_: Request, exc: Exception):
    log.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Something went wrong on our side. Please try again."})


# Serve the exported Next.js frontend (single-port deployment), if it has been built.
_front = Path(settings.frontend_dir)
if _front.is_dir():
    app.mount("/_next", StaticFiles(directory=_front / "_next"), name="next-assets")
    _front_resolved = _front.resolve()

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str):
        if path.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "Not found."})
        for candidate in (_front / path, _front / path / "index.html", _front / f"{path}.html"):
            try:
                resolved = candidate.resolve()
            except OSError:
                continue
            if resolved.is_file() and (resolved == _front_resolved or _front_resolved in resolved.parents):
                return FileResponse(resolved)
        if (_front / "404.html").exists():
            return FileResponse(_front / "404.html", status_code=404)
        return JSONResponse(status_code=404, content={"detail": "Not found."})
