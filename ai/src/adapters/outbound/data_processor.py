"""
Data processing module for scientific publications.
Handles CSV loading, article scraping, and data preprocessing.
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import asyncio
import aiohttp
from asyncio_throttle import Throttler
from typing import List, Dict, Optional, Tuple
import json
import os
from tqdm import tqdm
import time
from ...infrastructure.config import Config

class PublicationScraper:
    """Handles scraping of scientific articles from PMC."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.throttler = Throttler(rate_limit=Config.MAX_CONCURRENT_REQUESTS, period=60)
    
    def load_publications_csv(self) -> pd.DataFrame:
        """Load the publications CSV file."""
        csv_path = os.path.join(Config.DATA_DIR, Config.CSV_FILE)
        
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        df = pd.read_csv(csv_path)
        print(f"Loaded {len(df)} publications from CSV")
        
        if Config.MAX_ARTICLES_TO_PROCESS:
            df = df.head(Config.MAX_ARTICLES_TO_PROCESS)
            print(f"Limited to {Config.MAX_ARTICLES_TO_PROCESS} articles for processing")
        
        return df
    
    def extract_pmc_id(self, url: str) -> Optional[str]:
        """Extract PMC ID from URL."""
        if "PMC" in url:
            try:
                return url.split("PMC")[1].split("/")[0].replace("articles/", "").replace("/", "")
            except:
                return None
        return None
    
    def scrape_article_content(self, url: str, title: str) -> Dict[str, str]:
        """
        Scrape article content from PMC URL.
        Returns a dictionary with extracted content sections.
        """
        try:
            time.sleep(Config.REQUEST_DELAY)  # Rate limiting
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract different sections
            content = {
                'title': title,
                'url': url,
                'abstract': self._extract_abstract(soup),
                'introduction': self._extract_section(soup, 'introduction'),
                'methods': self._extract_section(soup, 'methods'),
                'results': self._extract_section(soup, 'results'),
                'discussion': self._extract_section(soup, 'discussion'),
                'conclusion': self._extract_section(soup, 'conclusion'),
                'full_text': self._extract_full_text(soup)
            }
            
            return content
            
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return {
                'title': title,
                'url': url,
                'error': str(e),
                'abstract': '',
                'introduction': '',
                'methods': '',
                'results': '',
                'discussion': '',
                'conclusion': '',
                'full_text': ''
            }
    
    def _extract_abstract(self, soup: BeautifulSoup) -> str:
        """Extract abstract section."""
        abstract_selectors = [
            'div.abstract',
            'div.abstract-content',
            'div[data-type="abstract"]',
            'section.abstract'
        ]
        
        for selector in abstract_selectors:
            element = soup.select_one(selector)
            if element:
                return self._clean_text(element.get_text())
        
        return ""
    
    def _extract_section(self, soup: BeautifulSoup, section_name: str) -> str:
        """Extract specific section by name."""
        section_selectors = [
            f'section[data-type="{section_name}"]',
            f'div.{section_name}',
            f'h1:contains("{section_name.title()}")',
            f'h2:contains("{section_name.title()}")'
        ]
        
        for selector in section_selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    # Get content until next section
                    content = []
                    for sibling in element.find_next_siblings():
                        if sibling.name in ['h1', 'h2', 'h3'] and sibling.get_text().lower().strip() != section_name:
                            break
                        content.append(sibling.get_text())
                    
                    return self._clean_text(element.get_text() + " " + " ".join(content))
            except:
                continue
        
        return ""
    
    def _extract_full_text(self, soup: BeautifulSoup) -> str:
        """Extract full article text."""
        # Remove navigation and metadata
        for element in soup(['nav', 'header', 'footer', 'script', 'style']):
            element.decompose()
        
        # Try to find main content area
        content_selectors = [
            'div.article-content',
            'div.main-content',
            'article',
            'div.content',
            'div.article-body'
        ]
        
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                return self._clean_text(element.get_text())
        
        # Fallback to body
        return self._clean_text(soup.get_text())
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = ' '.join(text.split())
        
        # Remove common unwanted patterns
        unwanted_patterns = [
            'PubMed Central',
            'PMC',
            'National Center for Biotechnology Information',
            'NIH',
            'NCBI',
            'U.S. National Library of Medicine'
        ]
        
        for pattern in unwanted_patterns:
            text = text.replace(pattern, '')
        
        return text.strip()
    
    def process_publications_batch(self, df: pd.DataFrame, batch_size: int = None) -> List[Dict]:
        """
        Process publications in batches.
        Returns list of processed articles.
        """
        if batch_size is None:
            batch_size = Config.BATCH_SIZE
        
        processed_articles = []
        total_batches = (len(df) + batch_size - 1) // batch_size
        
        print(f"Processing {len(df)} articles in {total_batches} batches of {batch_size}")
        
        for batch_idx in range(0, len(df), batch_size):
            batch_df = df.iloc[batch_idx:batch_idx + batch_size]
            print(f"\nProcessing batch {batch_idx // batch_size + 1}/{total_batches}")
            
            batch_results = []
            for idx, row in tqdm(batch_df.iterrows(), total=len(batch_df), desc="Scraping articles"):
                article_content = self.scrape_article_content(row['Link'], row['Title'])
                batch_results.append(article_content)
            
            processed_articles.extend(batch_results)
            
            # Save intermediate results
            self._save_batch_results(batch_results, batch_idx // batch_size + 1)
        
        return processed_articles
    
    def _save_batch_results(self, batch_results: List[Dict], batch_num: int):
        """Save batch results to JSON file."""
        output_file = os.path.join(Config.OUTPUT_DIR, f"articles_batch_{batch_num}.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(batch_results, f, indent=2, ensure_ascii=False)
        
        print(f"Saved batch {batch_num} results to {output_file}")

class DataProcessor:
    """Main data processing class."""
    
    def __init__(self):
        self.scraper = PublicationScraper()
    
    def load_and_process_data(self) -> Tuple[pd.DataFrame, List[Dict]]:
        """
        Main method to load CSV and process articles.
        Returns DataFrame and processed articles list.
        """
        # Load CSV
        df = self.scraper.load_publications_csv()
        
        # Process articles
        articles = self.scraper.process_publications_batch(df)
        
        return df, articles
    
    def save_processed_data(self, articles: List[Dict], filename: str = "processed_articles.json"):
        """Save all processed articles to a single file."""
        output_path = os.path.join(Config.OUTPUT_DIR, filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(articles)} processed articles to {output_path}")
    
    def load_processed_data(self, filename: str = "processed_articles.json") -> List[Dict]:
        """Load previously processed articles."""
        file_path = os.path.join(Config.OUTPUT_DIR, filename)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Processed data file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
