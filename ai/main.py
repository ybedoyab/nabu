"""
Main entry point for the research AI processing system.
Provides CLI interface for processing publications and interacting with the AI system.
"""

import argparse
import json
import os
import sys
from typing import List, Dict, Any

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.infrastructure.config import Config, validate_config, setup_directories
from src.adapters.outbound.data_processor import DataProcessor
from src.adapters.outbound.openai_client import OpenAIClient

def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="Nabu AI Processing System")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Process data command
    process_parser = subparsers.add_parser('process', help='Process publications')
    process_parser.add_argument('--limit', type=int, help='Limit number of articles to process')
    process_parser.add_argument('--batch-size', type=int, default=10, help='Batch size for processing')
    process_parser.add_argument('--skip-scraping', action='store_true', help='Skip scraping, use existing data')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze processed articles with AI')
    analyze_parser.add_argument('--input-file', default='processed_articles.json', help='Input file with processed articles')
    analyze_parser.add_argument('--output-file', default='ai_analysis.json', help='Output file for AI analysis')
    
    # Chat command
    chat_parser = subparsers.add_parser('chat', help='Interactive chat with the AI about articles')
    chat_parser.add_argument('--data-file', default='ai_analysis.json', help='File with analyzed articles')
    
    # Extract organisms command
    organisms_parser = subparsers.add_parser('extract-organisms', help='Extract organism information from articles')
    organisms_parser.add_argument('--input-file', default='processed_articles.json', help='Input file with processed articles')
    organisms_parser.add_argument('--output-file', default='organisms_analysis.json', help='Output file for organism analysis')
    
    # Recommend articles command
    recommend_parser = subparsers.add_parser('recommend', help='Recommend articles for a specific research topic')
    recommend_parser.add_argument('--query', required=True, help='Research query or topic')
    recommend_parser.add_argument('--data-file', default='ai_analysis.json', help='File with analyzed articles')
    recommend_parser.add_argument('--top-k', type=int, default=5, help='Number of top articles to recommend')
    recommend_parser.add_argument('--output-file', default='recommendations.json', help='Output file for recommendations')
    
    # Checkpoint management commands
    checkpoint_parser = subparsers.add_parser('checkpoint', help='Manage analysis checkpoints')
    checkpoint_subparsers = checkpoint_parser.add_subparsers(dest='checkpoint_action', help='Checkpoint actions')
    
    # Show checkpoint status
    checkpoint_subparsers.add_parser('status', help='Show checkpoint status')
    
    # Clear checkpoint
    clear_parser = checkpoint_subparsers.add_parser('clear', help='Clear analysis checkpoint')
    clear_parser.add_argument('--force', action='store_true', help='Force clear without confirmation')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Validate configuration
    if not validate_config():
        sys.exit(1)
    
    # Setup directories
    setup_directories()
    
    # Execute command
    try:
        if args.command == 'process':
            process_articles(args)
        elif args.command == 'analyze':
            analyze_articles(args)
        elif args.command == 'chat':
            chat_with_articles(args)
        elif args.command == 'extract-organisms':
            extract_organisms(args)
        elif args.command == 'recommend':
            recommend_articles(args)
        elif args.command == 'checkpoint':
            handle_checkpoint_command(args)
        else:
            print(f"Unknown command: {args.command}")
            parser.print_help()
    except Exception as e:
        print(f"Error executing command: {str(e)}")
        sys.exit(1)

def process_articles(args):
    """Process publications from CSV."""
    print("🚀 Starting publication data processing")
    
    processor = DataProcessor()
    
    if args.skip_scraping:
        print("📁 Loading existing processed data...")
        try:
            articles = processor.load_processed_data()
            print(f"✅ Loaded {len(articles)} previously processed articles")
        except FileNotFoundError:
            print("❌ No existing processed data found. Run without --skip-scraping first.")
            return
    else:
        # Update config if limit specified
        if args.limit:
            Config.MAX_ARTICLES_TO_PROCESS = args.limit
        
        if args.batch_size:
            Config.BATCH_SIZE = args.batch_size
        
        print("📊 Loading and processing publications...")
        df, articles = processor.load_and_process_data()
        
        # Save processed data
        processor.save_processed_data(articles)
    
    print(f"✅ Processing complete! Processed {len(articles)} articles")

def analyze_articles(args):
    """Analyze processed articles with OpenAI."""
    print("🤖 Starting AI analysis of publications")
    print("💡 Tip: Press Ctrl+C at any time to stop and save progress")
    print("🔄 To resume after stopping, run the same command again")
    
    # Load processed articles
    input_path = os.path.join(Config.OUTPUT_DIR, args.input_file)
    if not os.path.exists(input_path):
        print(f"❌ Input file not found: {input_path}")
        print("Run 'process' command first to create processed articles.")
        return
    
    with open(input_path, 'r', encoding='utf-8') as f:
        articles = json.load(f)
    
    print(f"📚 Analyzing {len(articles)} articles with OpenAI...")
    
    # Check for existing checkpoint
    checkpoint_path = os.path.join(Config.OUTPUT_DIR, "analysis_checkpoint.json")
    if os.path.exists(checkpoint_path):
        print(f"🔄 Found existing checkpoint. Will resume from where it left off.")
    
    # Initialize OpenAI client
    openai_client = OpenAIClient()
    
    # Process articles with AI (now with checkpoint support)
    analyzed_articles = openai_client.process_articles_batch(
        articles, 
        checkpoint_file="analysis_checkpoint.json",
        output_file=args.output_file
    )
    
    # Analysis results are already saved by the checkpoint system
    output_path = os.path.join(Config.OUTPUT_DIR, args.output_file)
    print(f"✅ AI analysis complete! Results saved to {output_path}")

def chat_with_articles(args):
    """Interactive chat interface."""
    print("💬 Nabu AI chat interface")
    print("Ask questions about the research articles. Type 'quit' to exit.")
    
    # Load analyzed articles
    data_path = os.path.join(Config.OUTPUT_DIR, args.data_file)
    if not os.path.exists(data_path):
        print(f"❌ Data file not found: {data_path}")
        print("Run 'analyze' command first to create analyzed articles.")
        return
    
    with open(data_path, 'r', encoding='utf-8') as f:
        analyzed_articles = json.load(f)
    
    # Initialize OpenAI client
    openai_client = OpenAIClient()
    
    print(f"📚 Loaded {len(analyzed_articles)} analyzed articles")
    print("\nExample questions:")
    print("- What are the main effects of long-context attention on model quality?")
    print("- Which benchmark datasets are most relevant to this topic?")
    print("- What are the key implementation challenges for production adoption?")
    print("- Summarize the findings about robustness and evaluation")
    
    while True:
        try:
            query = input("\n🔬 Your question: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not query:
                continue
            
            print("🤔 Thinking...")
            
            # Find relevant articles for context
            relevant_articles = find_relevant_articles(query, analyzed_articles)
            
            # Get AI response
            response = openai_client.chat_with_articles(query, relevant_articles)
            
            print(f"\n🤖 AI Response:\n{response}")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")

def extract_organisms(args):
    """Extract organism information from articles."""
    print("🧬 Extracting Organism Information")
    
    # Load processed articles
    input_path = os.path.join(Config.OUTPUT_DIR, args.input_file)
    if not os.path.exists(input_path):
        print(f"❌ Input file not found: {input_path}")
        return
    
    with open(input_path, 'r', encoding='utf-8') as f:
        articles = json.load(f)
    
    print(f"🔍 Extracting organisms from {len(articles)} articles...")
    
    # Initialize OpenAI client
    openai_client = OpenAIClient()
    
    organism_data = []
    for article in articles:
        if 'error' not in article:
            organism_info = openai_client.extract_organisms(
                article.get('title', ''),
                article.get('full_text', '') or article.get('abstract', '')
            )
            organism_data.append({
                'title': article.get('title', ''),
                'url': article.get('url', ''),
                'organism_analysis': organism_info
            })
    
    # Save organism analysis
    output_path = os.path.join(Config.OUTPUT_DIR, args.output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(organism_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Organism extraction complete! Results saved to {output_path}")

def recommend_articles(args):
    """Recommend articles for a specific research topic."""
    print("Nabu Article Recommendation System")
    
    # Load analyzed articles
    data_path = os.path.join(Config.OUTPUT_DIR, args.data_file)
    if not os.path.exists(data_path):
        print(f"❌ Data file not found: {data_path}")
        print("Run 'analyze' command first to create analyzed articles.")
        return
    
    with open(data_path, 'r', encoding='utf-8') as f:
        analyzed_articles = json.load(f)
    
    print(f"Loaded {len(analyzed_articles)} analyzed articles")
    print(f"Research Query: {args.query}")
    print("Analyzing and recommending articles...")
    
    # Initialize OpenAI client
    openai_client = OpenAIClient()
    
    # Get recommendations using individual analysis for better precision
    recommendations = openai_client.recommend_articles_individual_analysis(
        args.query, 
        analyzed_articles, 
        top_k=args.top_k
    )
    
    # Display results
    print(f"\nTop {args.top_k} Article Recommendations for: '{args.query}'")
    print("=" * 80)
    
    # Show analysis stats
    if 'total_analyzed' in recommendations:
        print(f"Analysis Statistics:")
        print(f"   - Total articles analyzed: {recommendations['total_analyzed']}")
        print(f"   - Relevant articles found: {recommendations['relevant_found']}")
        print(f"   - Analysis method: {recommendations.get('analysis_method', 'standard')}")
        print("-" * 80)
    
    if 'recommendations' in recommendations and recommendations['recommendations']:
        for i, rec in enumerate(recommendations['recommendations'], 1):
            print(f"\n{i}. {rec.get('article_title', 'Unknown Title')}")
            print(f"   Relevance Score: {rec.get('relevance_score', 'N/A')}/10")
            print(f"   Key Reasons:")
            for reason in rec.get('relevance_reasons', []):
                print(f"      - {reason}")
            print(f"   Research Applications:")
            for app in rec.get('research_applications', []):
                print(f"      - {app}")
            print(f"   Contribution: {rec.get('contribution', 'N/A')}")
            
            # Additional info if available
            if 'url' in rec and rec['url']:
                print(f"   URL: {rec['url']}")
            if 'organisms' in rec and rec['organisms']:
                print(f"   Organisms: {', '.join(rec['organisms'])}")
            if 'key_concepts' in rec and rec['key_concepts']:
                print(f"   Key Concepts: {', '.join(rec['key_concepts'][:3])}")
            
            print("-" * 80)
    else:
        print("No recommendations found. Try a different query or check if articles are available.")
        if 'error' in recommendations:
            print(f"Error: {recommendations['error']}")
        if 'raw_response' in recommendations:
            print(f"Raw response: {recommendations['raw_response'][:500]}...")
    
    # Display additional insights
    if 'research_insights' in recommendations:
        print(f"\nResearch Insights:")
        print(f"   {recommendations['research_insights']}")
    
    if 'knowledge_gaps' in recommendations and recommendations['knowledge_gaps']:
        print(f"\nKnowledge Gaps:")
        for gap in recommendations['knowledge_gaps']:
            print(f"   - {gap}")
    
    if 'suggested_follow_up' in recommendations:
        print(f"\nSuggested Follow-up Research:")
        print(f"   {recommendations['suggested_follow_up']}")
    
    # Save recommendations
    output_path = os.path.join(Config.OUTPUT_DIR, args.output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(recommendations, f, indent=2, ensure_ascii=False)
    
    print(f"\nRecommendations saved to: {output_path}")

def find_relevant_articles(query: str, articles: List[Dict]) -> List[Dict]:
    """Find articles relevant to the query using simple keyword matching."""
    query_lower = query.lower()
    relevant = []
    
    for article in articles:
        title = article.get('article_metadata', {}).get('title', '').lower()
        summary = article.get('summary', {}).get('summary', '').lower()
        
        # Simple relevance scoring
        score = 0
        if any(word in title for word in query_lower.split()):
            score += 2
        if any(word in summary for word in query_lower.split()):
            score += 1
        
        if score > 0:
            relevant.append((score, article))
    
    # Sort by relevance and return top articles
    relevant.sort(key=lambda x: x[0], reverse=True)
    return [article for score, article in relevant[:5]]

def handle_checkpoint_command(args):
    """Handle checkpoint management commands."""
    if args.checkpoint_action == 'status':
        show_checkpoint_status()
    elif args.checkpoint_action == 'clear':
        clear_checkpoint(args)
    else:
        print("Available checkpoint actions: status, clear")
        print("Use 'checkpoint status' to see current checkpoint information")
        print("Use 'checkpoint clear' to clear the checkpoint and start fresh")

def show_checkpoint_status():
    """Show current checkpoint status."""
    import time
    from datetime import datetime
    
    checkpoint_path = os.path.join(Config.OUTPUT_DIR, "analysis_checkpoint.json")
    output_path = os.path.join(Config.OUTPUT_DIR, "ai_analysis.json")
    
    print("📊 Checkpoint Status")
    print("=" * 40)
    
    # Check if analysis is complete
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                analyzed_data = json.load(f)
            print(f"✅ Analysis Complete: {len(analyzed_data)} articles analyzed")
            print(f"📁 Output file: {output_path}")
            
            # Check if checkpoint still exists (should be cleaned up)
            if os.path.exists(checkpoint_path):
                print("⚠️ Warning: Checkpoint file still exists (should be cleaned up)")
            else:
                print("✅ Checkpoint file properly cleaned up")
        except Exception as e:
            print(f"❌ Error reading analysis file: {str(e)}")
    
    # Check checkpoint status
    elif os.path.exists(checkpoint_path):
        try:
            with open(checkpoint_path, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
            
            processed_count = checkpoint_data.get('total_processed', 0)
            timestamp = checkpoint_data.get('checkpoint_timestamp', 0)
            
            if timestamp > 0:
                dt = datetime.fromtimestamp(timestamp)
                time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                time_str = "Unknown"
            
            print(f"🔄 Analysis In Progress: {processed_count} articles processed")
            print(f"⏰ Last checkpoint: {time_str}")
            print(f"📁 Checkpoint file: {checkpoint_path}")
            
            # Load processed articles to get total count
            input_path = os.path.join(Config.OUTPUT_DIR, "processed_articles.json")
            if os.path.exists(input_path):
                with open(input_path, 'r', encoding='utf-8') as f:
                    all_articles = json.load(f)
                total_articles = len(all_articles)
                remaining = total_articles - processed_count
                print(f"📊 Progress: {processed_count}/{total_articles} articles ({processed_count/total_articles*100:.1f}%)")
                print(f"⏳ Remaining: {remaining} articles")
            
        except Exception as e:
            print(f"❌ Error reading checkpoint: {str(e)}")
    
    else:
        print("📝 No checkpoint found - analysis not started or completed")
        print("💡 Run 'python main.py analyze' to start analysis")

def clear_checkpoint(args):
    """Clear analysis checkpoint."""
    checkpoint_path = os.path.join(Config.OUTPUT_DIR, "analysis_checkpoint.json")
    
    if not os.path.exists(checkpoint_path):
        print("📝 No checkpoint file found - nothing to clear")
        return
    
    # Confirmation unless --force is used
    if not args.force:
        response = input("⚠️ This will clear the analysis checkpoint and you'll have to start over. Continue? (y/N): ")
        if response.lower() != 'y':
            print("❌ Operation cancelled")
            return
    
    try:
        os.remove(checkpoint_path)
        print("✅ Checkpoint cleared successfully")
        print("💡 You can now run 'python main.py analyze' to start fresh")
    except Exception as e:
        print(f"❌ Error clearing checkpoint: {str(e)}")

if __name__ == "__main__":
    main()
