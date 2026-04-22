from typing import Any, Dict, List

from ...ports.research_assistant_port import ResearchAssistantPort


class GetArticlesUseCase:
    def __init__(self, assistant: ResearchAssistantPort):
        self.assistant = assistant

    def execute(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self.assistant.get_articles_list(limit)
