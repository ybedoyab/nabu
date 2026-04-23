import os
import re
from datetime import datetime, timezone
from typing import Callable, List, Optional, Tuple
from urllib.parse import urlparse

import serpapi

from ...domain.entities import ArticleRecord, Author
from ...infrastructure.logger import setup_scraper_logger
from ...scrapers import nih, nature, aaai, researchgate, springer, arxiv, ieee
from ..types import OrganicResult

SCRAPER_BY_DOMAIN: List[Tuple[str, Callable[[str], str]]] = [
    ("pmc.ncbi.nlm.nih.gov", nih.get_abstract),
    ("researchgate.net", researchgate.get_abstract),
    ("link.springer.com", springer.get_abstract),
    ("nature.com", nature.get_abstract),
    ("ojs.aaai.org", aaai.get_abstract),
    ("arxiv.org", arxiv.get_abstract),
    ("ieeexplore.ieee.org", ieee.get_abstract),
]


class GoogleScholarSearchProvider:
    """
    Search Provider Adapter for Google Scholar via SerpAPI.
    Implements the SearchProviderPort protocol and uses the Singleton pattern for the SerpAPI client.
    """
    source_name = "scholar"
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(GoogleScholarSearchProvider, cls).__new__(cls)

            api_key = os.environ.get("SERPAPI_API_KEY")
            if not api_key:
                raise RuntimeError("SERPAPI_API_KEY environment variable is not set.")
            cls._instance.client = serpapi.Client(api_key=api_key)

            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            log_dir = os.path.join(base_dir, "webscraping", "logs", "scholar")
            cls._instance.logger = setup_scraper_logger("scholar_provider", log_dir)
            cls._instance.logger.info("GoogleScholarSearchProvider instantiated.")

        return cls._instance

    @staticmethod
    def _parse_venue_and_year(summary: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse `publication_info.summary` of the form
            '<authors abbrev> - <venue>, <year> - <domain>' or
            '<authors abbrev> - <year> - <domain>'.
        Returns (venue, published_at_iso_or_None).
        """
        if not summary:
            return None, None

        parts = [p.strip() for p in summary.split(" - ")]
        if len(parts) < 2:
            return None, None

        middle = parts[1] if len(parts) >= 3 else ""
        if not middle:
            return None, None

        year_match = re.search(r"(\d{4})\s*$", middle)
        year = year_match.group(1) if year_match else None

        venue = middle
        if year:
            venue = re.sub(r",?\s*" + year + r"\s*$", "", middle).strip()
        venue = venue or None

        published_at = f"{year}-01-01T00:00:00Z" if year else None
        return venue, published_at

    @staticmethod
    def _match_scraper(url: str) -> Optional[Callable[[str], str]]:
        host = (urlparse(url).hostname or "").lower()
        if not host:
            return None
        for domain, fn in SCRAPER_BY_DOMAIN:
            if host == domain or host.endswith("." + domain):
                return fn
        return None

    def _fetch_abstract(self, item: OrganicResult) -> Tuple[str, bool]:
        """
        Pick the first candidate URL (landing link, then HTML/PDF resources) whose
        domain has a dedicated scraper, and return (abstract, is_partial).
        Falls back to (snippet, True) if no scraper matches or all scrapers fail.
        """
        candidates: List[str] = []
        link = item.get("link")
        if link:
            candidates.append(link)
        for resource in item.get("resources") or []:
            resource_link = resource.get("link")
            if resource_link:
                candidates.append(resource_link)

        for url in candidates:
            scraper = self._match_scraper(url)
            if not scraper:
                continue
            try:
                abstract = scraper(url)
                if abstract:
                    return abstract.strip(), False
            except Exception as e:
                self.logger.warning(f"Scraper failed for {url}: {e}")

        snippet = (item.get("snippet") or "").replace("…", "...").strip()
        return snippet, True

    def search(self, query: str, limit: int) -> List[ArticleRecord]:
        """
        Fetches data from Google Scholar (via SerpAPI) based on a query and maps
        it to ArticleRecord entities.
        """
        limit = max(1, min(limit, 20))
        self.logger.info(f"Fetching Google Scholar data for query: '{query}' (limit={limit})")

        records: List[ArticleRecord] = []
        fetched_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        try:
            response = self.client.search(
                {
                    "engine": "google_scholar",
                    "q": f"{query} -site:books.google.com -filetype:pdf",
                    "hl": "en",
                    "num": limit,
                }
            )
            organic_results: List[OrganicResult] = response.get("organic_results", []) or []

            for item in organic_results:
                external_id = item.get("result_id")
                if not external_id:
                    continue

                publication_info = item.get("publication_info", {}) or {}
                inline_links = item.get("inline_links", {}) or {}
                resources = item.get("resources", []) or []

                venue, published_at = self._parse_venue_and_year(
                    publication_info.get("summary", "")
                )
                pdf_url = next(
                    (r["link"] for r in resources if r.get("file_format") == "PDF"),
                    None,
                )
                citation_count = (inline_links.get("cited_by") or {}).get("total")
                authors = [
                    Author(name=a.get("name", ""), affiliation=None)
                    for a in publication_info.get("authors", []) or []
                ]
                abstract, snippet_is_partial = self._fetch_abstract(item)

                records.append(
                    ArticleRecord(
                        corpus_id=f"sha256:scholar:{external_id}",
                        source=self.source_name,
                        external_id=external_id,
                        title=(item.get("title") or "").strip(),
                        abstract=abstract,
                        authors=authors,
                        published_at=published_at,
                        updated_at=None,
                        landing_url=item.get("link") or "",
                        pdf_url=pdf_url,
                        categories=[],
                        keywords=[],
                        venue=venue,
                        citation_count=citation_count,
                        snippet_is_partial=snippet_is_partial,
                        authors_incomplete=False,
                        fetched_at=fetched_timestamp,
                    )
                )

            self.logger.info(
                f"Successfully retrieved and normalized {len(records)} results from Google Scholar."
            )

        except Exception as e:
            self.logger.error(f"Error fetching data from Google Scholar: {e}")

        return records
