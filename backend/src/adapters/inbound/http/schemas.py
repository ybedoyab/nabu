from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ResearchQueryRequest(BaseModel):
    research_query: str = Field(..., description="Research query or topic", min_length=1, max_length=500)
    top_k: int = Field(default=5, description="Number of recommendations to return", ge=1, le=20)


class ArticleSelectionRequest(BaseModel):
    selected_articles: List[Dict[str, Any]] = Field(..., description="Selected article recommendations")
    research_query: str = Field(..., description="Original research query", min_length=1)


class ChatRequest(BaseModel):
    user_question: str = Field(..., description="User's question", min_length=1, max_length=1000)
    selected_articles: List[Dict[str, Any]] = Field(..., description="Selected articles for context")
    research_query: str = Field(..., description="Original research query")
    chat_history: Optional[List[Dict[str, Any]]] = Field(default=[], description="Previous chat messages")


class ArticleRecommendation(BaseModel):
    id: str
    title: str
    relevance_score: float = Field(..., ge=0, le=10)
    relevance_reasons: List[str]
    research_applications: List[str]
    url: str
    organisms: List[str] = Field(default=[])
    key_concepts: List[str] = Field(default=[])
    selected: bool = False


class RecommendationsResponse(BaseModel):
    status: str = "success"
    step: str = "recommendations"
    research_query: str
    recommendations: List[ArticleRecommendation]
    metadata: Dict[str, Any]


class ArticleSummary(BaseModel):
    article_id: str
    title: str
    summary: str
    url: str
    relevance_score: float
    organisms: List[str] = Field(default=[])
    key_concepts: List[str] = Field(default=[])


class SuggestedQuestion(BaseModel):
    id: str
    question: str
    type: str
    focus: str
    article_id: Optional[str] = None
    article_title: Optional[str] = None


class ResearchInsights(BaseModel):
    overall_insights: str
    articles_analyzed: int
    research_query: str


class SummariesResponse(BaseModel):
    status: str = "success"
    step: str = "summaries_and_questions"
    research_query: str
    article_summaries: List[ArticleSummary]
    suggested_questions: List[SuggestedQuestion]
    research_insights: ResearchInsights
    metadata: Dict[str, Any]


class ChatMessage(BaseModel):
    id: str
    role: str
    content: str
    timestamp: float
    follow_up_questions: Optional[List[Dict[str, Any]]] = Field(default=[])


class FollowUpQuestion(BaseModel):
    id: str
    question: str
    type: str


class ChatResponse(BaseModel):
    status: str = "success"
    step: str = "chat"
    research_query: str
    chat_history: List[ChatMessage]
    follow_up_questions: List[FollowUpQuestion] = Field(default=[])
    metadata: Dict[str, Any]


class ErrorResponse(BaseModel):
    status: str = "error"
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())


class StatusResponse(BaseModel):
    status: str
    articles_available: int
    openai_configured: bool
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())


class HealthResponse(BaseModel):
    status: str = "healthy"
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())
