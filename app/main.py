import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse

from app.core.config import settings
from app.core.logging import logger
from app.api.v1 import api_router
from app.db.session import engine, Base
import app.models  # ensure models are registered with Base metadata


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database tables exist on startup
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully.")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AirSpace — AI-powered emotional decompression platform for private expression, structured decompression, and before/after reset.",
    lifespan=lifespan,
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Health endpoint for Render and monitoring
@app.get("/healthz", tags=["Health"])
def healthz():
    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }

# Mount static files directory
BASE_DIR = Path(__file__).resolve().parent
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# Serve Frontend Views
@app.get("/", response_class=HTMLResponse, tags=["Web"])
def serve_index():
    index_file = BASE_DIR / "static" / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<h1>AirSpace API is running. Static frontend not yet compiled.</h1>")
