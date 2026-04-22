"""Main entrypoint for backend HTTP service."""

from src.infrastructure.fastapi_app import create_app
from src.infrastructure.config import settings

app = create_app()

if __name__ == "__main__":
    import uvicorn
    
    print("Starting Nabu AI API...")
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
