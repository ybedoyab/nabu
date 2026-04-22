import json

from data.src.adapters.outbound.json_mock_search_provider import JsonMockSearchProvider


def test_search_returns_ranked_records(tmp_path):
    payload = [
        {"corpus_id": "1", "source": "arxiv", "external_id": "1", "title": "attention methods", "landing_url": "u1"},
        {"corpus_id": "2", "source": "arxiv", "external_id": "2", "title": "unrelated", "landing_url": "u2"},
    ]
    fp = tmp_path / "mock.json"
    fp.write_text(json.dumps(payload), encoding="utf-8")
    provider = JsonMockSearchProvider("arxiv", str(fp))
    result = provider.search("attention", 5)
    assert len(result) == 1
    assert result[0].title == "attention methods"


def test_search_handles_missing_or_invalid_files(tmp_path):
    provider = JsonMockSearchProvider("arxiv", str(tmp_path / "missing.json"))
    assert provider.search("q", 5) == []

    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"not": "list"}), encoding="utf-8")
    provider2 = JsonMockSearchProvider("arxiv", str(bad))
    assert provider2.search("q", 5) == []
