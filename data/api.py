from dataclasses import asdict
from typing import List, Optional
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

DATA_DIR = Path(__file__).resolve().parent
if str(DATA_DIR) not in sys.path:
    sys.path.insert(0, str(DATA_DIR))

from src.infrastructure.container import build_container

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from settings import settings as global_settings

app = FastAPI(title="Nabu Data API", version="2.0.0")
container = build_container()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SessionFetchLimits(BaseModel):
    arxiv: int = global_settings.DATA_API_DEFAULT_ARXIV_LIMIT
    scholar: int = global_settings.DATA_API_DEFAULT_SCHOLAR_LIMIT


class SessionFetchRequest(BaseModel):
    query: str
    limits: SessionFetchLimits = SessionFetchLimits()
    locale: str = "es"


class StatsQueryRequest(BaseModel):
    research_query: str
    article_urls: Optional[List[str]] = None


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "data-api"}


@app.post("/api/v1/session/fetch")
def session_fetch(payload: SessionFetchRequest):
    query = (payload.query or "").strip()
    if not query:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "query is required"},
        )
    result = container.fetch_session_use_case.execute(
        query=query,
        limits={"arxiv": payload.limits.arxiv, "scholar": payload.limits.scholar},
    )
    return JSONResponse(content=asdict(result))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8080, reload=True)

