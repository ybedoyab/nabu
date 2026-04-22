import arxiv
from pylatexenc.latex2text import LatexNodes2Text
from typing import List, Dict, Any
from datetime import datetime, timezone
import os

from ...domain.entities import ArticleRecord, Author
from ...infrastructure.logger import setup_scraper_logger


class ArxivSearchProvider:
    """
    Search Provider Adapter for arXiv.
    Implements the SearchProviderPort protocol and uses the Singleton pattern for the arxiv client.
    """
    source_name = "arxiv"
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ArxivSearchProvider, cls).__new__(cls)
            # Initialization
            cls._instance.client = arxiv.Client()
            
            # Setup Logger (logs go to data/webscraping/logs/arxiv)
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            log_dir = os.path.join(base_dir, "webscraping", "logs", "arxiv")
            cls._instance.logger = setup_scraper_logger("arxiv_provider", log_dir)
            cls._instance.logger.info("ArxivSearchProvider instantiated.")
            
        return cls._instance

    @staticmethod
    def clean_latex_text(text: str) -> str:
        """
        Cleans LaTeX formatting from strings and returns readable plain text.
        Uses pylatexenc for safe decoding.
        """
        if not text:
            return ""
        text = text.replace('\n', ' ').strip()
        try:
            converter = LatexNodes2Text()
            text = converter.latex_to_text(text)
        except Exception:
            pass
        return ' '.join(text.split())

    def search(self, query: str, limit: int) -> List[ArticleRecord]:
        """
        Fetches data from arXiv based on a query and maps it to ArticleRecord entities.
        """
        # Enforce maximum reasonable limit to not saturate the API
        limit = max(1, min(limit, 100))
        self.logger.info(f"Fetching arXiv data for query: '{query}' (limit={limit})")
        
        search_req = arxiv.Search(
            query=f"all:{query}",
            max_results=limit,
            sort_by=arxiv.SortCriterion.Relevance,
            sort_order=arxiv.SortOrder.Descending
        )
        
        records: List[ArticleRecord] = []
        fetched_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        try:
            for result in self.client.results(search_req):
                external_id = result.entry_id.split('/')[-1]
                corpus_id = f"sha256:arxiv:{external_id}"
                
                authors = [Author(name=a.name) for a in result.authors]
                published_at = result.published.strftime("%Y-%m-%dT%H:%M:%SZ") if result.published else None
                updated_at = result.updated.strftime("%Y-%m-%dT%H:%M:%SZ") if result.updated else None
                
                records.append(
                    ArticleRecord(
                        corpus_id=corpus_id,
                        source=self.source_name,
                        external_id=external_id,
                        title=self.clean_latex_text(result.title),
                        abstract=self.clean_latex_text(result.summary),
                        authors=authors,
                        published_at=published_at,
                        updated_at=updated_at,
                        landing_url=result.entry_id,
                        pdf_url=result.pdf_url,
                        categories=result.categories,
                        fetched_at=fetched_timestamp
                    )
                )
            
            self.logger.info(f"Successfully retrieved and normalized {len(records)} results from arXiv.")
            
        except arxiv.ArxivError as e:
            self.logger.error(f"Error fetching data from arXiv: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error in ArxivSearchProvider: {e}")
        
        return records
