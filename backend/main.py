"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from config import settings
from database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    create_db_and_tables()
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # tighten to vercel domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers (uncomment as built) ---
# from routers import books, chapters, topics, study, quiz, progress
# app.include_router(books.router, prefix=settings.API_PREFIX)
# app.include_router(chapters.router, prefix=settings.API_PREFIX)
# app.include_router(topics.router, prefix=settings.API_PREFIX)
# app.include_router(study.router, prefix=settings.API_PREFIX)
# app.include_router(quiz.router, prefix=settings.API_PREFIX)
# app.include_router(progress.router, prefix=settings.API_PREFIX)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "app": settings.APP_NAME}