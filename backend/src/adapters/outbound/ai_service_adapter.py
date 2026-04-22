from typing import Any, Dict, List, Optional

from ...infrastructure.ai_service import get_ai_service, initialize_ai_service


class AIServiceAdapter:
    """Outbound adapter that bridges the current AI service implementation."""

    def initialize(self) -> bool:
        return initialize_ai_service()

    def get_status(self) -> Dict[str, Any]:
        return get_ai_service().get_status()

    def get_articles_list(self, limit: int = 10) -> List[Dict[str, Any]]:
        return get_ai_service().get_articles_list(limit)

    def get_recommendations(self, research_query: str, top_k: int = 5) -> Dict[str, Any]:
        return get_ai_service().get_recommendations(research_query, top_k)

    def get_summaries_and_questions(
        self, selected_articles: List[Dict[str, Any]], research_query: str
    ) -> Dict[str, Any]:
        return get_ai_service().get_summaries_and_questions(selected_articles, research_query)

    def chat_with_articles(
        self,
        user_question: str,
        selected_articles: List[Dict[str, Any]],
        research_query: str,
        chat_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        return get_ai_service().chat_with_articles(
            user_question=user_question,
            selected_articles=selected_articles,
            research_query=research_query,
            chat_history=chat_history or [],
        )
