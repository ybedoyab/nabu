"""
AI service module for the Nabu backend.
Handles all AI-related operations using the research flow system.
"""

import sys
import os
import json
import time
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from urllib import request as urllib_request
from urllib import error as urllib_error

# Import backend config first
from .config import settings

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Set environment variables for AI module
os.environ.update({
    'OPENAI_API_KEY': settings.OPENAI_API_KEY,
    'OPENAI_MODEL': settings.OPENAI_MODEL,
    'OPENAI_MAX_TOKENS': str(settings.OPENAI_MAX_TOKENS),
    'OPENAI_TEMPERATURE': str(settings.OPENAI_TEMPERATURE),
    'MAX_CONCURRENT_REQUESTS': str(settings.MAX_CONCURRENT_REQUESTS),
    'REQUEST_DELAY': str(settings.REQUEST_DELAY),
    'DATA_DIR': settings.DATA_DIR,
    'OUTPUT_DIR': settings.OUTPUT_DIR,
    'CACHE_DIR': settings.CACHE_DIR,
})

# Import AI modules after setting environment
from ai.src.adapters.outbound.openai_client import OpenAIClient
from ai.src.application.services.research_flow import ResearchFlow

logger = logging.getLogger(__name__)

class AIService:
    """Service class for AI operations."""
    
    def __init__(self):
        """Initialize the AI service."""
        self.openai_client = None
        self.research_flow = None
        self.analyzed_articles = []
        self._initialize()
    
    def _initialize(self):
        """Initialize AI components."""
        started_at = time.perf_counter()
        try:
            logger.info("AIService initialization started")
            # Initialize OpenAI client
            self.openai_client = OpenAIClient()
            
            # Initialize research flow
            self.research_flow = ResearchFlow(self.openai_client)
            
            # Load analyzed articles
            self._load_analyzed_articles()
            logger.info(
                "AIService initialization completed in %.2fs (cached_articles=%d)",
                time.perf_counter() - started_at,
                len(self.analyzed_articles),
            )
            
        except Exception as e:
            logger.exception("AIService initialization failed: %s", str(e))
            raise
    
    def _load_analyzed_articles(self):
        """Load analyzed articles from the AI module."""
        try:
            # Try different possible locations for analyzed articles
            possible_dirs = [
                settings.OUTPUT_DIR,
                "../ai/output",
                os.path.join(os.path.dirname(__file__), "..", "ai", "output")
            ]
            
            articles_loaded = False
            self.analyzed_articles = []
            
            print("[INFO] Searching for analyzed articles...")
            
            for output_dir in possible_dirs:
                print(f"[INFO] Checking directory: {output_dir}")
                if os.path.exists(output_dir):
                    print(f"[OK] Directory exists: {output_dir}")
                    
                    # Check for analyzed articles first (priority)
                    analyzed_files = [
                        os.path.join(output_dir, "ai_analysis.json"),
                        os.path.join(output_dir, "example_analysis.json"),
                        os.path.join(output_dir, "analysis_checkpoint.json")
                    ]
                    
                    for analyzed_file in analyzed_files:
                        if os.path.exists(analyzed_file):
                            print(f"[INFO] Found analyzed file: {analyzed_file}")
                            try:
                                with open(analyzed_file, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                
                                # Handle different file formats
                                if analyzed_file.endswith("analysis_checkpoint.json"):
                                    # Checkpoint format
                                    if isinstance(data, dict) and 'processed_articles' in data:
                                        articles = data['processed_articles']
                                        print(f"[INFO] Checkpoint contains {len(articles)} analyzed articles")
                                    else:
                                        articles = data if isinstance(data, list) else []
                                else:
                                    # Regular analysis format
                                    articles = data if isinstance(data, list) else []
                                
                                if articles:
                                    self.analyzed_articles = articles
                                    articles_loaded = True
                                    print(f"[OK] Loaded {len(self.analyzed_articles)} analyzed articles from {analyzed_file}")
                                    break
                                    
                            except Exception as e:
                                print(f"[ERROR] Error loading {analyzed_file}: {str(e)}")
                                continue
                    
                    if articles_loaded:
                        break
                    
                    # Fallback: load batch files (scraped, not analyzed)
                    print("[INFO] No analyzed articles found, checking batch files...")
                    batch_files = []
                    for filename in os.listdir(output_dir):
                        if filename.startswith("articles_batch_") and filename.endswith(".json"):
                            batch_files.append(os.path.join(output_dir, filename))
                    
                    if batch_files:
                        print(f"[INFO] Found {len(batch_files)} batch files")
                        # Sort batch files by number
                        batch_files.sort(key=lambda x: int(x.split("articles_batch_")[1].split(".json")[0]))
                        
                        # Load all batch files
                        for batch_file in batch_files:
                            try:
                                with open(batch_file, 'r', encoding='utf-8') as f:
                                    batch_articles = json.load(f)
                                    if isinstance(batch_articles, list):
                                        self.analyzed_articles.extend(batch_articles)
                                    else:
                                        # If it's a dict with articles key
                                        if 'articles' in batch_articles:
                                            self.analyzed_articles.extend(batch_articles['articles'])
                                        else:
                                            self.analyzed_articles.append(batch_articles)
                            except Exception as e:
                                print(f"[ERROR] Error loading batch file {batch_file}: {str(e)}")
                                continue
                        
                        if self.analyzed_articles:
                            articles_loaded = True
                            print(f"[OK] Loaded {len(self.analyzed_articles)} scraped articles from {len(batch_files)} batch files")
                            break
                else:
                    print(f"[WARN] Directory not found: {output_dir}")
            
            if not articles_loaded:
                self.analyzed_articles = []
                print("[WARN] No articles found (neither analyzed nor scraped)")
            else:
                print(f"[OK] Total articles loaded: {len(self.analyzed_articles)}")
                if len(self.analyzed_articles) > 0:
                    # Check if articles are analyzed or just scraped
                    first_article = self.analyzed_articles[0]
                    if 'article_metadata' in first_article:
                        print("[OK] Articles appear to be AI-analyzed")
                    else:
                        print("[WARN] Articles appear to be scraped only (not AI-analyzed)")
                
        except Exception as e:
            self.analyzed_articles = []
            print(f"[ERROR] Error loading articles: {str(e)}")
    
    def get_recommendations(self, research_query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Get article recommendations for a research query.
        
        Args:
            research_query: The research query
            top_k: Number of recommendations
            
        Returns:
            Recommendations response
        """
        started_at = time.perf_counter()
        logger.info(
            "Recommendations requested (query=%r, top_k=%d, cached_articles=%d)",
            research_query,
            top_k,
            len(self.analyzed_articles),
        )
        if not self.analyzed_articles:
            logger.info("No cached analyzed articles, triggering on-demand fetch")
            fetched = self._fetch_and_prepare_articles(research_query)
            if fetched == 0:
                raise ValueError(
                    "No articles available for this query. Please try a different query or check data providers."
                )
        
        if not research_query.strip():
            raise ValueError("Research query cannot be empty")
        
        response = self.research_flow.get_research_recommendations(
            research_query, 
            self.analyzed_articles, 
            top_k
        )
        logger.info(
            "Recommendations generated (query=%r, returned=%d, elapsed=%.2fs)",
            research_query,
            len(response.get("recommendations", [])),
            time.perf_counter() - started_at,
        )
        return response

    def _fetch_and_prepare_articles(self, research_query: str) -> int:
        """Fetch articles from Data API and map them into recommendation-ready format."""
        started_at = time.perf_counter()
        data_api_url = os.getenv("DATA_API_URL", "http://127.0.0.1:8081")
        endpoint = f"{data_api_url.rstrip('/')}/api/v1/session/fetch"

        payload = {
            "query": research_query,
            "limits": {
                "arxiv": int(os.getenv("DATA_API_DEFAULT_ARXIV_LIMIT", "15")),
                "scholar": int(os.getenv("DATA_API_DEFAULT_SCHOLAR_LIMIT", "10")),
            },
            "locale": "es",
        }
        req_body = json.dumps(payload).encode("utf-8")
        req = urllib_request.Request(
            endpoint,
            data=req_body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        logger.info(
            "Fetching articles from Data API (endpoint=%s, query=%r, arxiv=%s, scholar=%s)",
            endpoint,
            research_query,
            payload["limits"]["arxiv"],
            payload["limits"]["scholar"],
        )

        try:
            with urllib_request.urlopen(req, timeout=60) as response:
                body = response.read().decode("utf-8")
                parsed = json.loads(body)
        except urllib_error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            logger.error("Data API HTTP error (%s): %s", exc.code, detail)
            return 0
        except Exception as exc:
            logger.exception("Failed to fetch articles from Data API: %s", exc)
            return 0

        articles = parsed.get("articles", [])
        mapped = [self._map_fetched_article(article) for article in articles]
        mapped = [article for article in mapped if article.get("article_metadata", {}).get("title")]
        self.analyzed_articles = mapped
        logger.info(
            "On-demand article fetch completed (raw=%d, mapped=%d, elapsed=%.2fs)",
            len(articles),
            len(self.analyzed_articles),
            time.perf_counter() - started_at,
        )
        return len(self.analyzed_articles)

    def _map_fetched_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Map Data API article shape to the analyzed-article shape expected by ResearchFlow."""
        title = article.get("title", "")
        abstract = article.get("abstract", "") or article.get("snippet", "")
        keywords = article.get("keywords", []) or []
        categories = article.get("categories", []) or []
        concepts = self._extract_key_concepts(title=title, abstract=abstract, keywords=keywords, categories=categories)

        return {
            "article_metadata": {
                "title": title,
                "url": article.get("landing_url", ""),
            },
            "summary": {
                "summary": abstract,
            },
            "organism_analysis": {
                "organisms": [],
            },
            "knowledge_analysis": {
                "key_concepts": concepts,
            },
        }

    @staticmethod
    def _extract_key_concepts(
        title: str, abstract: str, keywords: List[str], categories: List[str]
    ) -> List[str]:
        combined = " ".join([title, abstract])
        tokens = [tok.strip(".,:;()[]{}!?\"'").lower() for tok in combined.split()]
        candidate_tokens = [
            tok for tok in tokens
            if len(tok) > 3 and tok.isascii() and tok not in {"with", "from", "that", "this", "using", "based"}
        ]

        concepts: List[str] = []
        seen = set()
        for item in list(keywords) + list(categories) + candidate_tokens:
            normalized = item.strip().lower()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            concepts.append(normalized)
            if len(concepts) >= 12:
                break

        return concepts
    
    def get_summaries_and_questions(self, selected_articles: List[Dict], research_query: str) -> Dict[str, Any]:
        """
        Generate summaries and suggested questions for selected articles.
        
        Args:
            selected_articles: Selected article recommendations
            research_query: Original research query
            
        Returns:
            Summaries and questions response
        """
        started_at = time.perf_counter()
        logger.info(
            "Summaries generation requested (query=%r, selected_articles=%d)",
            research_query,
            len(selected_articles),
        )
        if not selected_articles:
            raise ValueError("At least one article must be selected")
        
        if not research_query.strip():
            raise ValueError("Research query cannot be empty")
        
        response = self.research_flow.generate_summaries_and_questions(
            selected_articles, 
            research_query
        )
        logger.info(
            "Summaries generation completed (query=%r, summaries=%d, questions=%d, elapsed=%.2fs)",
            research_query,
            len(response.get("article_summaries", [])),
            len(response.get("suggested_questions", [])),
            time.perf_counter() - started_at,
        )
        return response
    
    def chat_with_articles(self, user_question: str, selected_articles: List[Dict], 
                          research_query: str, chat_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Process chat interaction with selected articles.
        
        Args:
            user_question: User's question
            selected_articles: Selected articles for context
            research_query: Original research query
            chat_history: Previous chat messages
            
        Returns:
            Chat response
        """
        started_at = time.perf_counter()
        history_size = len(chat_history or [])
        logger.info(
            "Chat requested (query=%r, selected_articles=%d, chat_history=%d)",
            research_query,
            len(selected_articles),
            history_size,
        )
        if not user_question.strip():
            raise ValueError("User question cannot be empty")
        
        if not selected_articles:
            raise ValueError("At least one article must be selected")
        
        response = self.research_flow.chat_with_selected_articles(
            user_question,
            selected_articles,
            research_query,
            chat_history or []
        )
        logger.info(
            "Chat completed (query=%r, follow_ups=%d, elapsed=%.2fs)",
            research_query,
            len(response.get("follow_up_questions", [])),
            time.perf_counter() - started_at,
        )
        return response
    
    def get_articles_list(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get list of available articles for debugging.
        
        Args:
            limit: Maximum number of articles to return
            
        Returns:
            List of article summaries
        """
        if not self.analyzed_articles:
            return []
        
        articles_list = []
        for article in self.analyzed_articles[:limit]:
            articles_list.append({
                "title": article.get('article_metadata', {}).get('title', 'Unknown'),
                "url": article.get('article_metadata', {}).get('url', ''),
                "organisms": article.get('organism_analysis', {}).get('organisms', []),
                "key_concepts": article.get('knowledge_analysis', {}).get('key_concepts', [])[:5]
            })
        
        return articles_list
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get AI service status.
        
        Returns:
            Status information
        """
        return {
            "articles_available": len(self.analyzed_articles),
            "openai_configured": self.openai_client is not None,
            "research_flow_ready": self.research_flow is not None,
            "service_healthy": (
                self.openai_client is not None and 
                self.research_flow is not None and 
                len(self.analyzed_articles) > 0
            )
        }

# Global AI service instance
ai_service = None

def get_ai_service() -> AIService:
    """Get the global AI service instance."""
    global ai_service
    if ai_service is None:
        ai_service = AIService()
    return ai_service

def initialize_ai_service():
    """Initialize the AI service."""
    global ai_service
    try:
        ai_service = AIService()
        return True
    except Exception as e:
        print(f"Failed to initialize AI service: {str(e)}")
        return False
