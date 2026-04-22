"""Backward-compatible schema exports (moved to hexagonal adapters)."""

from src.adapters.inbound.http.schemas import (  # noqa: F401
    ArticleRecommendation,
    ArticleSelectionRequest,
    ArticleSummary,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    FollowUpQuestion,
    HealthResponse,
    RecommendationsResponse,
    ResearchInsights,
    ResearchQueryRequest,
    StatusResponse,
    SuggestedQuestion,
    SummariesResponse,
)
