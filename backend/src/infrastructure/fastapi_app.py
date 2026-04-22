import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings, validate_settings

from ..adapters.inbound.http.router import create_research_router
from ..adapters.inbound.http.schemas import ErrorResponse, HealthResponse
from .container import build_container


def create_app() -> FastAPI:
    logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
    logger = logging.getLogger(__name__)
    container = build_container()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="AI-powered research assistant for scientific publications",
        version=settings.VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "*",
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
        allow_headers=["*"],
        expose_headers=["Content-Type", "Authorization"],
        max_age=86400,
    )

    @app.middleware("http")
    async def add_cors_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH"
        response.headers["Access-Control-Allow-Headers"] = (
            "Accept, Accept-Language, Content-Language, Content-Type, Authorization, "
            "X-Requested-With, Origin, Access-Control-Request-Method, Access-Control-Request-Headers"
        )
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Max-Age"] = "86400"
        return response

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Global exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error_code="INTERNAL_SERVER_ERROR",
                message="An internal server error occurred",
                details={"error": str(exc)},
            ).dict(),
        )

    @app.on_event("startup")
    async def startup_event():
        logger.info("Starting Nabu AI API...")
        if not validate_settings():
            raise RuntimeError("Invalid configuration")
        if not container.assistant_adapter.initialize():
            raise RuntimeError("Failed to initialize AI service")

    @app.options("/{full_path:path}")
    async def options_handler(full_path: str):
        return JSONResponse(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH",
                "Access-Control-Allow-Headers": (
                    "Accept, Accept-Language, Content-Language, Content-Type, Authorization, "
                    "X-Requested-With, Origin, Access-Control-Request-Method, Access-Control-Request-Headers, "
                    "Access-Control-Allow-Origin, Access-Control-Allow-Methods, Access-Control-Allow-Headers"
                ),
                "Access-Control-Max-Age": "86400",
                "Access-Control-Allow-Credentials": "true",
            },
        )

    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        return HealthResponse()

    @app.get("/cors-test")
    async def cors_test():
        return {
            "message": "CORS is working!",
            "timestamp": time.time(),
            "cors_headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With, Origin",
            },
        }

    @app.get("/")
    async def root():
        return {
            "message": "Nabu AI API",
            "version": settings.VERSION,
            "docs": "/docs",
            "health": "/health",
            "status": f"{settings.API_V1_STR}/research/status",
        }

    app.include_router(create_research_router(container, settings.API_V1_STR))
    return app
