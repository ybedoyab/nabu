from dataclasses import dataclass

from fastapi.testclient import TestClient

import data.api as data_api


@dataclass
class _Result:
    status: str = "ok"
    session_id: str = "sess_x"
    query: str = "q"
    ttl_seconds: int = 3600
    expires_at: str = "2026-01-01T00:00:00Z"
    sources_queried: list = None
    limits_applied: dict = None
    stats: dict = None
    articles: list = None
    errors_by_source: dict = None

    def __post_init__(self):
        self.sources_queried = self.sources_queried or ["arxiv"]
        self.limits_applied = self.limits_applied or {"arxiv": 1, "scholar": 0}
        self.stats = self.stats or {"merged_unique": 0}
        self.articles = self.articles or []
        self.errors_by_source = self.errors_by_source or {}


class _FetchUC:
    def execute(self, query, limits):
        return _Result(query=query)


class _Container:
    fetch_session_use_case = _FetchUC()


def test_health_endpoint():
    client = TestClient(data_api.app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["service"] == "data-api"


def test_session_fetch_success(monkeypatch):
    monkeypatch.setattr(data_api, "container", _Container())
    client = TestClient(data_api.app)
    r = client.post("/api/v1/session/fetch", json={"query": "abc"})
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_session_fetch_bad_request():
    client = TestClient(data_api.app)
    r = client.post("/api/v1/session/fetch", json={"query": " "})
    assert r.status_code == 400


def test_query_images_bad_request():
    client = TestClient(data_api.app)
    r = client.post("/api/v1/stats/query-images", json={"research_query": " "})
    assert r.status_code == 400
