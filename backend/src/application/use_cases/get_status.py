from typing import Any, Dict

from ...ports.research_assistant_port import ResearchAssistantPort


class GetStatusUseCase:
    def __init__(self, assistant: ResearchAssistantPort):
        self.assistant = assistant

    def execute(self) -> Dict[str, Any]:
        return self.assistant.get_status()
