"""DocForge FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.database import get_database, close_database
from app.api.routes import health, generate, documents, auth, conversations, document_briefs, knowledge


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup: Initialize database
    await get_database()
    yield
    # Shutdown: Close database
    await close_database()


# Create FastAPI app
settings = get_settings()
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS middleware - allow credentials for cookies
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,  # Important for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(generate.router, prefix="/api", tags=["generation"])
app.include_router(documents.router, prefix="/api", tags=["documents"])
app.include_router(conversations.router, prefix="/api", tags=["conversations"])
app.include_router(document_briefs.router, prefix="/api", tags=["document-briefs"])
app.include_router(knowledge.router, prefix="/api", tags=["knowledge-base"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }
