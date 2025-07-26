#!/usr/bin/env python3
"""
Last Week in AI - RSS Feed Fetcher
==================================

This module fetches top AI articles from trusted sources and stores them locally.
Designed to run weekly via scheduler and display in the frontend.

Features:
- Fetches from multiple trusted AI sources
- Filters articles from the past week
- Stores top 10 articles in JSON format
- No NLP processing - just clean fetching and storage
- Handles rate limiting and error recovery
"""

import requests
import feedparser
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import os
from urllib.parse import urljoin
import time
import hashlib

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AINewsFetcher:
    """Fetches and stores AI news articles from trusted RSS sources"""
    
    def __init__(self, storage_file: str = "ai_articles.json"):
        self.storage_file = storage_file
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Trusted AI news sources with RSS feeds
        self.rss_sources = [
            {
                'name': 'MIT Technology Review - AI',
                'url': 'https://www.technologyreview.com/topic/artificial-intelligence/feed/',
                'priority': 1
            },
            {
                'name': 'Stanford HAI',
                'url': 'https://hai.stanford.edu/news/rss.xml',
                'priority': 1
            },
            {
                'name': 'arXiv AI/ML (cs.AI)',
                'url': 'http://export.arxiv.org/rss/cs.AI',
                'priority': 2
            },
            {
                'name': 'arXiv Machine Learning (cs.LG)',
                'url': 'http://export.arxiv.org/rss/cs.LG',
                'priority': 2
            },
            {
                'name': 'VentureBeat AI',
                'url': 'https://venturebeat.com/ai/feed/',
                'priority': 2
            },
            {
                'name': 'AI News',
                'url': 'https://www.artificialintelligence-news.com/feed/',
                'priority': 2
            },
            {
                'name': 'TechCrunch AI',
                'url': 'https://techcrunch.com/category/artificial-intelligence/feed/',
                'priority': 3
            },
            {
                'name': 'The Verge AI',
                'url': 'https://www.theverge.com/ai-artificial-intelligence/rss/index.xml',
                'priority': 3
            }
        ]
        
        # Keywords for AI relevance (simple filtering)
        self.ai_keywords = [
            'artificial intelligence', 'ai', 'machine learning', 'ml', 'deep learning',
            'neural network', 'chatgpt', 'openai', 'microsoft copilot', 'copilot',
            'generative ai', 'large language model', 'llm', 'transformer',
            'computer vision', 'nlp', 'natural language processing', 'robotics',
            'automation', 'cognitive computing', 'data science', 'algorithm'
        ]

    def _rate_limit(self, delay: float = 1.0):
        """Simple rate limiting between requests"""
        time.sleep(delay)

    def _is_recent(self, published_date: str, days_back: int = 7) -> bool:
        """Check if article is from the past week"""
        try:
            if not published_date:
                return False
                
            # Parse the date (feedparser usually provides struct_time)
            if hasattr(published_date, 'tm_year'):
                article_date = datetime(*published_date[:6])
            else:
                # Try to parse string date
                from dateutil import parser
                article_date = parser.parse(published_date)
            
            cutoff_date = datetime.now() - timedelta(days=days_back)
            return article_date >= cutoff_date
            
        except Exception as e:
            logger.debug(f"Date parsing error: {e}")
            # If we can't parse the date, include the article (better safe than sorry)
            return True

    def _is_ai_relevant(self, title: str, description: str = "") -> bool:
        """Check if article is AI-related using keyword matching"""
        text_to_check = f"{title} {description}".lower()
        return any(keyword in text_to_check for keyword in self.ai_keywords)

    def _generate_article_id(self, title: str, link: str) -> str:
        """Generate unique ID for article to avoid duplicates"""
        content = f"{title}{link}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def fetch_from_source(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch articles from a single RSS source"""
        articles = []
        
        try:
            logger.info(f"🔍 Fetching from {source['name']}...")
            
            # Add rate limiting
            self._rate_limit(1.0)
            
            # Parse RSS feed
            feed = feedparser.parse(source['url'])
            
            if feed.bozo:
                logger.warning(f"⚠️  RSS parsing warning for {source['name']}: {feed.bozo_exception}")
            
            logger.info(f"📰 Found {len(feed.entries)} entries from {source['name']}")
            
            for entry in feed.entries:
                try:
                    # Extract article data
                    title = entry.get('title', 'No Title')
                    link = entry.get('link', '')
                    description = entry.get('description', '') or entry.get('summary', '')
                    published = entry.get('published_parsed', None)
                    author = entry.get('author', '')
                    
                    # Skip if no title or link
                    if not title or not link:
                        continue
                    
                    # Check if article is recent (past week)
                    if not self._is_recent(published, days_back=7):
                        logger.debug(f"Skipping old article: {title[:50]}...")
                        continue
                    
                    # Check if article is AI-relevant
                    if not self._is_ai_relevant(title, description):
                        logger.debug(f"Skipping non-AI article: {title[:50]}...")
                        continue
                    
                    # Create article object
                    article = {
                        'id': self._generate_article_id(title, link),
                        'title': title[:200],  # Limit title length
                        'link': link,
                        'description': description[:500] if description else '',  # Limit description
                        'source': source['name'],
                        'author': author,
                        'published': published,
                        'published_str': entry.get('published', ''),
                        'priority': source['priority'],
                        'fetched_at': datetime.now().isoformat()
                    }
                    
                    articles.append(article)
                    logger.debug(f"✅ Added: {title[:50]}...")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing entry from {source['name']}: {e}")
                    continue
            
            logger.info(f"✅ Successfully fetched {len(articles)} AI articles from {source['name']}")
            
        except Exception as e:
            logger.error(f"❌ Error fetching from {source['name']}: {e}")
        
        return articles

    def fetch_all_articles(self) -> List[Dict[str, Any]]:
        """Fetch articles from all RSS sources"""
        logger.info("🚀 Starting AI news fetch from all sources...")
        
        all_articles = []
        
        for source in self.rss_sources:
            try:
                articles = self.fetch_from_source(source)
                all_articles.extend(articles)
                
                # Rate limiting between sources
                self._rate_limit(2.0)
                
            except Exception as e:
                logger.error(f"❌ Failed to fetch from {source['name']}: {e}")
                continue
        
        logger.info(f"📊 Total articles fetched: {len(all_articles)}")
        return all_articles

    def select_top_articles(self, articles: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
        """Select top articles based on priority and recency"""
        
        # Remove duplicates based on article ID
        unique_articles = {}
        for article in articles:
            article_id = article['id']
            if article_id not in unique_articles:
                unique_articles[article_id] = article
        
        articles = list(unique_articles.values())
        logger.info(f"📊 After deduplication: {len(articles)} unique articles")
        
        # Sort by priority (lower number = higher priority) and then by date
        def sort_key(article):
            priority = article.get('priority', 5)
            # Convert published time to sortable format
            try:
                if article.get('published'):
                    if hasattr(article['published'], 'tm_year'):
                        pub_date = datetime(*article['published'][:6])
                    else:
                        from dateutil import parser
                        pub_date = parser.parse(article['published_str'])
                    return (priority, -pub_date.timestamp())  # Negative for reverse chronological
                else:
                    return (priority, 0)
            except:
                return (priority, 0)
        
        sorted_articles = sorted(articles, key=sort_key)
        top_articles = sorted_articles[:limit]
        
        logger.info(f"🎯 Selected top {len(top_articles)} articles")
        
        # Log the top articles
        for i, article in enumerate(top_articles, 1):
            logger.info(f"  {i}. {article['title'][:60]}... ({article['source']})")
        
        return top_articles

    def save_articles(self, articles: List[Dict[str, Any]]):
        """Save articles to JSON file"""
        try:
            # Prepare data for storage
            storage_data = {
                'last_updated': datetime.now().isoformat(),
                'article_count': len(articles),
                'articles': articles
            }
            
            # Write to JSON file
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(storage_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"💾 Saved {len(articles)} articles to {self.storage_file}")
            
        except Exception as e:
            logger.error(f"❌ Error saving articles: {e}")

    def load_articles(self) -> Dict[str, Any]:
        """Load articles from JSON file"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"📖 Loaded {data.get('article_count', 0)} articles from storage")
                return data
            else:
                logger.info("📂 No existing articles file found")
                return {'articles': [], 'last_updated': None, 'article_count': 0}
                
        except Exception as e:
            logger.error(f"❌ Error loading articles: {e}")
            return {'articles': [], 'last_updated': None, 'article_count': 0}

    def run_fetch(self, limit: int = 10) -> Dict[str, Any]:
        """Main method to run the complete fetch process"""
        logger.info("🎯 Starting Last Week in AI article fetch...")
        
        try:
            # Fetch articles from all sources
            all_articles = self.fetch_all_articles()
            
            if not all_articles:
                logger.warning("⚠️  No articles fetched from any source")
                return {'success': False, 'message': 'No articles fetched', 'articles': []}
            
            # Select top articles
            top_articles = self.select_top_articles(all_articles, limit=limit)
            
            # Save to storage
            self.save_articles(top_articles)
            
            logger.info(f"🎉 Successfully completed AI news fetch! Top {len(top_articles)} articles saved.")
            
            return {
                'success': True,
                'message': f'Successfully fetched {len(top_articles)} articles',
                'articles': top_articles,
                'total_fetched': len(all_articles),
                'sources_used': len(set(article['source'] for article in all_articles))
            }
            
        except Exception as e:
            logger.error(f"❌ Fatal error in fetch process: {e}")
            return {'success': False, 'message': f'Fetch failed: {str(e)}', 'articles': []}

def main():
    """CLI entry point for testing"""
    fetcher = AINewsFetcher()
    result = fetcher.run_fetch()
    
    print(f"\n{'='*50}")
    print("LAST WEEK IN AI - FETCH SUMMARY")
    print(f"{'='*50}")
    print(f"Status: {'✅ SUCCESS' if result['success'] else '❌ FAILED'}")
    print(f"Message: {result['message']}")
    
    if result['success']:
        print(f"Articles saved: {len(result['articles'])}")
        print(f"Total fetched: {result.get('total_fetched', 0)}")
        print(f"Sources used: {result.get('sources_used', 0)}")
        
        print(f"\n📰 TOP ARTICLES:")
        for i, article in enumerate(result['articles'], 1):
            print(f"  {i}. {article['title']}")
            print(f"     Source: {article['source']}")
            print(f"     Link: {article['link']}")
            print()

if __name__ == "__main__":
    main()
