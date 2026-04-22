from typing import Any, Dict, List, Optional

from ...ports.research_assistant_port import ResearchAssistantPort


class ChatWithArticlesUseCase:
    def __init__(self, assistant: ResearchAssistantPort):
        self.assistant = assistant

    def execute(
        self,
        user_question: str,
        selected_articles: List[Dict[str, Any]],
        research_query: str,
        chat_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        if not user_question.strip():
            raise ValueError("User question cannot be empty")
        if not selected_articles:
            raise ValueError("At least one article must be selected")
        return self.assistant.chat_with_articles(
            user_question=user_question,
            selected_articles=selected_articles,
            research_query=research_query,
            chat_history=chat_history or [],
        )
