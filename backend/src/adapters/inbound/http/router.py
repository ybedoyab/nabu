import logging
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
        try:
            status = container.get_status_use_case.execute()
            if status["articles_available"] == 0:
                raise HTTPException(
                    status_code=503,
                    detail="No analyzed articles available. Please run analysis first.",
                )
            response = container.get_recommendations_use_case.execute(
                request.research_query, request.top_k
            )
            return RecommendationsResponse(**response)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Error getting recommendations: %s", exc)
            raise HTTPException(status_code=500, detail=f"Error getting recommendations: {exc}")

    @router.post(f"{api_prefix}/research/summaries", response_model=SummariesResponse)
    async def get_summaries(request: ArticleSelectionRequest):
        try:
            response = container.get_summaries_use_case.execute(
                request.selected_articles, request.research_query
            )
            return SummariesResponse(**response)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:
            logger.error("Error generating summaries: %s", exc)
            raise HTTPException(status_code=500, detail=f"Error generating summaries: {exc}")

    @router.post(f"{api_prefix}/research/chat", response_model=ChatResponse)
    async def chat_with_articles(request: ChatRequest):
        try:
            response = container.chat_with_articles_use_case.execute(
                user_question=request.user_question,
                selected_articles=request.selected_articles,
                research_query=request.research_query,
                chat_history=request.chat_history,
            )
            return ChatResponse(**response)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:
            logger.error("Error processing chat: %s", exc)
            raise HTTPException(status_code=500, detail=f"Error processing chat: {exc}")

    return router
