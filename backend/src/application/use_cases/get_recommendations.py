from typing import Any, Dict

from ...ports.research_assistant_port import ResearchAssistantPort


class GetRecommendationsUseCase:
    def __init__(self, assistant: ResearchAssistantPort):
        self.assistant = assistant

    def execute(self, research_query: str, top_k: int = 5) -> Dict[str, Any]:
        if not research_query.strip():
            raise ValueError("Research query cannot be empty")
        return self.assistant.get_recommendations(research_query, top_k)
