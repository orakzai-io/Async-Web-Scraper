import os
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from dotenv import load_dotenv
import time

import api
from app.database import engine
from app.models import Base

# Load environment variables early
load_dotenv()  # Removed override=True - don't override existing env vars

# Configuration from environment
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "7860"))
RELOAD = os.getenv("RELOAD", "true").lower() == "true"
LOG = os.getenv("LOG_LEVEL", "DEBUG")
ALLOWED_ORIGINS_ENV = os.getenv("ALLOWED_ORIGINS", "")

# Logging setup
logger.remove()

# Simplified plain-text format
LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <7}</level> | "
    "<level>{message}</level>"
)

# Configure with defaults for extra fields to prevent KeyError
logger.configure(
    extra={"context": "SYS", "url": "GLOBAL"},
    patcher=lambda record: (
        record["extra"].setdefault("context", "SYS")
        or record["extra"].setdefault("url", "GLOBAL")
    ),
)
logger.add(sys.stderr, format=LOG_FORMAT, colorize=True, level=LOG)

log = logger.bind(context="STARTUP")


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup logging (Moved from module level to avoid duplication)
    if not ALLOWED_ORIGINS_ENV:
        log.warning(
            "CORS: Using default origins (localhost/127.0.0.1) - set ALLOWED_ORIGINS for production"
        )
    else:
        log.info(
            f"CORS: Configured with {len(ALLOWED_ORIGINS_ENV.split(','))} custom origins"
        )

    log.info("Starting up Web Scraper API...")
    try:
        Base.metadata.create_all(bind=engine)
        log.info("Database: Tables verified/created")
    except Exception as e:
        log.error(f"Database: Initialization failed: {e}")
        raise

    yield

    # Shutdown
    log.info("Shutting down Web Scraper API...")
    engine.dispose()
    log.info("Database connections closed")


# FastAPI app initialization
app = FastAPI(
    title="Web Scraper API",
    description="API for triggering and polling asynchronous web scraping jobs.",
    version="1.0.0",
    lifespan=lifespan,
)


# Middleware for logging requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    # cleaner, standardized visit log
    log.info(
        f"VISIT: {getattr(request.client, 'host', 'unknown')} - "
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {duration:.4f}s"
    )
    return response


# CORS configuration
if not ALLOWED_ORIGINS_ENV:
    origins = [
        "http://localhost",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
    ]
else:
    origins = [origin.strip() for origin in ALLOWED_ORIGINS_ENV.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API routes
app.include_router(api.router)


# Serve static files from the Frontend/dist directory
# Ensure 'dist' folder is copied to the backend during build
frontend_path = os.path.join(os.path.dirname(__file__), "dist")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")
else:
    log.warning(f"Frontend: 'dist' folder not found at {frontend_path}. Static file serving disabled.")


# Run server
if __name__ == "__main__":
    log.info(f"Starting server on {HOST}:{PORT}")
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=RELOAD,
        log_config=None,  # Disabled uvicorn's default logging since we use loguru
    )
