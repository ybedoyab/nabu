import arxiv
from pylatexenc.latex2text import LatexNodes2Text
from typing import List, Dict, Any
from datetime import datetime, timezone
import json
import os

from common.logger import setup_scraper_logger

class ArxivScraper:
    """
    Singleton class that encapsulates the arxiv Client and fetching logic.
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ArxivScraper, cls).__new__(cls)
            # Initialization
            cls._instance.client = arxiv.Client()
            
            # Setup Logger
            log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
            cls._instance.logger = setup_scraper_logger("arxiv_scraper", log_dir)
            cls._instance.logger.info("ArxivScraper Singleton instantiated.")
            
        return cls._instance

    @staticmethod
    def clean_latex_text(text: str) -> str:
        """
        Cleans LaTeX formatting from strings and returns readable plain text.
        Uses pylatexenc for safe decoding.
        """
        if not text:
            return ""
        # Remove basic newlines
        text = text.replace('\n', ' ').strip()
        try:
            # Convert LaTeX to plain text
            converter = LatexNodes2Text()
            text = converter.latex_to_text(text)
        except Exception as e:
            # Fallback to the text without newlines if pylatexenc fails
            pass
        # Remove double spaces
        return ' '.join(text.split())

    def fetch_data(self, query: str, max_results: int = 10, sort_by_relevance: bool = True) -> List[Dict[str, Any]]:
        """
        Fetches and normalizes data from arXiv based on a query.
        Returns a list of standardized dictionaries ready for consumption.
        """
        self.logger.info(f"Fetching arXiv data for query: '{query}' (max_results={max_results})")
        
        sort_criterion = arxiv.SortCriterion.Relevance if sort_by_relevance else arxiv.SortCriterion.SubmittedDate
        
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=sort_criterion
        )
        
        results = []
        fetched_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        try:
            for result in self.client.results(search):
                external_id = result.entry_id.split('/')[-1]
                corpus_id = f"sha256:arxiv:{external_id}"
                
                normalized_result = {
                    "corpus_id": corpus_id,
                    "source": "arxiv",
                    "external_id": external_id,
                    "title": self.clean_latex_text(result.title),
                    "abstract": self.clean_latex_text(result.summary),
                    "authors": [{"name": author.name, "affiliation": None} for author in result.authors],
                    "published_at": result.published.strftime("%Y-%m-%dT%H:%M:%SZ") if result.published else None,
                    "updated_at": result.updated.strftime("%Y-%m-%dT%H:%M:%SZ") if result.updated else None,
                    "landing_url": result.entry_id,
                    "pdf_url": result.pdf_url,
                    "categories": result.categories,
                    "keywords": [],
                    "venue": None,
                    "citation_count": None,
                    "snippet_is_partial": False,
                    "authors_incomplete": False,
                    "fetched_at": fetched_timestamp
                }
                results.append(normalized_result)
            
            self.logger.info(f"Successfully retrieved and normalized {len(results)} results.")
            
        except arxiv.ArxivError as e:
            self.logger.error(f"Error fetching data from arXiv: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
        
        return results

if __name__ == "__main__":
    # Test execution
    scraper1 = ArxivScraper()
    scraper2 = ArxivScraper()
    
    # Verify Singleton
    scraper1.logger.info(f"Scraper 1 memory ID: {id(scraper1)}")
    scraper1.logger.info(f"Scraper 2 memory ID: {id(scraper2)}")
    assert id(scraper1) == id(scraper2), "Singleton pattern failed!"
    
    sample_query = "quantum computing"
    data = scraper1.fetch_data(query=sample_query, max_results=2)
    
    # Save the output to a test file
    output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_output.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    scraper1.logger.info(f"Test script completed. Output saved to {output_file}.")
