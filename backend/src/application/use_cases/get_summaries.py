from typing import Any, Dict, List

from ...ports.research_assistant_port import ResearchAssistantPort


class GetSummariesUseCase:
    def __init__(self, assistant: ResearchAssistantPort):
        self.assistant = assistant

    def execute(
        self, selected_articles: List[Dict[str, Any]], research_query: str
    ) -> Dict[str, Any]:
        if not selected_articles:
            raise ValueError("At least one article must be selected")
        if not research_query.strip():
            raise ValueError("Research query cannot be empty")
        return self.assistant.get_summaries_and_questions(selected_articles, research_query)
