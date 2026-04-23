"""
Research Flow Module for Nabu AI System.
Implements the complete scientific research workflow:
1. Research query → Article recommendations
2. Selected articles → Summaries + Suggested questions
3. Interactive chat with selected articles
"""

import json
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional
from ...adapters.outbound.openai_client import OpenAIClient

logger = logging.getLogger(__name__)

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
        logger.info("ResearchFlow recommendations started (query=%r, candidates=%d)", research_query, len(analyzed_articles))
        
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
                "source": rec.get('source', '') or '',
                "organisms": rec.get('organisms', []),
                "key_concepts": rec.get('key_concepts', []),
                "selected": False  # For frontend state management
            })
        
        logger.info(
            "ResearchFlow recommendations completed (query=%r, returned=%d, relevant_found=%d)",
            research_query,
            len(frontend_response["recommendations"]),
            frontend_response["metadata"]["relevant_found"],
        )
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
        logger.info(
            "ResearchFlow summaries started (query=%r, selected_articles=%d)",
            research_query,
            len(selected_articles),
        )
        
        # Run summary + questions for every article in parallel (2N OpenAI calls concurrently)
        article_summaries: List[Optional[Dict[str, Any]]] = [None] * len(selected_articles)
        questions_per_article: List[List[Dict[str, Any]]] = [[] for _ in selected_articles]

        parallel_started_at = time.perf_counter()
        max_workers = max(1, min(len(selected_articles) * 2, 10))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map: Dict[Any, tuple] = {}
            for idx, article in enumerate(selected_articles):
                future_map[executor.submit(self._generate_article_summary, article, research_query)] = ("summary", idx)
                future_map[executor.submit(self._generate_suggested_questions, article, research_query)] = ("questions", idx)

            for future in as_completed(future_map):
                kind, idx = future_map[future]
                try:
                    result = future.result()
                except Exception as exc:
                    logger.exception("Parallel %s task failed for article %d: %s", kind, idx, exc)
                    result = None

                if kind == "summary":
                    article_summaries[idx] = result or {
                        "article_id": selected_articles[idx].get("id", ""),
                        "title": selected_articles[idx].get("title", ""),
                        "summary": "Error generating summary",
                        "url": selected_articles[idx].get("url", ""),
                        "relevance_score": selected_articles[idx].get("relevance_score", 0),
                    }
                else:
                    questions_per_article[idx] = result or []

        all_suggested_questions = [q for qs in questions_per_article for q in qs]
        all_suggested_questions = self._normalize_questions(
            all_suggested_questions,
            selected_articles=selected_articles,
            research_query=research_query,
        )
        logger.info(
            "ResearchFlow parallel per-article generation finished in %.2fs",
            time.perf_counter() - parallel_started_at,
        )

        # Generate overall research insights (depends on summaries, so runs after)
        research_insights = self._generate_research_insights(article_summaries, research_query)
        combined_summary = self._generate_combined_summary(article_summaries, research_query)
        if not combined_summary.strip():
            combined_summary = research_insights.get("overall_insights", "").strip()
        
        # Format for frontend
        frontend_response = {
            "status": "success",
            "step": "summaries_and_questions",
            "research_query": research_query,
            "article_summaries": article_summaries,
            "suggested_questions": all_suggested_questions,
            "combined_summary": combined_summary,
            "research_insights": research_insights,
            "metadata": {
                "articles_count": len(selected_articles),
                "questions_generated": len(all_suggested_questions),
                "timestamp": time.time()
            }
        }
        
        logger.info(
            "ResearchFlow summaries completed (query=%r, summaries=%d, questions=%d)",
            research_query,
            len(frontend_response["article_summaries"]),
            len(frontend_response["suggested_questions"]),
        )
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
        logger.info(
            "ResearchFlow chat started (query=%r, selected_articles=%d, question_len=%d)",
            research_query,
            len(selected_articles),
            len(user_question),
        )
        
        # Prepare context from selected articles
        article_context = self._prepare_article_context(selected_articles)
        
        # Get AI response and follow-ups in one call
        ai_result = self.openai_client.chat_with_articles(
            query=user_question, 
            article_context=article_context,
            chat_history=chat_history,
            research_query=research_query
        )
        
        ai_response = ai_result.get("response", "Error generating response.")
        follow_up_questions = ai_result.get("follow_up_questions", [])
        for i, q in enumerate(follow_up_questions):
            if "id" not in q:
                q["id"] = f"followup_{int(time.time())}_{i}"
        
        # Format chat response
        chat_message = {
            "id": f"msg_{int(time.time())}",
            "role": "user",
            "content": user_question,
            "timestamp": time.time()
        }
        
        ai_message = {
            "id": f"msg_{int(time.time()) + 1}",
            "role": "assistant",
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
        
        logger.info(
            "ResearchFlow chat completed (query=%r, history_size=%d, follow_ups=%d)",
            research_query,
            len(frontend_response["chat_history"]),
            len(frontend_response["follow_up_questions"]),
        )
        return frontend_response
    
    def _generate_article_summary(self, article: Dict, research_query: str) -> Dict[str, Any]:
        """Generate detailed summary for a single article."""
        title = article.get('title', '')
        abstract = article.get('abstract', 'No abstract available.')
        
        # Create a focused summary prompt
        summary_prompt = f"""
        Based on the research query "{research_query}", provide a focused summary of this article:
        
        Article: {title}
        Abstract: {abstract}
        
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
                    {"role": "system", "content": "You are a research assistant providing focused article summaries for scientists. Always respond in Spanish."},
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
        Basado en el artículo "{title}" y la consulta de investigación "{research_query}",
        genera entre 3 y 5 preguntas específicas que un investigador podría explorar.

        Requisitos:
        - Deben estar escritas en español.
        - Deben ser variadas y NO repetidas entre sí.
        - Deben ser accionables y relevantes para la consulta.
        - Usa tipos variados: methodological, conceptual, practical, comparative.

        Responde SOLO como arreglo JSON con este formato:
        [
            {{
                "question": "Pregunta en español",
                "type": "methodological|conceptual|practical|comparative",
                "focus": "Enfoque breve en español"
            }}
        ]
        """
        
        try:
            response = self.openai_client.client.chat.completions.create(
                model=self.openai_client.model,
                messages=[
                    {"role": "system", "content": "You are a research assistant generating insightful questions for scientists. Write the 'question' and 'focus' fields in Spanish. Keep the 'type' field values in English (methodological|conceptual|practical|comparative)."},
                    {"role": "user", "content": questions_prompt}
                ],
                max_tokens=800,
                temperature=0.4
            )
            
            questions_text = response.choices[0].message.content
            
            try:
                parsed = json.loads(questions_text)
                if isinstance(parsed, dict):
                    questions = parsed.get("questions") or next(
                        (v for v in parsed.values() if isinstance(v, list)), []
                    )
                else:
                    questions = parsed

                normalized = []
                for i, q in enumerate(questions):
                    if not isinstance(q, dict):
                        continue
                    normalized.append({
                        "id": f"q_{int(time.time())}_{i}",
                        "question": q.get("question", ""),
                        "type": q.get("type", "conceptual"),
                        "focus": q.get("focus", ""),
                        "article_id": article.get("id", ""),
                        "article_title": title,
                    })
                return normalized
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return [{
                    "id": f"q_{int(time.time())}_0",
                    "question": f"¿Cuáles son los hallazgos clave de \"{title}\" para {research_query}?",
                    "type": "conceptual",
                    "focus": "Resultados principales del estudio",
                    "article_id": article.get('id', ''),
                    "article_title": title
                }]
                
        except Exception as e:
            return [{
                "id": f"q_{int(time.time())}_0",
                "question": f"¿Qué línea de investigación priorizarías a partir de \"{title}\"?",
                "type": "practical",
                "focus": "Priorización de próximos pasos",
                "article_id": article.get('id', ''),
                "article_title": title
            }]

    def _normalize_questions(
        self,
        questions: List[Dict[str, Any]],
        selected_articles: List[Dict[str, Any]],
        research_query: str,
    ) -> List[Dict[str, Any]]:
        """Remove duplicates, enforce Spanish-oriented defaults, and ensure variety."""
        seen = set()
        normalized: List[Dict[str, Any]] = []

        for idx, q in enumerate(questions):
            question_text = (q.get("question", "") or "").strip()
            if not question_text:
                continue

            key = " ".join(question_text.lower().split())
            if key in seen:
                continue
            seen.add(key)

            qtype = (q.get("type", "conceptual") or "conceptual").lower()
            if qtype not in {"methodological", "conceptual", "practical", "comparative"}:
                qtype = "conceptual"

            focus = (q.get("focus", "") or "").strip()
            if not focus:
                focus = "Análisis del tema de investigación"

            normalized.append({
                "id": q.get("id") or f"q_{int(time.time())}_{idx}",
                "question": question_text,
                "type": qtype,
                "focus": focus,
                "article_id": q.get("article_id"),
                "article_title": q.get("article_title"),
            })

        if len(normalized) < 5:
            seed_title = selected_articles[0].get("title", "el artículo principal") if selected_articles else "el artículo"
            fallbacks = [
                f"¿Qué evidencia adicional se necesita para validar los resultados sobre {research_query}?",
                f"¿Cómo se compara {seed_title} con otros estudios recientes sobre {research_query}?",
                f"¿Qué limitaciones metodológicas podrían afectar la generalización de estos hallazgos?",
                f"¿Qué experimento de seguimiento propondrías para profundizar en {research_query}?",
                f"¿Qué implicaciones prácticas tienen estos resultados en contextos reales?",
            ]
            fallback_types = ["conceptual", "comparative", "methodological", "practical", "practical"]

            for i, text in enumerate(fallbacks):
                key = " ".join(text.lower().split())
                if key in seen:
                    continue
                seen.add(key)
                normalized.append({
                    "id": f"q_fb_{int(time.time())}_{i}",
                    "question": text,
                    "type": fallback_types[i],
                    "focus": "Pregunta de apoyo para profundizar la investigación",
                    "article_id": selected_articles[0].get("id", "") if selected_articles else "",
                    "article_title": selected_articles[0].get("title", "") if selected_articles else "",
                })
                if len(normalized) >= 6:
                    break

        return normalized[:8]

    def _generate_combined_summary(self, article_summaries: List[Dict], research_query: str) -> str:
        """Generate a general synthesis and comparison across selected articles."""
        comparison_prompt = f"""
        Consulta de investigación: "{research_query}"

        A partir de los siguientes resúmenes de artículos, redacta una síntesis general y comparación.

        Resúmenes:
        {json.dumps([{
            "title": s.get("title", ""),
            "summary": s.get("summary", "")
        } for s in article_summaries], ensure_ascii=False, indent=2)}

        Requisitos de salida (en español):
        1) Síntesis general (idea central conjunta)
        2) Coincidencias entre estudios
        3) Diferencias o contradicciones
        4) Implicaciones prácticas
        5) Conclusión breve para toma de decisiones
        """

        try:
            response = self.openai_client.client.chat.completions.create(
                model=self.openai_client.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Eres un analista de investigación científica. "
                            "Produce comparaciones claras, accionables y en español."
                        ),
                    },
                    {"role": "user", "content": comparison_prompt},
                ],
                max_tokens=1200,
                temperature=0.3,
            )
            return (response.choices[0].message.content or "").strip()
        except Exception as exc:
            logger.exception("Failed to generate combined summary: %s", exc)
            return ""
    
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
                    {"role": "system", "content": "You are a research advisor providing comprehensive insights from multiple studies. Always respond in Spanish."},
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
                "summary": article.get('abstract', article.get('summary', '')),
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
