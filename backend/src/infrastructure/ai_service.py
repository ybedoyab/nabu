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
        self._cached_query: Optional[str] = None
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
        if not research_query.strip():
            raise ValueError("Research query cannot be empty")

        normalized_query = research_query.strip().lower()
        cache_hit = (
            self._cached_query == normalized_query and bool(self.analyzed_articles)
        )
        logger.info(
            "Recommendations requested (query=%r, top_k=%d, cached_articles=%d, cache_hit=%s)",
            research_query,
            top_k,
            len(self.analyzed_articles),
            cache_hit,
        )
        if not cache_hit:
            logger.info(
                "Cache miss for query=%r (previous=%r), triggering on-demand fetch",
                research_query,
                self._cached_query,
            )
            fetched = self._fetch_and_prepare_articles(research_query)
            if fetched == 0:
                self._cached_query = None
                raise ValueError(
                    "No articles available for this query. Please try a different query or check data providers."
                )
            self._cached_query = normalized_query
        
        response = self.research_flow.get_research_recommendations(
            research_query, 
            self.analyzed_articles, 
            top_k
        )
        response["recommendations"] = self._normalize_and_balance_recommendations(
            response.get("recommendations", []),
            top_k=top_k,
        )
        logger.info(
            "Recommendations generated (query=%r, returned=%d, elapsed=%.2fs)",
            research_query,
            len(response.get("recommendations", [])),
            time.perf_counter() - started_at,
        )
        return response

    def _normalize_and_balance_recommendations(
        self,
        recommendations: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        for rec in recommendations:
            source = (rec.get("source", "") or "").strip().lower()
            if not source:
                url = (rec.get("url", "") or "").lower()
                if "arxiv.org" in url:
                    source = "arxiv"
                elif (
                    "scholar.google" in url
                    or "nature.com" in url
                    or "sciencedirect.com" in url
                    or "springer.com" in url
                    or "academic.oup.com" in url
                ):
                    source = "scholar"
            normalized.append({**rec, "source": source})

        arxiv = [r for r in normalized if r.get("source") == "arxiv"]
        scholar = [r for r in normalized if r.get("source") == "scholar"]
        others = [r for r in normalized if r.get("source") not in {"arxiv", "scholar"}]

        if top_k >= 10 and len(arxiv) >= 5 and len(scholar) >= 5:
            selected = arxiv[:5] + scholar[:5]
            leftovers = arxiv[5:] + scholar[5:] + others
            selected_keys = {
                ((r.get("title") or "") + "|" + (r.get("url") or "")).strip().lower()
                for r in selected
            }
            for rec in leftovers:
                if len(selected) >= top_k:
                    break
                key = ((rec.get("title") or "") + "|" + (rec.get("url") or "")).strip().lower()
                if key in selected_keys:
                    continue
                selected.append(rec)
                selected_keys.add(key)
            return selected

        if top_k >= 10:
            selected = normalized[:top_k]
            selected_keys = {
                ((r.get("title") or "") + "|" + (r.get("url") or "")).strip().lower()
                for r in selected
            }
            current_arxiv = len([r for r in selected if r.get("source") == "arxiv"])
            current_scholar = len([r for r in selected if r.get("source") == "scholar"])

            deficits = {
                "arxiv": max(0, 5 - current_arxiv),
                "scholar": max(0, 5 - current_scholar),
            }
            for source_name, deficit in deficits.items():
                if deficit <= 0:
                    continue
                source_candidates = [
                    a for a in self.analyzed_articles
                    if (a.get("article_metadata", {}).get("source", "") or "").lower() == source_name
                ]
                for candidate in source_candidates:
                    if deficit <= 0:
                        break
                    title = candidate.get("article_metadata", {}).get("title", "")
                    url = candidate.get("article_metadata", {}).get("url", "")
                    key = (title + "|" + url).strip().lower()
                    if not title or key in selected_keys:
                        continue
                    selected.append({
                        "id": f"rec_extra_{source_name}_{len(selected)+1}",
                        "title": title,
                        "relevance_score": 0,
                        "relevance_reasons": [f"Resultado complementario de {source_name}"],
                        "research_applications": [],
                        "url": url,
                        "source": source_name,
                        "organisms": candidate.get("organism_analysis", {}).get("organisms", []),
                        "key_concepts": candidate.get("knowledge_analysis", {}).get("key_concepts", []),
                        "selected": False,
                    })
                    selected_keys.add(key)
                    deficit -= 1

            return selected[:top_k]

        return normalized

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
                "source": article.get("source", ""),
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
        
        enriched_articles = self._enrich_selected_articles(selected_articles)
        
        response = self.research_flow.generate_summaries_and_questions(
            enriched_articles, 
            research_query
        )
        if not (response.get("combined_summary") or "").strip():
            response["combined_summary"] = (
                response.get("research_insights", {}).get("overall_insights", "") or ""
            ).strip()
        if not (response.get("combined_summary") or "").strip():
            response["combined_summary"] = (
                "Síntesis general no disponible temporalmente. "
                "Vuelve a intentar en unos segundos para regenerar la comparación."
            )
        response["suggested_questions"] = self._postprocess_suggested_questions(
            response.get("suggested_questions", []),
            selected_articles=enriched_articles,
            research_query=research_query,
        )
        response["metadata"] = {
            **response.get("metadata", {}),
            "questions_generated": len(response.get("suggested_questions", [])),
        }
        logger.info(
            "Summaries generation completed (query=%r, summaries=%d, questions=%d, elapsed=%.2fs)",
            research_query,
            len(response.get("article_summaries", [])),
            len(response.get("suggested_questions", [])),
            time.perf_counter() - started_at,
        )
        return response

    def _postprocess_suggested_questions(
        self,
        questions: List[Dict[str, Any]],
        selected_articles: List[Dict[str, Any]],
        research_query: str,
    ) -> List[Dict[str, Any]]:
        """Normalize, de-duplicate and ensure Spanish suggested questions."""
        normalized: List[Dict[str, Any]] = []
        seen = set()
        generic_en = "what are the key findings of this study?"

        for idx, q in enumerate(questions):
            if not isinstance(q, dict):
                continue
            question_text = (q.get("question", "") or "").strip()
            if not question_text:
                continue

            if question_text.lower() == generic_en:
                article_title = q.get("article_title") or selected_articles[0].get("title", "este estudio")
                question_text = f"¿Cuáles son los hallazgos clave de \"{article_title}\" para {research_query}?"
                q["focus"] = "Resultados principales del estudio"
                q["type"] = "conceptual"

            key = " ".join(question_text.lower().split())
            if key in seen:
                continue
            seen.add(key)

            normalized.append({
                "id": q.get("id") or f"q_norm_{int(time.time())}_{idx}",
                "question": question_text,
                "type": q.get("type", "conceptual"),
                "focus": q.get("focus", "Análisis del tema de investigación"),
                "article_id": q.get("article_id", ""),
                "article_title": q.get("article_title", ""),
            })

        if len(normalized) < 5:
            seed_title = selected_articles[0].get("title", "el artículo principal") if selected_articles else "el artículo"
            templates = [
                f"¿Qué evidencia adicional se requiere para fortalecer las conclusiones sobre {research_query}?",
                f"¿Cómo se compara {seed_title} con otros trabajos recientes sobre {research_query}?",
                "¿Qué limitaciones metodológicas podrían sesgar la interpretación de estos resultados?",
                f"¿Qué experimento de seguimiento sería prioritario para avanzar en {research_query}?",
                "¿Qué implicaciones prácticas tienen estos hallazgos en escenarios reales?",
            ]
            types = ["conceptual", "comparative", "methodological", "practical", "practical"]
            for i, text in enumerate(templates):
                key = " ".join(text.lower().split())
                if key in seen:
                    continue
                seen.add(key)
                normalized.append({
                    "id": f"q_tpl_{int(time.time())}_{i}",
                    "question": text,
                    "type": types[i],
                    "focus": "Pregunta guía para profundizar la investigación",
                    "article_id": selected_articles[0].get("id", "") if selected_articles else "",
                    "article_title": selected_articles[0].get("title", "") if selected_articles else "",
                })
                if len(normalized) >= 6:
                    break

        return normalized[:8]
    
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
        
        enriched_articles = self._enrich_selected_articles(selected_articles)
        
        response = self.research_flow.chat_with_selected_articles(
            user_question,
            enriched_articles,
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
        
    def _enrich_selected_articles(self, selected_articles: List[Dict]) -> List[Dict]:
        """Enrich selected articles with full abstracts from memory."""
        enriched = []
        for article in selected_articles:
            enriched_article = dict(article)
            title = article.get('title', '')
            for analyzed in self.analyzed_articles:
                if analyzed.get('article_metadata', {}).get('title') == title:
                    summary_obj = analyzed.get('summary', {})
                    if isinstance(summary_obj, dict):
                        enriched_article['abstract'] = summary_obj.get('summary', '')
                    elif isinstance(summary_obj, str):
                        enriched_article['abstract'] = summary_obj
                    break
            enriched.append(enriched_article)
        return enriched
    
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
