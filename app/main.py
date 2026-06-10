"""
FastAPI application entry point.
Initializes database, configures routes, and exposes health check.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.base import init_db
from app.api.jobs import router as jobs_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI-Powered Transaction Processing Pipeline",
    description="Backend system for processing transaction CSVs with AI-powered analysis",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(jobs_router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "transaction-processing-api"
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "AI-Powered Transaction Processing Pipeline API",
        "version": "1.0.0",
        "docs": "/docs"
    }
