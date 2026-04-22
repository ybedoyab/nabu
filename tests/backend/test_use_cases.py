import pytest

from backend.src.application.use_cases.chat_with_articles import ChatWithArticlesUseCase
from backend.src.application.use_cases.get_articles import GetArticlesUseCase
from backend.src.application.use_cases.get_recommendations import GetRecommendationsUseCase
from backend.src.application.use_cases.get_status import GetStatusUseCase
from backend.src.application.use_cases.get_summaries import GetSummariesUseCase


class DummyAssistant:
    def initialize(self):
        return True

    def get_status(self):
        return {"service_healthy": True, "articles_available": 2, "openai_configured": True}

    def get_articles_list(self, limit=10):
        return [{"id": "a1"}][:limit]

    def get_recommendations(self, research_query, top_k=5):
        return {"status": "success", "research_query": research_query, "recommendations": [], "metadata": {}}

    def get_summaries_and_questions(self, selected_articles, research_query):
        return {
            "status": "success",
            "step": "summaries_and_questions",
            "research_query": research_query,
            "article_summaries": [],
            "suggested_questions": [],
            "research_insights": {
                "overall_insights": "",
                "articles_analyzed": len(selected_articles),
                "research_query": research_query,
            },
            "metadata": {},
        }

    def chat_with_articles(self, user_question, selected_articles, research_query, chat_history=None):
        return {
            "status": "success",
            "step": "chat",
            "research_query": research_query,
            "chat_history": [],
            "follow_up_questions": [],
            "metadata": {},
        }


def test_get_status_use_case():
    use_case = GetStatusUseCase(DummyAssistant())
    assert use_case.execute()["service_healthy"] is True


def test_get_articles_use_case():
    use_case = GetArticlesUseCase(DummyAssistant())
    assert use_case.execute(limit=1) == [{"id": "a1"}]


def test_get_recommendations_use_case_success():
    use_case = GetRecommendationsUseCase(DummyAssistant())
    result = use_case.execute("transformers", 3)
    assert result["research_query"] == "transformers"


def test_get_recommendations_use_case_empty_query():
    use_case = GetRecommendationsUseCase(DummyAssistant())
    with pytest.raises(ValueError, match="Research query cannot be empty"):
        use_case.execute("   ", 3)


def test_get_summaries_use_case_success():
    use_case = GetSummariesUseCase(DummyAssistant())
    result = use_case.execute([{"id": "a1"}], "topic")
    assert result["status"] == "success"


def test_get_summaries_use_case_empty_articles():
    use_case = GetSummariesUseCase(DummyAssistant())
    with pytest.raises(ValueError, match="At least one article must be selected"):
        use_case.execute([], "topic")


def test_get_summaries_use_case_empty_query():
    use_case = GetSummariesUseCase(DummyAssistant())
    with pytest.raises(ValueError, match="Research query cannot be empty"):
        use_case.execute([{"id": "a1"}], " ")


def test_chat_use_case_success():
    use_case = ChatWithArticlesUseCase(DummyAssistant())
    result = use_case.execute("hello", [{"id": "a1"}], "topic")
    assert result["step"] == "chat"


def test_chat_use_case_empty_question():
    use_case = ChatWithArticlesUseCase(DummyAssistant())
    with pytest.raises(ValueError, match="User question cannot be empty"):
        use_case.execute("  ", [{"id": "a1"}], "topic")


def test_chat_use_case_empty_articles():
    use_case = ChatWithArticlesUseCase(DummyAssistant())
    with pytest.raises(ValueError, match="At least one article must be selected"):
        use_case.execute("hi", [], "topic")
