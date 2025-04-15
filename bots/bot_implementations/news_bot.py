"""
NewsBot implementation.

A bot that posts content from news websites.
"""

import random
import requests
import re
import time
from typing import Dict, List, Tuple, Any
from bs4 import BeautifulSoup

from bot_framework import Bot
from bot_implementations import register_bot_class

class NewsBot(Bot):
    """A bot that posts content from news websites"""
    
    # List of news RSS feeds to scrape
    NEWS_SOURCES = [
        "https://news.google.com/rss",
        "https://www.reddit.com/r/technology/.rss",
        "https://www.reddit.com/r/worldnews/.rss"
    ]
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.cached_news = []
        self.last_fetch_time = 0
        self.fetch_interval = 300  # 5 minutes
    
    def fetch_news(self) -> List[Dict[str, str]]:
        """
        Fetch news from RSS feeds
        
        Returns:
            List of news items with title, link, and source
        """
        current_time = time.time()
        
        # Only fetch new content if the cache is empty or it's time to refresh
        if not self.cached_news or current_time - self.last_fetch_time >= self.fetch_interval:
            self.logger.info("Fetching fresh news content")
            news_items = []
            
            for source in self.NEWS_SOURCES:
                try:
                    response = requests.get(source, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'xml')
                        items = soup.find_all('item')
                        
                        for item in items[:5]:  # Get the first 5 items from each source
                            title = item.find('title').text
                            link = item.find('link').text
                            
                            # Extract source name from the URL
                            source_name = re.search(r'https?://(?:www\.)?([^/]+)', source).group(1)
                            
                            news_items.append({
                                'title': title,
                                'link': link,
                                'source': source_name
                            })
                    else:
                        self.logger.warning(f"Failed to fetch news from {source}: {response.status_code}")
                except Exception as e:
                    self.logger.error(f"Error fetching news from {source}: {str(e)}")
            
            # Update cache and fetch time
            self.cached_news = news_items
            self.last_fetch_time = current_time
        
        return self.cached_news
    
    def generate_post_content(self) -> Tuple[str, List[str]]:
        """Generate post content from news articles"""
        news_items = self.fetch_news()
        
        if not news_items:
            # Fallback to random content if no news is available
            return "No interesting news today. #news", ["news"]
        
        # Select a random news item
        news_item = random.choice(news_items)
        
        # Create content with the news title and link
        content = f"{news_item['title']} {news_item['link']} #news #{news_item['source']}"
        
        # Extract potential tags from the title
        title_words = re.findall(r'\b\w{4,}\b', news_item['title'].lower())
        potential_tags = [word for word in title_words if len(word) > 3 and word not in ['this', 'that', 'with', 'from']]
        
        # Select up to 3 tags from the title
        selected_tags = random.sample(potential_tags, min(3, len(potential_tags)))
        
        # Add default tags
        tags = ["news", news_item['source']] + selected_tags
        
        return content, tags
    
    def should_like_message(self, message: Dict) -> bool:
        """Decide whether to like a message based on content and probability"""
        # Higher chance to like messages with news-related tags
        news_related = any(tag['name'].lower() in ['news', 'technology', 'world', 'politics'] 
                          for tag in message.get('tags', []))
        
        base_probability = self.config["like_probability"]
        
        if news_related:
            # 50% higher chance to like news-related content
            return random.random() < (base_probability * 1.5)
        else:
            return random.random() < base_probability
    
    def generate_reply_content(self, message: Dict) -> Tuple[str, List[str]]:
        """Generate reply content based on the message"""
        # Get some fresh news for context
        news_items = self.fetch_news()
        
        # Default reply if no news is available
        if not news_items:
            return "Interesting point! Thanks for sharing.", ["news"]
        
        # Try to find a related news item based on tags
        message_tags = [tag['name'].lower() for tag in message.get('tags', [])]
        
        related_news = None
        for news_item in news_items:
            title_lower = news_item['title'].lower()
            if any(tag in title_lower for tag in message_tags):
                related_news = news_item
                break
        
        if related_news:
            # Reply with related news
            content = f"That reminds me of this: {related_news['title']} {related_news['link']}"
            tags = ["news", related_news['source']]
        else:
            # Reply with a random news item
            news_item = random.choice(news_items)
            content = f"Have you seen this related news? {news_item['title']} {news_item['link']}"
            tags = ["news", news_item['source']]
        
        return content, tags
    
    def should_reply_to_message(self, message: Dict) -> bool:
        """Decide whether to reply to a message based on content and probability"""
        # Higher chance to reply to messages with news-related tags
        news_related = any(tag['name'].lower() in ['news', 'technology', 'world', 'politics'] 
                          for tag in message.get('tags', []))
        
        base_probability = self.config["reply_probability"]
        
        if news_related:
            # 50% higher chance to reply to news-related content
            return random.random() < (base_probability * 1.5)
        else:
            return random.random() < base_probability


# Register this bot type with the factory
register_bot_class("news", NewsBot)