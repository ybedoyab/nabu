from data.src.application.use_cases.fetch_session import FetchSessionUseCase
from data.src.domain.entities import ArticleRecord


class Provider:
    def __init__(self, source_name, records=None, fail=False):
        self.source_name = source_name
        self._records = records or []
        self._fail = fail

    def search(self, query, limit):
        if self._fail:
            raise RuntimeError("boom")
        return self._records[:limit]


def _article(source, external_id, landing_url):
    return ArticleRecord(
        corpus_id=f"{source}:{external_id}",
        source=source,
        external_id=external_id,
        title=f"{source}-{external_id}",
        landing_url=landing_url,
    )


def test_execute_ok_and_deduplicate():
    a1 = _article("arxiv", "1", "https://x/1")
    s1_dup = _article("scholar", "x", "https://x/1")
    use_case = FetchSessionUseCase(
        providers=[Provider("arxiv", [a1]), Provider("scholar", [s1_dup])],
        ttl_seconds=3600,
    )
    result = use_case.execute("query", {"arxiv": 10, "scholar": 10})
    assert result.status == "ok"
    assert result.stats["merged_unique"] == 1
    assert result.stats["duplicates_removed"] == 1


def test_execute_partial_when_provider_fails():
    a1 = _article("arxiv", "1", "https://x/1")
    use_case = FetchSessionUseCase(
        providers=[Provider("arxiv", [a1]), Provider("scholar", fail=True)],
    )
    result = use_case.execute("query", {"arxiv": 1, "scholar": 1})
    assert result.status == "partial"
    assert "scholar" in result.errors_by_source


def test_execute_skips_zero_limits():
    use_case = FetchSessionUseCase(providers=[Provider("arxiv", [_article("arxiv", "1", "u")])])
    result = use_case.execute("query", {"arxiv": 0})
    assert result.stats["merged_unique"] == 0
