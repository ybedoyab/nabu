"""
Command Line Interface for the Research Flow System.
Provides interactive commands for the complete scientific research workflow.
"""

import argparse
import json
import os
from typing import List, Dict, Any
from ...infrastructure.config import Config, validate_config, setup_directories
from ...adapters.outbound.openai_client import OpenAIClient
from ...application.services.research_flow import ResearchFlow

def main():
    """Main entry point for the research flow CLI."""
    parser = argparse.ArgumentParser(description="Nabu Research Flow System")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Research flow command
    research_parser = subparsers.add_parser('research', help='Complete research workflow')
    research_parser.add_argument('--query', required=True, help='Research query or topic')
    research_parser.add_argument('--data-file', default='ai_analysis.json', help='File with analyzed articles')
    research_parser.add_argument('--top-k', type=int, default=5, help='Number of article recommendations')
    research_parser.add_argument('--output-dir', default='research_output', help='Output directory for research results')
    
    # Interactive research session
    interactive_parser = subparsers.add_parser('interactive', help='Interactive research session')
    interactive_parser.add_argument('--data-file', default='ai_analysis.json', help='File with analyzed articles')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Validate configuration
    if not validate_config():
        print("Configuration validation failed. Please check your OpenAI API key.")
        return
    
    # Setup directories
    setup_directories()
    
    # Execute command
    try:
        if args.command == 'research':
            run_research_workflow(args)
        elif args.command == 'interactive':
            run_interactive_session(args)
        else:
            print(f"Unknown command: {args.command}")
            parser.print_help()
    except Exception as e:
        print(f"Error executing command: {str(e)}")
        return

def run_research_workflow(args):
    """Run the complete research workflow."""
    print("Nabu Research Workflow")
    print("=" * 50)
    
    # Load analyzed articles
    data_path = os.path.join(Config.OUTPUT_DIR, args.data_file)
    if not os.path.exists(data_path):
        print(f"Data file not found: {data_path}")
        print("Run 'python main.py analyze' first to create analyzed articles.")
        return
    
    with open(data_path, 'r', encoding='utf-8') as f:
        analyzed_articles = json.load(f)
    
    print(f"Loaded {len(analyzed_articles)} analyzed articles")
    print(f"Research Query: {args.query}")
    
    # Initialize components
    openai_client = OpenAIClient()
    research_flow = ResearchFlow(openai_client)
    
    # Step 1: Get recommendations
    print("\nStep 1: Getting article recommendations...")
    recommendations_response = research_flow.get_research_recommendations(
        args.query, analyzed_articles, args.top_k
    )
    
    # Save recommendations
    output_dir = os.path.join(Config.OUTPUT_DIR, args.output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    recommendations_file = os.path.join(output_dir, "recommendations.json")
    with open(recommendations_file, 'w', encoding='utf-8') as f:
        json.dump(recommendations_response, f, indent=2, ensure_ascii=False)
    
    print(f"Recommendations saved to: {recommendations_file}")
    
    # Display recommendations
    print(f"\nTop {args.top_k} Article Recommendations:")
    print("-" * 50)
    for i, rec in enumerate(recommendations_response['recommendations'], 1):
        print(f"{i}. {rec['title']}")
        print(f"   Relevance Score: {rec['relevance_score']}/10")
        print(f"   Key Reasons: {', '.join(rec['relevance_reasons'][:2])}")
        print()
    
    # For demo purposes, select top 2 articles
    selected_articles = recommendations_response['recommendations'][:2]
    print(f"Auto-selecting top 2 articles for demo...")
    
    # Step 2: Generate summaries and questions
    print("\nStep 2: Generating summaries and suggested questions...")
    summaries_response = research_flow.generate_summaries_and_questions(
        selected_articles, args.query
    )
    
    # Save summaries
    summaries_file = os.path.join(output_dir, "summaries_and_questions.json")
    with open(summaries_file, 'w', encoding='utf-8') as f:
        json.dump(summaries_response, f, indent=2, ensure_ascii=False)
    
    print(f"Summaries and questions saved to: {summaries_file}")
    
    # Display summaries
    print("\nArticle Summaries:")
    print("-" * 50)
    for summary in summaries_response['article_summaries']:
        print(f"\nTitle: {summary['title']}")
        print(f"Summary: {summary['summary'][:200]}...")
    
    # Display suggested questions
    print(f"\nSuggested Questions ({len(summaries_response['suggested_questions'])}):")
    print("-" * 50)
    for i, question in enumerate(summaries_response['suggested_questions'][:5], 1):
        print(f"{i}. {question['question']}")
        print(f"   Type: {question['type']} | Focus: {question['focus']}")
        print()
    
    # Step 3: Demo chat
    print("\nStep 3: Demo chat interaction...")
    demo_question = "What are the main challenges mentioned in these studies?"
    
    chat_response = research_flow.chat_with_selected_articles(
        demo_question, selected_articles, args.query
    )
    
    # Save chat
    chat_file = os.path.join(output_dir, "chat_demo.json")
    with open(chat_file, 'w', encoding='utf-8') as f:
        json.dump(chat_response, f, indent=2, ensure_ascii=False)
    
    print(f"Chat demo saved to: {chat_file}")
    
    print(f"\nDemo Question: {demo_question}")
    print(f"AI Response: {chat_response['chat_history'][-1]['content'][:300]}...")
    
    print(f"\nWorkflow complete! Check {output_dir} for all results.")

def run_interactive_session(args):
    """Run an interactive research session."""
    print("Nabu Interactive Research Session")
    print("=" * 50)
    print("Type 'quit' to exit at any time.")
    
    # Load analyzed articles
    data_path = os.path.join(Config.OUTPUT_DIR, args.data_file)
    if not os.path.exists(data_path):
        print(f"Data file not found: {data_path}")
        return
    
    with open(data_path, 'r', encoding='utf-8') as f:
        analyzed_articles = json.load(f)
    
    print(f"Loaded {len(analyzed_articles)} analyzed articles")
    
    # Initialize components
    openai_client = OpenAIClient()
    research_flow = ResearchFlow(openai_client)
    
    # Get research query
    research_query = input("\nWhat is your research question/topic? ").strip()
    if not research_query or research_query.lower() == 'quit':
        return
    
    # Step 1: Get recommendations
    print(f"\nGetting recommendations for: {research_query}")
    recommendations_response = research_flow.get_research_recommendations(
        research_query, analyzed_articles, 5
    )
    
    print(f"\nTop 5 Recommendations:")
    for i, rec in enumerate(recommendations_response['recommendations'], 1):
        print(f"{i}. {rec['title']} (Score: {rec['relevance_score']}/10)")
    
    # Select articles
    print(f"\nWhich articles would you like to explore? (Enter numbers separated by commas, e.g., 1,3,5)")
    selection_input = input("Selection: ").strip()
    
    if selection_input.lower() == 'quit':
        return
    
    try:
        selected_indices = [int(x.strip()) - 1 for x in selection_input.split(',')]
        selected_articles = [recommendations_response['recommendations'][i] for i in selected_indices]
    except (ValueError, IndexError):
        print("Invalid selection. Using first 2 articles.")
        selected_articles = recommendations_response['recommendations'][:2]
    
    print(f"\nSelected {len(selected_articles)} articles for analysis.")
    
    # Step 2: Generate summaries and questions
    print("\nGenerating summaries and suggested questions...")
    summaries_response = research_flow.generate_summaries_and_questions(
        selected_articles, research_query
    )
    
    print(f"\nGenerated {len(summaries_response['suggested_questions'])} suggested questions.")
    
    # Step 3: Interactive chat
    print("\nInteractive Chat Mode")
    print("You can ask questions about the selected articles or use suggested questions.")
    print("Type 'suggestions' to see suggested questions, 'quit' to exit.")
    
    chat_history = []
    
    while True:
        user_input = input("\nYour question: ").strip()
        
        if user_input.lower() == 'quit':
            break
        elif user_input.lower() == 'suggestions':
            print("\nSuggested Questions:")
            for i, q in enumerate(summaries_response['suggested_questions'][:5], 1):
                print(f"{i}. {q['question']}")
            continue
        elif not user_input:
            continue
        
        # Get AI response
        chat_response = research_flow.chat_with_selected_articles(
            user_input, selected_articles, research_query, chat_history
        )
        
        chat_history = chat_response['chat_history']
        
        print(f"\nAI Response: {chat_response['chat_history'][-1]['content']}")
        
        # Show follow-up questions
        if chat_response['follow_up_questions']:
            print(f"\nFollow-up Questions:")
            for i, q in enumerate(chat_response['follow_up_questions'], 1):
                print(f"{i}. {q['question']}")
    
    print("\nResearch session ended. Thank you!")

if __name__ == "__main__":
    main()
