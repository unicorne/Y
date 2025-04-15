"""
QuoteBot implementation.

A bot that posts famous quotes.
"""

import random
import requests
from typing import Dict, List, Tuple, Any

from bot_framework import Bot
from bot_implementations import register_bot_class

class QuoteBot(Bot):
    """A bot that posts famous quotes"""
    
    # API for quotes
    QUOTES_API = "https://api.quotable.io/random"
    
    def generate_post_content(self) -> Tuple[str, List[str]]:
        """Generate post content with a famous quote"""
        try:
            response = requests.get(self.QUOTES_API)
            if response.status_code == 200:
                data = response.json()
                quote = data.get('content')
                author = data.get('author')
                tags = data.get('tags', [])
                
                content = f'"{quote}" - {author} #quote'
                
                # Add the author as a tag
                author_tag = author.lower().replace(' ', '')
                tags.append('quote')
                tags.append(author_tag)
                
                return content, tags
            else:
                self.logger.warning(f"Failed to fetch quote: {response.status_code}")
        except Exception as e:
            self.logger.error(f"Error fetching quote: {str(e)}")
        
        # Fallback to a default quote
        return '"The only limit to our realization of tomorrow is our doubts of today." - Franklin D. Roosevelt', ['quote', 'motivation']
    
    def should_like_message(self, message: Dict) -> bool:
        """Decide whether to like a message based on content and probability"""
        # Higher chance to like messages with quote-related content
        content_lower = message.get('content', '').lower()
        has_quote = '"' in content_lower and '-' in content_lower
        
        base_probability = self.config["like_probability"]
        
        if has_quote:
            # 50% higher chance to like quote-related content
            return random.random() < (base_probability * 1.5)
        else:
            return random.random() < base_probability
    
    def generate_reply_content(self, message: Dict) -> Tuple[str, List[str]]:
        """Generate reply content based on the message"""
        try:
            # Get a new quote for the reply
            response = requests.get(self.QUOTES_API)
            if response.status_code == 200:
                data = response.json()
                quote = data.get('content')
                author = data.get('author')
                tags = data.get('tags', [])
                
                content = f'That reminds me of this quote: "{quote}" - {author}'
                
                # Add the author as a tag
                author_tag = author.lower().replace(' ', '')
                tags.append('quote')
                tags.append(author_tag)
                
                return content, tags
        except Exception as e:
            self.logger.error(f"Error fetching quote for reply: {str(e)}")
        
        # Fallback to a default reply
        return 'Great point! Here\'s a thought: "The best way to predict the future is to create it."', ['quote', 'inspiration']
    
    def should_reply_to_message(self, message: Dict) -> bool:
        """Decide whether to reply to a message based on content and probability"""
        # Higher chance to reply to messages with thoughtful content
        content_lower = message.get('content', '').lower()
        thoughtful_keywords = ['think', 'believe', 'opinion', 'perspective', 'view', 'idea']
        is_thoughtful = any(keyword in content_lower for keyword in thoughtful_keywords)
        
        base_probability = self.config["reply_probability"]
        
        if is_thoughtful:
            # 50% higher chance to reply to thoughtful content
            return random.random() < (base_probability * 1.5)
        else:
            return random.random() < base_probability


# Register this bot type with the factory
register_bot_class("quote", QuoteBot)