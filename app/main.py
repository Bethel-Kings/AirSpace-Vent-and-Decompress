from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from sqlalchemy import inspect, text
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.core.logging import logger
from app.core.rate_limit import limiter
from app.api.v1 import api_router
from app.db.session import engine, Base, SessionLocal
import app.models  # ensure models are registered with Base metadata


def _ensure_runtime_schema() -> None:
    """Create missing tables and additive columns for local/dev SQLite."""
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if "users" in tables:
        columns = {col["name"] for col in inspector.get_columns("users")}
        if "token_version" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN token_version INTEGER NOT NULL DEFAULT 0"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database schema...")
    _ensure_runtime_schema()
    logger.info("Database schema initialized successfully.")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AirSpace — private emotional decompression: Air It Out, Decompress & Reframe, Track Your Reset.",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please wait a moment and try again."},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


def _health_payload():
    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health", tags=["Health"])
def health():
    return _health_payload()


@app.get("/healthz", tags=["Health"])
def healthz():
    return _health_payload()


@app.get("/ready", tags=["Health"])
def ready():
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        logger.error("Readiness check failed")
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    finally:
        db.close()


BASE_DIR = Path(__file__).resolve().parent
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", response_class=HTMLResponse, tags=["Web"])
def serve_index():
    index_file = BASE_DIR / "static" / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<h1>AirSpace API is running. Static frontend not yet compiled.</h1>")
