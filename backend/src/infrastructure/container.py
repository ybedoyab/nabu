from dataclasses import dataclass

from ..adapters.outbound.ai_service_adapter import AIServiceAdapter
from ..application.use_cases.chat_with_articles import ChatWithArticlesUseCase
from ..application.use_cases.get_articles import GetArticlesUseCase
from ..application.use_cases.get_recommendations import GetRecommendationsUseCase
from ..application.use_cases.get_status import GetStatusUseCase
from ..application.use_cases.get_summaries import GetSummariesUseCase


@dataclass
class Container:
    assistant_adapter: AIServiceAdapter
    get_status_use_case: GetStatusUseCase
    get_articles_use_case: GetArticlesUseCase
    get_recommendations_use_case: GetRecommendationsUseCase
    get_summaries_use_case: GetSummariesUseCase
    chat_with_articles_use_case: ChatWithArticlesUseCase


def build_container() -> Container:
    assistant_adapter = AIServiceAdapter()
    return Container(
        assistant_adapter=assistant_adapter,
        get_status_use_case=GetStatusUseCase(assistant_adapter),
        get_articles_use_case=GetArticlesUseCase(assistant_adapter),
        get_recommendations_use_case=GetRecommendationsUseCase(assistant_adapter),
        get_summaries_use_case=GetSummariesUseCase(assistant_adapter),
        chat_with_articles_use_case=ChatWithArticlesUseCase(assistant_adapter),
    )
