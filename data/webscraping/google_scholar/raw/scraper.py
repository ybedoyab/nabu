import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import serpapi

from ...common.logger import setup_scraper_logger
from ..types import OrganicResult
from dotenv import load_dotenv

class GoogleScholarScraper:
    """
    Singleton class that encapsulates the SerpAPI Google Scholar client and fetching logic.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(GoogleScholarScraper, cls).__new__(cls)

            api_key = os.environ.get("SERPAPI_API_KEY")
            if not api_key:
                raise RuntimeError("SERPAPI_API_KEY environment variable is not set.")
            cls._instance.client = serpapi.Client(api_key=api_key)

            log_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "..", "logs"
            )
            cls._instance.logger = setup_scraper_logger(
                "google_scholar_scraper", log_dir
            )
            cls._instance.logger.info("GoogleScholarScraper Singleton instantiated.")

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

    def fetch_data(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Fetches and normalizes data from Google Scholar (via SerpAPI) based on a query.
        Returns a list of standardized dictionaries ready for consumption.
        """
        self.logger.info(
            f"Fetching Google Scholar data for query: '{query}' (max_results={max_results})"
        )
        fetched_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        results: List[Dict[str, Any]] = []

        try:
            response = self.client.search(
                {
                    "engine": "google_scholar",
                    "q": query,
                    "hl": "en",
                    "num": max_results,
                }
            )
            organic_results: List[OrganicResult] = (
                response.get("organic_results", []) or []
            )

            for item in organic_results:
                results.append(self._normalize(item, fetched_timestamp))

            self.logger.info(
                f"Successfully retrieved and normalized {len(results)} results."
            )

        except Exception as e:
            self.logger.error(f"Error fetching Google Scholar data: {e}")

        return results

    def _normalize(self, item: OrganicResult, fetched_timestamp: str) -> Dict[str, Any]:
        external_id = item["result_id"]
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
            {"name": a.get("name", ""), "affiliation": None}
            for a in publication_info.get("authors", []) or []
        ]
        abstract = (item.get("snippet") or "").replace("…", "...").strip()

        return {
            "corpus_id": f"sha256:google_scholar:{external_id}",
            "source": "google_scholar",
            "external_id": external_id,
            "title": (item.get("title") or "").strip(),
            "abstract": abstract,
            "authors": authors,
            "published_at": published_at,
            "updated_at": None,
            "landing_url": item.get("link"),
            "pdf_url": pdf_url,
            "categories": [],
            "keywords": [],
            "venue": venue,
            "citation_count": citation_count,
            "snippet_is_partial": True,
            "authors_incomplete": False,
            "fetched_at": fetched_timestamp,
        }


if __name__ == "__main__":
    load_dotenv()
    scraper1 = GoogleScholarScraper()
    scraper2 = GoogleScholarScraper()

    scraper1.logger.info(f"Scraper 1 memory ID: {id(scraper1)}")
    scraper1.logger.info(f"Scraper 2 memory ID: {id(scraper2)}")
    assert id(scraper1) == id(scraper2), "Singleton pattern failed!"

    sample_query = "machine learning"
    data = scraper1.fetch_data(query=sample_query, max_results=2)

    output_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "raw",
        "sample_output.json",
    )
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    scraper1.logger.info(f"Test script completed. Output saved to {output_file}.")
