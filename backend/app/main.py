from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.core.logging import setup_logging, logger
from backend.app.db.init_db import init_db
from backend.app.api.health import router as health_router
from backend.app.api.auth import router as auth_router
from backend.app.api.jobs import router as jobs_router
from backend.app.api.segments import router as segments_router
from backend.app.api.uploads import router as uploads_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Initializing Lecture Dubber database and storage...")
    init_db()
    # Ensure storage root exists
    _ = settings.storage_path
    logger.info("Lecture Dubber API startup complete.")
    yield
    logger.info("Lecture Dubber API shutting down...")


app = FastAPI(
    title="Lecture Dubber API",
    version="1.0.0",
    description="Video lecture translation and voice cloning platform API.",
    lifespan=lifespan
)

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers under /api prefix
app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(jobs_router, prefix="/api")
app.include_router(segments_router, prefix="/api")
app.include_router(uploads_router, prefix="/api")
