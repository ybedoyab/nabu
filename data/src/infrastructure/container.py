from ..adapters.outbound.arxiv_search_provider import ArxivSearchProvider
from ..adapters.outbound.google_scholar_search_provider import GoogleScholarSearchProvider
from ..application.use_cases.fetch_session import FetchSessionUseCase


class Container:
    def __init__(self):
        providers = [
            ArxivSearchProvider(),
            GoogleScholarSearchProvider(),
        ]
        self.fetch_session_use_case = FetchSessionUseCase(providers=providers, ttl_seconds=3600)


def build_container() -> Container:
    return Container()
