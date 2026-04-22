"""
AI service module for the Nabu backend.
Handles all AI-related operations using the research flow system.
"""

import sys
import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

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
        try:
            # Initialize OpenAI client
            self.openai_client = OpenAIClient()
            
            # Initialize research flow
            self.research_flow = ResearchFlow(self.openai_client)
            
            # Load analyzed articles
            self._load_analyzed_articles()
            
        except Exception as e:
            print(f"Error initializing AI service: {str(e)}")
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
            
            print("🔍 Searching for analyzed articles...")
            
            for output_dir in possible_dirs:
                print(f"📁 Checking directory: {output_dir}")
                if os.path.exists(output_dir):
                    print(f"✅ Directory exists: {output_dir}")
                    
                    # Check for analyzed articles first (priority)
                    analyzed_files = [
                        os.path.join(output_dir, "ai_analysis.json"),
                        os.path.join(output_dir, "example_analysis.json"),
                        os.path.join(output_dir, "analysis_checkpoint.json")
                    ]
                    
                    for analyzed_file in analyzed_files:
                        if os.path.exists(analyzed_file):
                            print(f"📄 Found analyzed file: {analyzed_file}")
                            try:
                                with open(analyzed_file, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                
                                # Handle different file formats
                                if analyzed_file.endswith("analysis_checkpoint.json"):
                                    # Checkpoint format
                                    if isinstance(data, dict) and 'processed_articles' in data:
                                        articles = data['processed_articles']
                                        print(f"📊 Checkpoint contains {len(articles)} analyzed articles")
                                    else:
                                        articles = data if isinstance(data, list) else []
                                else:
                                    # Regular analysis format
                                    articles = data if isinstance(data, list) else []
                                
                                if articles:
                                    self.analyzed_articles = articles
                                    articles_loaded = True
                                    print(f"✅ Loaded {len(self.analyzed_articles)} analyzed articles from {analyzed_file}")
                                    break
                                    
                            except Exception as e:
                                print(f"❌ Error loading {analyzed_file}: {str(e)}")
                                continue
                    
                    if articles_loaded:
                        break
                    
                    # Fallback: load batch files (scraped, not analyzed)
                    print("📄 No analyzed articles found, checking batch files...")
                    batch_files = []
                    for filename in os.listdir(output_dir):
                        if filename.startswith("articles_batch_") and filename.endswith(".json"):
                            batch_files.append(os.path.join(output_dir, filename))
                    
                    if batch_files:
                        print(f"📦 Found {len(batch_files)} batch files")
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
                                print(f"❌ Error loading batch file {batch_file}: {str(e)}")
                                continue
                        
                        if self.analyzed_articles:
                            articles_loaded = True
                            print(f"📦 Loaded {len(self.analyzed_articles)} scraped articles from {len(batch_files)} batch files")
                            break
                else:
                    print(f"❌ Directory not found: {output_dir}")
            
            if not articles_loaded:
                self.analyzed_articles = []
                print("❌ No articles found (neither analyzed nor scraped)")
            else:
                print(f"🎉 Total articles loaded: {len(self.analyzed_articles)}")
                if len(self.analyzed_articles) > 0:
                    # Check if articles are analyzed or just scraped
                    first_article = self.analyzed_articles[0]
                    if 'article_metadata' in first_article:
                        print("✅ Articles appear to be AI-analyzed")
                    else:
                        print("⚠️ Articles appear to be scraped only (not AI-analyzed)")
                
        except Exception as e:
            self.analyzed_articles = []
            print(f"❌ Error loading articles: {str(e)}")
    
    def get_recommendations(self, research_query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Get article recommendations for a research query.
        
        Args:
            research_query: The research query
            top_k: Number of recommendations
            
        Returns:
            Recommendations response
        """
        if not self.analyzed_articles:
            raise ValueError("No analyzed articles available. Please run analysis first.")
        
        if not research_query.strip():
            raise ValueError("Research query cannot be empty")
        
        return self.research_flow.get_research_recommendations(
            research_query, 
            self.analyzed_articles, 
            top_k
        )
    
    def get_summaries_and_questions(self, selected_articles: List[Dict], research_query: str) -> Dict[str, Any]:
        """
        Generate summaries and suggested questions for selected articles.
        
        Args:
            selected_articles: Selected article recommendations
            research_query: Original research query
            
        Returns:
            Summaries and questions response
        """
        if not selected_articles:
            raise ValueError("At least one article must be selected")
        
        if not research_query.strip():
            raise ValueError("Research query cannot be empty")
        
        return self.research_flow.generate_summaries_and_questions(
            selected_articles, 
            research_query
        )
    
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
        if not user_question.strip():
            raise ValueError("User question cannot be empty")
        
        if not selected_articles:
            raise ValueError("At least one article must be selected")
        
        return self.research_flow.chat_with_selected_articles(
            user_question,
            selected_articles,
            research_query,
            chat_history or []
        )
    
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
