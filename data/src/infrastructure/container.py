from pathlib import Path

from ..adapters.outbound.json_mock_search_provider import JsonMockSearchProvider
from ..application.use_cases.fetch_session import FetchSessionUseCase


class Container:
    def __init__(self):
        base = Path(__file__).resolve().parents[2]
        providers = [
            JsonMockSearchProvider(
                source_name="arxiv",
                json_path=str(base / "webscraping" / "arxiv" / "mock_results.json"),
            ),
            JsonMockSearchProvider(
                source_name="scholar",
                json_path=str(base / "webscraping" / "google_scholar" / "mock_results.json"),
            ),
        ]
        self.fetch_session_use_case = FetchSessionUseCase(providers=providers, ttl_seconds=3600)


def build_container() -> Container:
    return Container()
