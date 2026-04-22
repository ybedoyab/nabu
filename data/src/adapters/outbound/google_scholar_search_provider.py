from typing import Any, List

from ...domain.entities import ArticleRecord, Author


class GoogleScholarSearchProvider:
    """
    Search Provider Adapter for Google Scholar via SerpAPI.
    Implements the SearchProviderPort protocol and uses the Singleton pattern for the SerpAPI client.
    """
    source_name = "scholar"
    _instance = None
    _scraper = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(GoogleScholarSearchProvider, cls).__new__(cls)

            # Defer hard failures to search() so Data API can still boot
            # and return partial responses when Scholar is unavailable.
            cls._instance._scraper = None

        return cls._instance

    def _get_scraper(self) -> Any:
        if self._scraper is None:
            try:
                from data.webscraping.google_scholar.raw.scraper import GoogleScholarScraper
            except Exception as exc:
                raise RuntimeError(f"Google Scholar scraper unavailable: {exc}") from exc
            self._scraper = GoogleScholarScraper()
        return self._scraper

    @staticmethod
    def _to_article(record: dict) -> ArticleRecord:
        external_id = (record.get("external_id") or "").strip()
        authors = [
            Author(
                name=(a.get("name") or "").strip(),
                affiliation=a.get("affiliation"),
            )
            for a in (record.get("authors") or [])
            if (a.get("name") or "").strip()
        ]

        return ArticleRecord(
            corpus_id=f"sha256:scholar:{external_id}",
            source="scholar",
            external_id=external_id,
            title=(record.get("title") or "").strip(),
            abstract=(record.get("abstract") or "").strip(),
            authors=authors,
            published_at=record.get("published_at"),
            updated_at=record.get("updated_at"),
            landing_url=(record.get("landing_url") or "").strip(),
            pdf_url=record.get("pdf_url"),
            categories=record.get("categories") or [],
            keywords=record.get("keywords") or [],
            venue=record.get("venue"),
            citation_count=record.get("citation_count"),
            snippet_is_partial=bool(record.get("snippet_is_partial")),
            authors_incomplete=bool(record.get("authors_incomplete")),
            fetched_at=record.get("fetched_at") or "",
        )

    def search(self, query: str, limit: int) -> List[ArticleRecord]:
        limit = max(1, min(limit, 20))
        scraper = self._get_scraper()
        normalized = scraper.fetch_data(query=query, max_results=limit)
        return [self._to_article(record) for record in normalized if record.get("external_id")]
