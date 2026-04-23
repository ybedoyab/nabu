"""
OpenAI client module for processing scientific articles.
Handles all interactions with OpenAI API for text analysis and extraction.
"""

import openai
import json
from typing import Dict, List, Optional, Any
import os
from tqdm import tqdm
import time
from ...infrastructure.config import Config

class OpenAIClient:
    """Client for OpenAI API interactions."""
    
    def __init__(self):
        if not Config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_MODEL
        self.max_tokens = Config.OPENAI_MAX_TOKENS
        self.temperature = Config.OPENAI_TEMPERATURE
    
    def extract_organisms(self, title: str, content: str = "") -> Dict[str, Any]:
        """
        Extract organism information from article title and content.
        
        Args:
            title: Article title
            content: Article content (optional)
            
        Returns:
            Dictionary with organism information
        """
        prompt = Config.ORGANISM_EXTRACTION_PROMPT.format(title=title)
        
        if content:
            # Add content to prompt if available
            prompt += f"\n\nAdditional Content (first 2000 characters): {content[:2000]}"
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a scientific research assistant. Extract organism information accurately from research articles."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            result_text = response.choices[0].message.content
            
            # Try to parse as JSON, fallback to text
            try:
                return json.loads(result_text)
            except json.JSONDecodeError:
                return {
                    "organisms": [],
                    "organism_types": [],
                    "study_subjects": [],
                    "environment": "unknown",
                    "raw_response": result_text
                }
                
        except Exception as e:
            print(f"Error extracting organisms for '{title}': {str(e)}")
            return {
                "organisms": [],
                "organism_types": [],
                "study_subjects": [],
                "environment": "unknown",
                "error": str(e)
            }
    
    def summarize_article(self, title: str, content: str) -> Dict[str, Any]:
        """
        Generate comprehensive summary of scientific article.
        
        Args:
            title: Article title
            content: Article content
            
        Returns:
            Dictionary with article summary
        """
        # Truncate content if too long
        max_content_length = 8000  # Leave room for prompt
        if len(content) > max_content_length:
            content = content[:max_content_length] + "... [truncated]"
        
        prompt = Config.ARTICLE_SUMMARY_PROMPT.format(title=title, content=content)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a scientific research assistant. Provide clear, structured summaries of research articles."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            summary_text = response.choices[0].message.content
            
            return {
                "summary": summary_text,
                "title": title,
                "word_count": len(content.split()),
                "processing_timestamp": time.time()
            }
            
        except Exception as e:
            print(f"Error summarizing '{title}': {str(e)}")
            return {
                "summary": f"Error processing article: {str(e)}",
                "title": title,
                "error": str(e),
                "processing_timestamp": time.time()
            }
    
    def analyze_knowledge_connections(self, title: str, content: str) -> Dict[str, Any]:
        """
        Analyze article for knowledge graph connections and insights.
        
        Args:
            title: Article title
            content: Article content
            
        Returns:
            Dictionary with knowledge analysis
        """
        # Truncate content if too long
        max_content_length = 8000
        if len(content) > max_content_length:
            content = content[:max_content_length] + "... [truncated]"
        
        prompt = Config.KNOWLEDGE_GRAPH_PROMPT.format(title=title, content=content)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a scientific research assistant. Analyze research articles to identify key concepts, relationships, and knowledge gaps."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            analysis_text = response.choices[0].message.content
            
            # Try to parse as JSON, fallback to text
            try:
                parsed_analysis = json.loads(analysis_text)
                return {
                    **parsed_analysis,
                    "title": title,
                    "processing_timestamp": time.time()
                }
            except json.JSONDecodeError:
                return {
                    "key_concepts": [],
                    "biological_processes": [],
                    "space_effects": [],
                    "research_gaps": [],
                    "connections": [],
                    "raw_analysis": analysis_text,
                    "title": title,
                    "processing_timestamp": time.time()
                }
                
        except Exception as e:
            print(f"Error analyzing knowledge connections for '{title}': {str(e)}")
            return {
                "key_concepts": [],
                "biological_processes": [],
                "space_effects": [],
                "research_gaps": [],
                "connections": [],
                "error": str(e),
                "title": title,
                "processing_timestamp": time.time()
            }
    
    def process_article_comprehensive(self, article_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Process article with all available AI analysis methods.
        
        Args:
            article_data: Dictionary with article information (title, content, etc.)
            
        Returns:
            Comprehensive analysis results
        """
        title = article_data.get('title', '')
        content = article_data.get('full_text', '') or article_data.get('abstract', '')
        
        print(f"Processing article: {title[:100]}...")
        
        # Extract organisms
        organism_analysis = self.extract_organisms(title, content)
        
        # Generate summary
        summary = self.summarize_article(title, content)
        
        # Analyze knowledge connections
        knowledge_analysis = self.analyze_knowledge_connections(title, content)
        
        # Combine all results
        comprehensive_result = {
            "article_metadata": {
                "title": title,
                "url": article_data.get('url', ''),
                "processing_timestamp": time.time()
            },
            "organism_analysis": organism_analysis,
            "summary": summary,
            "knowledge_analysis": knowledge_analysis,
            "raw_content": {
                "abstract": article_data.get('abstract', ''),
                "introduction": article_data.get('introduction', ''),
                "methods": article_data.get('methods', ''),
                "results": article_data.get('results', ''),
                "discussion": article_data.get('discussion', ''),
                "conclusion": article_data.get('conclusion', '')
            }
        }
        
        return comprehensive_result
    
    def process_articles_batch(self, articles: List[Dict[str, str]], checkpoint_file: str = "analysis_checkpoint.json", output_file: str = "ai_analysis.json") -> List[Dict[str, Any]]:
        """
        Process multiple articles in batch with checkpoint support.
        
        Args:
            articles: List of article dictionaries
            checkpoint_file: File to save progress
            output_file: Final output file
            
        Returns:
            List of processed article results
        """
        import signal
        import sys
        from ...infrastructure.config import Config
        
        checkpoint_path = os.path.join(Config.OUTPUT_DIR, checkpoint_file)
        output_path = os.path.join(Config.OUTPUT_DIR, output_file)
        
        # Load existing checkpoint if it exists
        processed_articles = self._load_checkpoint(checkpoint_path)
        start_index = len(processed_articles)
        
        print(f"Processing {len(articles)} articles with OpenAI API...")
        if start_index > 0:
            print(f"Resuming from checkpoint: {start_index} articles already processed")
        
        # Set up signal handler for graceful interruption
        def signal_handler(signum, frame):
            print(f"\n\n🛑 Analysis interrupted by user (Ctrl+C)")
            print(f"💾 Saving checkpoint with {len(processed_articles)} processed articles...")
            self._save_checkpoint(processed_articles, checkpoint_path)
            print(f"✅ Checkpoint saved to: {checkpoint_path}")
            print(f"🔄 To resume, run the analysis command again")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        try:
            for i in range(start_index, len(articles)):
                article = articles[i]
                try:
                    print(f"Processing article {i+1}/{len(articles)}: {article.get('title', 'Unknown')[:60]}...")
                    
                    result = self.process_article_comprehensive(article)
                    processed_articles.append(result)
                    
                    # Save checkpoint every 10 articles
                    if (i + 1) % 10 == 0:
                        self._save_checkpoint(processed_articles, checkpoint_path)
                        print(f"💾 Checkpoint saved: {i+1}/{len(articles)} articles processed")
                    
                    # Add delay between requests to respect rate limits
                    if i < len(articles) - 1:  # Don't delay after last article
                        time.sleep(1)
                        
                except Exception as e:
                    print(f"❌ Error processing article {i+1}: {str(e)}")
                    processed_articles.append({
                        "article_metadata": {
                            "title": article.get('title', 'Unknown'),
                            "url": article.get('url', ''),
                            "error": str(e),
                            "processing_timestamp": time.time()
                        }
                    })
            
            # Save final results
            print(f"✅ Analysis complete! Saving {len(processed_articles)} articles to {output_path}")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(processed_articles, f, indent=2, ensure_ascii=False)
            
            # Remove checkpoint file since analysis is complete
            if os.path.exists(checkpoint_path):
                os.remove(checkpoint_path)
                print(f"🗑️ Checkpoint file removed")
            
        except KeyboardInterrupt:
            # This will be handled by the signal handler
            pass
        
        return processed_articles
    
    def _load_checkpoint(self, checkpoint_path: str) -> List[Dict[str, Any]]:
        """Load checkpoint if it exists."""
        if os.path.exists(checkpoint_path):
            try:
                with open(checkpoint_path, 'r', encoding='utf-8') as f:
                    checkpoint_data = json.load(f)
                    if isinstance(checkpoint_data, list):
                        return checkpoint_data
                    elif isinstance(checkpoint_data, dict) and 'processed_articles' in checkpoint_data:
                        return checkpoint_data['processed_articles']
            except Exception as e:
                print(f"⚠️ Error loading checkpoint: {str(e)}")
                return []
        return []
    
    def _save_checkpoint(self, processed_articles: List[Dict[str, Any]], checkpoint_path: str):
        """Save checkpoint with metadata."""
        checkpoint_data = {
            "processed_articles": processed_articles,
            "checkpoint_timestamp": time.time(),
            "total_processed": len(processed_articles),
            "version": "1.0"
        }
        
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
    
    def chat_with_articles(self, query: str, article_context: List[Dict] = None, chat_history: List[Dict] = None, research_query: str = None) -> Dict[str, Any]:
        """
        Chat interface for asking questions about processed articles.
        
        Args:
            query: User question
            article_context: List of relevant articles for context
            chat_history: Previous chat messages
            research_query: Original research topic
            
        Returns:
            Dictionary with 'response' and 'follow_up_questions'
        """
        system_prompt = f"""You are Nabu, an advanced scientific Research Co-Pilot specializing in literature analysis and cross-reference synthesis.
        The user is conducting research on the topic: "{research_query if research_query else 'Unspecified'}"
        
        You have access to a specific, filtered corpus of scientific articles provided in the context below. 
        Your primary goal is to help the researcher synthesize this information, find connections, and discover new insights.

        RULES FOR YOUR RESPONSE:
        1. STRICT CITATIONS: You MUST cite your sources for every factual claim. Use the exact format `[Title]`. Never invent citations.
        2. CROSS-ANALYSIS: Whenever possible, compare and contrast the different articles. Point out where they agree, disagree, or complement each other.
        3. METHODOLOGICAL RIGOR: Pay attention to the organisms studied, key concepts, and limitations mentioned in the articles.
        4. NO HALLUCINATIONS: If the provided articles do not contain the answer, explicitly state "Based on the provided articles, I cannot answer this..." Do not use outside knowledge to invent answers about the specific papers.
        5. ACADEMIC TONE: Maintain a professional, objective, and analytical tone.
        
        You must format your response as a JSON object with two fields:
        - "response": Your detailed answer to the user's question. Use rich Markdown for formatting (bolding, lists, etc).
        - "follow_up_questions": A list of 3 highly relevant, analytical follow-up questions the researcher should explore next to deepen their understanding of this specific corpus.
        
        JSON structure:
        {{
            "response": "Your detailed, cited answer...",
            "follow_up_questions": [
                {{"question": "How does the methodology in [Article 1] compare to [Article 2]?", "type": "comparative"}},
                {{"question": "What are the limitations of the findings regarding [Concept]?", "type": "analytical"}}
            ]
        }}
        """
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add article context
        if article_context:
            context_msg = "Relevant article context for this conversation:\n\n"
            for article in article_context:
                context_msg += f"Title: {article.get('title', 'Unknown')}\n"
                if 'url' in article and article['url']:
                    context_msg += f"URL: {article['url']}\n"
                if 'organisms' in article and article['organisms']:
                    context_msg += f"Organisms: {', '.join(article['organisms'])}\n"
                if 'key_concepts' in article and article['key_concepts']:
                    context_msg += f"Key Concepts: {', '.join(article['key_concepts'])}\n"
                if 'summary' in article:
                    context_msg += f"Abstract/Summary: {article['summary'][:2000]}\n"
                context_msg += "---\n"
            messages.append({"role": "system", "content": context_msg})
            
        # Add chat history
        if chat_history:
            for msg in chat_history[-10:]:
                role = msg.get("role", "user")
                if role not in ["system", "user", "assistant"]:
                    role = "user"
                messages.append({"role": role, "content": msg.get("content", "")})
                
        # Add current query
        messages.append({"role": "user", "content": query})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            try:
                parsed = json.loads(result_text)
                return {
                    "response": parsed.get("response", "Could not generate response."),
                    "follow_up_questions": parsed.get("follow_up_questions", [])
                }
            except json.JSONDecodeError:
                return {
                    "response": result_text,
                    "follow_up_questions": []
                }
            
        except Exception as e:
            return {
                "response": f"Error processing your question: {str(e)}",
                "follow_up_questions": []
            }
    
    def recommend_articles_for_research(self, research_query: str, analyzed_articles: List[Dict], top_k: int = 5) -> Dict[str, Any]:
        """
        Recommend the best articles for a specific research topic.
        
        Args:
            research_query: Research topic or question
            analyzed_articles: List of analyzed articles with AI insights
            top_k: Number of top articles to recommend
            
        Returns:
            Dictionary with recommendations and reasoning
        """
        # Create a comprehensive prompt for article recommendation
        system_prompt = """You are a research librarian specializing in scientific literature.
        Your task is to analyze research queries and recommend the most relevant scientific articles from a database.
        
        For each recommendation, provide:
        1. Relevance score (1-10)
        2. Key reasons why this article is relevant
        3. Specific aspects that match the research query
        4. Potential research applications
        5. Complementary studies to consider
        
        Focus on practical utility for researchers and clear explanations of relevance."""
        
        # Prepare article summaries for analysis
        articles_summary = ""
        for i, article in enumerate(analyzed_articles):  # Process all articles
            title = article.get('article_metadata', {}).get('title', 'Unknown')
            summary = article.get('summary', {}).get('summary', 'No summary available')
            organisms = article.get('organism_analysis', {}).get('organisms', [])
            concepts = article.get('knowledge_analysis', {}).get('key_concepts', [])
            
            articles_summary += f"""
Article {i+1}:
Title: {title}
Summary: {summary[:300]}...
Organisms: {', '.join(organisms)}
Key Concepts: {', '.join(concepts[:5])}
---
"""
        
        user_prompt = f"""
Research Query: {research_query}

Available Articles Database ({len(analyzed_articles)} articles):
{articles_summary}

IMPORTANT: You must recommend EXACTLY {top_k} articles, ordered by relevance score (highest first).

For each recommendation, provide:
- Article title (exact match from the database)
- Relevance score (1-10, must be precise)
- Key reasons for relevance (2-3 specific reasons)
- Specific research applications (2-3 applications)
- How it contributes to the research goal

CRITICAL REQUIREMENTS:
1. Return EXACTLY {top_k} recommendations
2. Order by relevance score (highest first)
3. Use exact article titles from the database
4. Provide specific, detailed reasons for each recommendation

Format as JSON with this structure:
{{
    "research_query": "{research_query}",
    "recommendations": [
        {{
            "article_title": "EXACT_TITLE_FROM_DATABASE",
            "relevance_score": 9,
            "relevance_reasons": ["specific reason 1", "specific reason 2"],
            "research_applications": ["application 1", "application 2"],
            "contribution": "Specific contribution to the research goal"
        }}
    ],
    "research_insights": "Overall insights about the research field",
    "knowledge_gaps": ["gap1", "gap2"],
    "suggested_follow_up": "Additional research directions"
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=6000,  # Increased for more detailed responses
                temperature=0.2  # Very low temperature for consistent recommendations
            )
            
            result_text = response.choices[0].message.content
            
            # Try to parse as JSON, fallback to text
            try:
                parsed_result = json.loads(result_text)
                return parsed_result
            except json.JSONDecodeError:
                return {
                    "research_query": research_query,
                    "recommendations": [],
                    "raw_response": result_text,
                    "error": "Could not parse JSON response"
                }
                
        except Exception as e:
                return {
                "research_query": research_query,
                "recommendations": [],
                "error": str(e)
            }
    
    def recommend_articles_individual_analysis(self, research_query: str, analyzed_articles: List[Dict], top_k: int = 5) -> Dict[str, Any]:
        """
        Alternative recommendation method using individual article analysis for better precision.
        
        Args:
            research_query: Research topic or question
            analyzed_articles: List of analyzed articles with AI insights
            top_k: Number of top articles to recommend
            
        Returns:
            Dictionary with recommendations and reasoning
        """
        print(f"Analyzing {len(analyzed_articles)} articles individually for better precision...")
        
        scored_articles = []
        
        for i, article in enumerate(analyzed_articles):
            title = article.get('article_metadata', {}).get('title', '')
            summary = article.get('summary', {}).get('summary', '')
            organisms = article.get('organism_analysis', {}).get('organisms', [])
            concepts = article.get('knowledge_analysis', {}).get('key_concepts', [])
            
            if not title or not summary:
                continue
            
            # Analyze relevance for this specific article
            relevance_analysis = self._analyze_article_relevance(
                research_query, title, summary, organisms, concepts
            )
            
            if relevance_analysis:
                article_copy = article.copy()
                article_copy.update(relevance_analysis)
                scored_articles.append(article_copy)
            
            print(f"   Analyzed {i+1}/{len(analyzed_articles)} articles", end='\r')
        
        print(f"\nAnalysis complete! Found {len(scored_articles)} relevant articles")
        
        # Sort by relevance score (highest first)
        scored_articles.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Take top_k recommendations
        top_recommendations = scored_articles[:top_k]
        
        # Format recommendations
        formatted_recommendations = []
        for article in top_recommendations:
            formatted_recommendations.append({
                "article_title": article.get('article_metadata', {}).get('title', ''),
                "relevance_score": article.get('relevance_score', 0),
                "relevance_reasons": article.get('relevance_reasons', []),
                "research_applications": article.get('research_applications', []),
                "contribution": article.get('contribution', ''),
                "url": article.get('article_metadata', {}).get('url', ''),
                "organisms": article.get('organism_analysis', {}).get('organisms', []),
                "key_concepts": article.get('knowledge_analysis', {}).get('key_concepts', [])
            })
        
        return {
            "research_query": research_query,
            "recommendations": formatted_recommendations,
            "total_analyzed": len(analyzed_articles),
            "relevant_found": len(scored_articles),
            "analysis_method": "individual_article_analysis"
        }

    def recommend_articles_fast(self, research_query: str, analyzed_articles: List[Dict], top_k: int = 5) -> Dict[str, Any]:
        """
        Fast recommendation method using pre-analyzed keywords and concepts.
        
        Args:
            research_query: Research topic or question
            analyzed_articles: List of analyzed articles with AI insights
            top_k: Number of top articles to recommend
            
        Returns:
            Dictionary with recommendations and reasoning
        """
        print(f"Fast analysis of {len(analyzed_articles)} articles using keywords and concepts...")
        
        # Normalize query for matching
        query_words = set(research_query.lower().split())
        
        scored_articles = []
        
        for article in analyzed_articles:
            title = article.get('article_metadata', {}).get('title', '').lower()
            summary = article.get('summary', {}).get('summary', '').lower()
            organisms = [org.lower() for org in article.get('organism_analysis', {}).get('organisms', [])]
            concepts = [concept.lower() for concept in article.get('knowledge_analysis', {}).get('key_concepts', [])]
            
            if not title:
                continue
            
            # Calculate relevance score based on keyword matching
            score = 0
            
            # Title matches (highest weight)
            title_matches = sum(1 for word in query_words if word in title)
            score += title_matches * 3
            
            # Summary matches (medium weight)
            summary_matches = sum(1 for word in query_words if word in summary)
            score += summary_matches * 2
            
            # Concept matches (high weight)
            concept_matches = sum(1 for word in query_words if any(word in concept for concept in concepts))
            score += concept_matches * 2.5
            
            # Organism matches (medium weight)
            organism_matches = sum(1 for word in query_words if any(word in org for org in organisms))
            score += organism_matches * 2
            
            # Bonus for exact phrase matches
            if research_query.lower() in title:
                score += 5
            if research_query.lower() in summary:
                score += 3
            
            # Normalize score to 0-10 scale
            max_possible_score = len(query_words) * 3 + 5  # Title matches + bonus
            normalized_score = min(10, (score / max_possible_score) * 10) if max_possible_score > 0 else 0
            
            if normalized_score > 0:
                article_copy = article.copy()
                article_copy['relevance_score'] = round(normalized_score, 1)
                article_copy['relevance_reasons'] = self._generate_fast_reasons(query_words, title, summary, concepts, organisms)
                article_copy['research_applications'] = self._generate_fast_applications(concepts, organisms)
                article_copy['contribution'] = f"Provides insights on {', '.join(concepts[:3])} relevant to your research query"
                scored_articles.append(article_copy)
        
        # Sort by relevance score (highest first)
        scored_articles.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Take top_k recommendations
        top_recommendations = scored_articles[:top_k]
        
        # Format recommendations
        formatted_recommendations = []
        for article in top_recommendations:
            organisms = article.get('organism_analysis', {}).get('organisms', [])
            concepts = article.get('knowledge_analysis', {}).get('key_concepts', [])
            
            formatted_recommendations.append({
                "article_title": article.get('article_metadata', {}).get('title', ''),
                "relevance_score": article.get('relevance_score', 0),
                "relevance_reasons": article.get('relevance_reasons', []),
                "research_applications": article.get('research_applications', []),
                "contribution": article.get('contribution', ''),
                "url": article.get('article_metadata', {}).get('url', ''),
                "organisms": organisms,
                "key_concepts": concepts
            })
        
        print(f"Fast analysis complete! Found {len(scored_articles)} relevant articles")
        
        return {
            "research_query": research_query,
            "recommendations": formatted_recommendations,
            "total_analyzed": len(analyzed_articles),
            "relevant_found": len(scored_articles),
            "analysis_method": "fast_keyword_matching"
        }
    
    def _generate_fast_reasons(self, query_words: set, title: str, summary: str, concepts: list, organisms: list) -> list:
        """Generate relevance reasons based on keyword matches."""
        reasons = []
        
        # Title matches
        title_matches = [word for word in query_words if word in title]
        if title_matches:
            reasons.append(f"Title contains relevant keywords: {', '.join(title_matches)}")
        
        # Concept matches
        concept_matches = [word for word in query_words if any(word in concept for concept in concepts)]
        if concept_matches:
            reasons.append(f"Addresses key concepts: {', '.join(concept_matches)}")
        
        # Organism matches
        organism_matches = [word for word in query_words if any(word in org for org in organisms)]
        if organism_matches:
            reasons.append(f"Studies relevant organisms: {', '.join(organism_matches)}")
        
        # Summary matches
        summary_matches = [word for word in query_words if word in summary]
        if summary_matches:
            reasons.append(f"Content discusses: {', '.join(summary_matches[:3])}")
        
        return reasons[:3] if reasons else ["General relevance to research topic"]
    
    def _generate_fast_applications(self, concepts: list, organisms: list) -> list:
        """Generate research applications based on concepts and organisms."""
        applications = []
        
        if concepts:
            applications.append(f"Understanding {concepts[0]} mechanisms")
            if len(concepts) > 1:
                applications.append(f"Research on {concepts[1]} applications")
        
        if organisms:
            applications.append(f"Studies using {organisms[0]} as model organism")
        
        return applications[:3] if applications else ["General research applications"]
    
    def _analyze_article_relevance(self, query: str, title: str, summary: str, organisms: List[str], concepts: List[str]) -> Dict:
        """
        Analyze relevance of a single article to a research query.
        
        Args:
            query: Research query
            title: Article title
            summary: Article summary
            organisms: List of organisms
            concepts: List of key concepts
            
        Returns:
            Dictionary with relevance analysis
        """
        system_prompt = """You are a research librarian analyzing article relevance to specific research queries.
        Analyze the article and provide a relevance score (0-10) and detailed reasoning.
        
        Consider:
        - Direct topic matches (highest priority)
        - Related concepts and methodologies
        - Organisms studied
        - Research applications
        - Indirect relevance through related fields
        
        IMPORTANT: Use varied scores based on actual relevance:
        - 9-10: Direct, perfect match to query
        - 7-8: Strong relevance with clear connections
        - 5-6: Moderate relevance, some connections
        - 3-4: Weak relevance, tangential connections
        - 1-2: Minimal relevance
        - 0: No relevance
        
        Provide specific, actionable insights for researchers."""
        
        prompt = f"""
Research Query: {query}

Article to Analyze:
Title: {title}
Summary: {summary[:800]}
Organisms: {', '.join(organisms)}
Key Concepts: {', '.join(concepts[:10])}

Provide a JSON response with:
1. Relevance score (0-10, be precise and varied based on actual relevance)
2. 2-3 specific reasons for relevance
3. 2-3 research applications
4. How it contributes to the research goal

JSON format:
{{
    "relevance_score": <actual_score_based_on_relevance>,
    "relevance_reasons": ["reason1", "reason2", "reason3"],
    "research_applications": ["app1", "app2", "app3"],
    "contribution": "Specific contribution description"
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content
            
            try:
                return json.loads(result_text)
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    "relevance_score": 5.0,
                    "relevance_reasons": ["Article contains relevant content"],
                    "research_applications": ["General research application"],
                    "contribution": "Provides relevant information for the research query"
                }
                
        except Exception as e:
            print(f"Error analyzing article '{title}': {str(e)}")
            return None
    
    def find_articles_by_topic(self, topic: str, analyzed_articles: List[Dict], min_relevance: float = 0.7) -> List[Dict]:
        """
        Find articles related to a specific topic using semantic similarity.
        
        Args:
            topic: Research topic or keywords
            analyzed_articles: List of analyzed articles
            min_relevance: Minimum relevance threshold (0-1)
            
        Returns:
            List of relevant articles with relevance scores
        """
        system_prompt = """You are a research assistant analyzing article relevance to specific topics.
        For each article, determine how relevant it is to the given topic on a scale of 0.0 to 1.0.
        
        Consider:
        - Direct topic matches
        - Related concepts and methodologies
        - Organisms studied
        - Research applications
        - Indirect relevance through related fields
        
        Provide relevance scores and brief explanations."""
        
        relevant_articles = []
        
        for article in analyzed_articles:
            title = article.get('article_metadata', {}).get('title', '')
            summary = article.get('summary', {}).get('summary', '')
            organisms = article.get('organism_analysis', {}).get('organisms', [])
            concepts = article.get('knowledge_analysis', {}).get('key_concepts', [])
            
            if not title or not summary:
                continue
            
            prompt = f"""
Topic: {topic}

Article to analyze:
Title: {title}
Summary: {summary[:500]}
Organisms: {', '.join(organisms)}
Key Concepts: {', '.join(concepts[:5])}

Rate the relevance of this article to the topic on a scale of 0.0 to 1.0.
Provide only a JSON response:
{{
    "relevance_score": 0.8,
    "relevance_explanation": "Brief explanation of why this is relevant"
}}
"""
            
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=200,
                    temperature=0.1
                )
                
                result_text = response.choices[0].message.content
                
                try:
                    relevance_data = json.loads(result_text)
                    relevance_score = relevance_data.get('relevance_score', 0.0)
                    
                    if relevance_score >= min_relevance:
                        article_copy = article.copy()
                        article_copy['relevance_score'] = relevance_score
                        article_copy['relevance_explanation'] = relevance_data.get('relevance_explanation', '')
                        relevant_articles.append(article_copy)
                        
                except json.JSONDecodeError:
                    continue
                    
            except Exception as e:
                print(f"Error analyzing article relevance: {str(e)}")
                continue
        
        # Sort by relevance score
        relevant_articles.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return relevant_articles
