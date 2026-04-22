from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.src.adapters.inbound.http.router import create_research_router


class _UseCase:
    def __init__(self, fn):
        self.execute = fn


class DummyContainer:
    def __init__(self):
        self.get_status_use_case = _UseCase(
            lambda: {"service_healthy": True, "articles_available": 2, "openai_configured": True}
        )
        self.get_articles_use_case = _UseCase(lambda limit=10: [{"id": "a1"}][:limit])
        self.get_recommendations_use_case = _UseCase(
            lambda query, top_k=5: {
                "status": "success",
                "step": "recommendations",
                "research_query": query,
                "recommendations": [],
                "metadata": {},
            }
        )
        self.get_summaries_use_case = _UseCase(
            lambda selected_articles, research_query: {
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
        )
        self.chat_with_articles_use_case = _UseCase(
            lambda user_question, selected_articles, research_query, chat_history=None: {
                "status": "success",
                "step": "chat",
                "research_query": research_query,
                "chat_history": [],
                "follow_up_questions": [],
                "metadata": {},
            }
        )


def _build_client(container=None):
    app = FastAPI()
    app.include_router(create_research_router(container or DummyContainer(), "/api/v1"))
    return TestClient(app)


def test_status_endpoint():
    client = _build_client()
    r = client.get("/api/v1/research/status")
    assert r.status_code == 200
    assert r.json()["status"] == "operational"


def test_articles_endpoint():
    client = _build_client()
    r = client.get("/api/v1/research/articles?limit=1")
    assert r.status_code == 200
    assert r.json()["count"] == 1


def test_recommendations_endpoint_success():
    client = _build_client()
    r = client.post("/api/v1/research/recommendations", json={"research_query": "abc", "top_k": 3})
    assert r.status_code == 200
    assert r.json()["status"] == "success"


def test_summaries_endpoint_success():
    client = _build_client()
    r = client.post(
        "/api/v1/research/summaries",
        json={"selected_articles": [{"id": "a1"}], "research_query": "abc"},
    )
    assert r.status_code == 200
    assert r.json()["step"] == "summaries_and_questions"


def test_chat_endpoint_success():
    client = _build_client()
    r = client.post(
        "/api/v1/research/chat",
        json={
            "user_question": "Hello?",
            "selected_articles": [{"id": "a1"}],
            "research_query": "abc",
            "chat_history": [],
        },
    )
    assert r.status_code == 200
    assert r.json()["step"] == "chat"


def test_recommendations_503_when_no_articles():
    c = DummyContainer()
    c.get_status_use_case = _UseCase(
        lambda: {"service_healthy": True, "articles_available": 0, "openai_configured": True}
    )
    client = _build_client(c)
    r = client.post("/api/v1/research/recommendations", json={"research_query": "abc", "top_k": 3})
    assert r.status_code == 503
