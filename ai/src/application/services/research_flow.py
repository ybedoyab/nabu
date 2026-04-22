"""
Research Flow Module for Nabu AI System.
Implements the complete scientific research workflow:
1. Research query → Article recommendations
2. Selected articles → Summaries + Suggested questions
3. Interactive chat with selected articles
"""

import json
import time
from typing import Dict, List, Any, Optional
from ...adapters.outbound.openai_client import OpenAIClient

class ResearchFlow:
    """Main class for handling the scientific research workflow."""
    
    def __init__(self, openai_client: OpenAIClient):
        self.openai_client = openai_client
    
    def get_research_recommendations(self, research_query: str, analyzed_articles: List[Dict], top_k: int = 5) -> Dict[str, Any]:
        """
        Step 1: Get article recommendations for a research query.
        
        Args:
            research_query: The scientist's research question/topic
            analyzed_articles: List of analyzed articles
            top_k: Number of recommendations to return
            
        Returns:
            JSON response for frontend with recommendations
        """
        print(f"Getting recommendations for: {research_query}")
        
        # Get recommendations using fast keyword matching (much faster!)
        recommendations = self.openai_client.recommend_articles_fast(
            research_query, 
            analyzed_articles, 
            top_k=top_k
        )
        
        # Format for frontend
        frontend_response = {
            "status": "success",
            "step": "recommendations",
            "research_query": research_query,
            "recommendations": [],
            "metadata": {
                "total_analyzed": recommendations.get('total_analyzed', 0),
                "relevant_found": recommendations.get('relevant_found', 0),
                "timestamp": time.time()
            }
        }
        
        # Format recommendations for frontend buttons
        for i, rec in enumerate(recommendations.get('recommendations', [])):
            frontend_response["recommendations"].append({
                "id": f"rec_{i+1}",
                "title": rec.get('article_title', ''),
                "relevance_score": rec.get('relevance_score', 0),
                "relevance_reasons": rec.get('relevance_reasons', []),
                "research_applications": rec.get('research_applications', []),
                "url": rec.get('url', ''),
                "organisms": rec.get('organisms', []),
                "key_concepts": rec.get('key_concepts', []),
                "selected": False  # For frontend state management
            })
        
        return frontend_response
    
    def generate_summaries_and_questions(self, selected_articles: List[Dict], research_query: str) -> Dict[str, Any]:
        """
        Step 2: Generate summaries and suggested questions for selected articles.
        
        Args:
            selected_articles: List of selected article recommendations
            research_query: Original research query for context
            
        Returns:
            JSON response with summaries and suggested questions
        """
        print(f"Generating summaries for {len(selected_articles)} selected articles")
        
        # Generate summaries for each selected article
        article_summaries = []
        all_suggested_questions = []
        
        for article in selected_articles:
            # Get full article data (you'll need to pass this from the main system)
            summary_data = self._generate_article_summary(article, research_query)
            article_summaries.append(summary_data)
            
            # Generate suggested questions for this article
            questions = self._generate_suggested_questions(article, research_query)
            all_suggested_questions.extend(questions)
        
        # Generate overall research insights
        research_insights = self._generate_research_insights(article_summaries, research_query)
        
        # Format for frontend
        frontend_response = {
            "status": "success",
            "step": "summaries_and_questions",
            "research_query": research_query,
            "article_summaries": article_summaries,
            "suggested_questions": all_suggested_questions,
            "research_insights": research_insights,
            "metadata": {
                "articles_count": len(selected_articles),
                "questions_generated": len(all_suggested_questions),
                "timestamp": time.time()
            }
        }
        
        return frontend_response
    
    def chat_with_selected_articles(self, user_question: str, selected_articles: List[Dict], 
                                  research_query: str, chat_history: List[Dict] = None) -> Dict[str, Any]:
        """
        Step 3: Interactive chat with selected articles.
        
        Args:
            user_question: User's question
            selected_articles: List of selected articles
            research_query: Original research query
            chat_history: Previous chat messages for context
            
        Returns:
            JSON response with AI answer and follow-up suggestions
        """
        print(f"Processing chat question: {user_question}")
        
        # Prepare context from selected articles
        article_context = self._prepare_article_context(selected_articles)
        
        # Get AI response
        ai_response = self.openai_client.chat_with_articles(
            user_question, 
            article_context
        )
        
        # Generate follow-up questions
        follow_up_questions = self._generate_follow_up_questions(
            user_question, ai_response, selected_articles, research_query
        )
        
        # Format chat response
        chat_message = {
            "id": f"msg_{int(time.time())}",
            "type": "user",
            "content": user_question,
            "timestamp": time.time()
        }
        
        ai_message = {
            "id": f"msg_{int(time.time()) + 1}",
            "type": "assistant",
            "content": ai_response,
            "follow_up_questions": follow_up_questions,
            "timestamp": time.time()
        }
        
        # Update chat history
        if chat_history is None:
            chat_history = []
        
        chat_history.extend([chat_message, ai_message])
        
        # Format for frontend
        frontend_response = {
            "status": "success",
            "step": "chat",
            "research_query": research_query,
            "chat_history": chat_history,
            "follow_up_questions": follow_up_questions,
            "metadata": {
                "articles_context": len(selected_articles),
                "timestamp": time.time()
            }
        }
        
        return frontend_response
    
    def _generate_article_summary(self, article: Dict, research_query: str) -> Dict[str, Any]:
        """Generate detailed summary for a single article."""
        title = article.get('title', '')
        
        # Create a focused summary prompt
        summary_prompt = f"""
        Based on the research query "{research_query}", provide a focused summary of this article:
        
        Article: {title}
        
        Please provide:
        1. Key findings relevant to the research query
        2. Methodology used
        3. Organisms/study subjects
        4. Implications for the research query
        5. Limitations or gaps
        
        Format as a clear, structured summary suitable for researchers.
        """
        
        try:
            response = self.openai_client.client.chat.completions.create(
                model=self.openai_client.model,
                messages=[
                    {"role": "system", "content": "You are a research assistant providing focused article summaries for scientists."},
                    {"role": "user", "content": summary_prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            summary_text = response.choices[0].message.content
            
            return {
                "article_id": article.get('id', ''),
                "title": title,
                "summary": summary_text,
                "url": article.get('url', ''),
                "relevance_score": article.get('relevance_score', 0),
                "organisms": article.get('organisms', []),
                "key_concepts": article.get('key_concepts', [])
            }
            
        except Exception as e:
            return {
                "article_id": article.get('id', ''),
                "title": title,
                "summary": f"Error generating summary: {str(e)}",
                "url": article.get('url', ''),
                "relevance_score": article.get('relevance_score', 0),
                "error": str(e)
            }
    
    def _generate_suggested_questions(self, article: Dict, research_query: str) -> List[Dict[str, Any]]:
        """Generate suggested questions for an article."""
        title = article.get('title', '')
        
        questions_prompt = f"""
        Based on the article "{title}" and the research query "{research_query}", 
        generate 3-5 specific questions that a researcher might want to explore further.
        
        Questions should be:
        - Specific to the article content
        - Relevant to the research query
        - Actionable for further research
        - Different types (methodological, conceptual, practical)
        
        Return as JSON array:
        [
            {{
                "question": "Question text",
                "type": "methodological|conceptual|practical|comparative",
                "focus": "What aspect this question explores"
            }}
        ]
        """
        
        try:
            response = self.openai_client.client.chat.completions.create(
                model=self.openai_client.model,
                messages=[
                    {"role": "system", "content": "You are a research assistant generating insightful questions for scientists."},
                    {"role": "user", "content": questions_prompt}
                ],
                max_tokens=800,
                temperature=0.4
            )
            
            questions_text = response.choices[0].message.content
            
            try:
                questions = json.loads(questions_text)
                # Add metadata to each question
                for i, q in enumerate(questions):
                    q["id"] = f"q_{int(time.time())}_{i}"
                    q["article_id"] = article.get('id', '')
                    q["article_title"] = title
                
                return questions
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return [{
                    "id": f"q_{int(time.time())}_0",
                    "question": "What are the key findings of this study?",
                    "type": "conceptual",
                    "focus": "Main research outcomes",
                    "article_id": article.get('id', ''),
                    "article_title": title
                }]
                
        except Exception as e:
            return [{
                "id": f"q_{int(time.time())}_0",
                "question": f"Error generating questions: {str(e)}",
                "type": "error",
                "focus": "System error",
                "article_id": article.get('id', ''),
                "article_title": title
            }]
    
    def _generate_research_insights(self, article_summaries: List[Dict], research_query: str) -> Dict[str, Any]:
        """Generate overall research insights from selected articles."""
        insights_prompt = f"""
        Based on the research query "{research_query}" and the following article summaries, 
        provide overall research insights:
        
        Article Summaries:
        {json.dumps([s.get('summary', '') for s in article_summaries], indent=2)}
        
        Please provide:
        1. Key themes across articles
        2. Research gaps identified
        3. Potential research directions
        4. Methodological considerations
        5. Practical applications
        
        Format as structured insights for researchers.
        """
        
        try:
            response = self.openai_client.client.chat.completions.create(
                model=self.openai_client.model,
                messages=[
                    {"role": "system", "content": "You are a research advisor providing comprehensive insights from multiple studies."},
                    {"role": "user", "content": insights_prompt}
                ],
                max_tokens=1500,
                temperature=0.3
            )
            
            insights_text = response.choices[0].message.content
            
            return {
                "overall_insights": insights_text,
                "articles_analyzed": len(article_summaries),
                "research_query": research_query
            }
            
        except Exception as e:
            return {
                "overall_insights": f"Error generating insights: {str(e)}",
                "articles_analyzed": len(article_summaries),
                "research_query": research_query,
                "error": str(e)
            }
    
    def _prepare_article_context(self, selected_articles: List[Dict]) -> List[Dict]:
        """Prepare article context for chat."""
        context = []
        for article in selected_articles:
            context.append({
                "title": article.get('title', ''),
                "summary": article.get('summary', ''),
                "organisms": article.get('organisms', []),
                "key_concepts": article.get('key_concepts', []),
                "url": article.get('url', '')
            })
        return context
    
    def _generate_follow_up_questions(self, user_question: str, ai_response: str, 
                                    selected_articles: List[Dict], research_query: str) -> List[Dict[str, Any]]:
        """Generate follow-up questions based on the conversation."""
        follow_up_prompt = f"""
        Based on this conversation about "{research_query}":
        
        User Question: {user_question}
        AI Response: {ai_response[:500]}...
        
        Generate 3-4 follow-up questions that would help the researcher explore this topic further.
        Questions should be:
        - Natural follow-ups to the current discussion
        - Specific and actionable
        - Relevant to the research query
        - Different from the original question
        
        Return as JSON array:
        [
            {{
                "question": "Follow-up question text",
                "type": "clarification|deeper_analysis|comparison|application"
            }}
        ]
        """
        
        try:
            response = self.openai_client.client.chat.completions.create(
                model=self.openai_client.model,
                messages=[
                    {"role": "system", "content": "You are a research assistant generating helpful follow-up questions."},
                    {"role": "user", "content": follow_up_prompt}
                ],
                max_tokens=600,
                temperature=0.4
            )
            
            questions_text = response.choices[0].message.content
            
            try:
                questions = json.loads(questions_text)
                # Add IDs to each question
                for i, q in enumerate(questions):
                    q["id"] = f"followup_{int(time.time())}_{i}"
                
                return questions
            except json.JSONDecodeError:
                return []
                
        except Exception as e:
            return []
