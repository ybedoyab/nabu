import logging
import time
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from ....infrastructure.container import Container
from .schemas import (
    ArticleSelectionRequest,
    ChatRequest,
    ChatResponse,
    RecommendationsResponse,
    ResearchQueryRequest,
    StatusResponse,
    SummariesResponse,
)


def create_research_router(container: Container, api_prefix: str) -> APIRouter:
    router = APIRouter()
    logger = logging.getLogger(__name__)

    @router.get(f"{api_prefix}/research/status", response_model=StatusResponse)
    async def get_status():
        try:
            status = container.get_status_use_case.execute()
            return StatusResponse(
                status="operational" if status["service_healthy"] else "degraded",
                articles_available=status["articles_available"],
                openai_configured=status["openai_configured"],
            )
        except Exception as exc:
            logger.error("Error getting status: %s", exc)
            raise HTTPException(status_code=500, detail="Error retrieving system status")

    @router.get(f"{api_prefix}/research/articles")
    async def get_articles_list(limit: int = 10):
        try:
            articles = container.get_articles_use_case.execute(limit)
            service_status = container.get_status_use_case.execute()
            return {
                "articles": articles,
                "count": len(articles),
                "total_available": service_status["articles_available"],
            }
        except Exception as exc:
            logger.error("Error getting articles list: %s", exc)
            raise HTTPException(status_code=500, detail="Error retrieving articles list")

    @router.post(f"{api_prefix}/research/recommendations", response_model=RecommendationsResponse)
    async def get_recommendations(request: ResearchQueryRequest):
        started_at = time.perf_counter()
        logger.info(
            "HTTP recommendations request received (query=%r, top_k=%d)",
            request.research_query,
            request.top_k,
        )
        try:
            response = container.get_recommendations_use_case.execute(
                request.research_query, request.top_k
            )
            logger.info(
                "HTTP recommendations request completed (returned=%d, elapsed=%.2fs)",
                len(response.get("recommendations", [])),
                time.perf_counter() - started_at,
            )
            return RecommendationsResponse(**response)
        except ValueError as exc:
            logger.warning(
                "HTTP recommendations validation failed (query=%r): %s",
                request.research_query,
                exc,
            )
            raise HTTPException(status_code=400, detail=str(exc))
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception(
                "HTTP recommendations request failed (query=%r): %s",
                request.research_query,
                exc,
            )
            raise HTTPException(status_code=500, detail=f"Error getting recommendations: {exc}")

    @router.post(f"{api_prefix}/research/summaries", response_model=SummariesResponse)
    async def get_summaries(request: ArticleSelectionRequest):
        started_at = time.perf_counter()
        logger.info(
            "HTTP summaries request received (query=%r, selected_articles=%d)",
            request.research_query,
            len(request.selected_articles),
        )
        try:
            response = container.get_summaries_use_case.execute(
                request.selected_articles, request.research_query
            )
            logger.info(
                "HTTP summaries request completed (summaries=%d, questions=%d, elapsed=%.2fs)",
                len(response.get("article_summaries", [])),
                len(response.get("suggested_questions", [])),
                time.perf_counter() - started_at,
            )
            return SummariesResponse(**response)
        except ValueError as exc:
            logger.warning(
                "HTTP summaries validation failed (query=%r): %s",
                request.research_query,
                exc,
            )
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:
            logger.exception(
                "HTTP summaries request failed (query=%r): %s",
                request.research_query,
                exc,
            )
            raise HTTPException(status_code=500, detail=f"Error generating summaries: {exc}")

    @router.post(f"{api_prefix}/research/chat", response_model=ChatResponse)
    async def chat_with_articles(request: ChatRequest):
        started_at = time.perf_counter()
        logger.info(
            "HTTP chat request received (query=%r, selected_articles=%d, chat_history=%d)",
            request.research_query,
            len(request.selected_articles),
            len(request.chat_history),
        )
        try:
            response = container.chat_with_articles_use_case.execute(
                user_question=request.user_question,
                selected_articles=request.selected_articles,
                research_query=request.research_query,
                chat_history=request.chat_history,
            )
            logger.info(
                "HTTP chat request completed (history_out=%d, follow_ups=%d, elapsed=%.2fs)",
                len(response.get("chat_history", [])),
                len(response.get("follow_up_questions", [])),
                time.perf_counter() - started_at,
            )
            return ChatResponse(**response)
        except ValueError as exc:
            logger.warning(
                "HTTP chat validation failed (query=%r): %s",
                request.research_query,
                exc,
            )
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:
            logger.exception(
                "HTTP chat request failed (query=%r): %s",
                request.research_query,
                exc,
            )
            raise HTTPException(status_code=500, detail=f"Error processing chat: {exc}")

    return router
