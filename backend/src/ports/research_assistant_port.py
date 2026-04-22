from typing import Any, Dict, List, Optional, Protocol


class ResearchAssistantPort(Protocol):
    def initialize(self) -> bool:
        ...

    def get_status(self) -> Dict[str, Any]:
        ...

    def get_articles_list(self, limit: int = 10) -> List[Dict[str, Any]]:
        ...

    def get_recommendations(self, research_query: str, top_k: int = 5) -> Dict[str, Any]:
        ...

    def get_summaries_and_questions(
        self, selected_articles: List[Dict[str, Any]], research_query: str
    ) -> Dict[str, Any]:
        ...

    def chat_with_articles(
        self,
        user_question: str,
        selected_articles: List[Dict[str, Any]],
        research_query: str,
        chat_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        ...
