"""
RandomBot implementation.

A simple bot that posts random content and interacts randomly with other users' messages.
"""

import random
from typing import Dict, List, Tuple, Any

from bot_framework import Bot
from bot_implementations import register_bot_class

class RandomBot(Bot):
    """A bot that posts random content and interacts randomly"""
    
    # Sample data for random posts
    TOPICS = ["technology", "sports", "food", "travel", "movies", "music", "books", "gaming"]
    ADJECTIVES = ["amazing", "awesome", "great", "interesting", "cool", "fantastic", "wonderful", "excellent"]
    VERBS = ["love", "enjoy", "like", "appreciate", "admire", "recommend", "suggest", "prefer"]
    
    def generate_post_content(self) -> Tuple[str, List[str]]:
        """Generate random post content"""
        topic = random.choice(self.TOPICS)
        adjective = random.choice(self.ADJECTIVES)
        verb = random.choice(self.VERBS)
        
        content = f"I {verb} this {adjective} {topic}! #{topic} #{adjective}"
        tags = [topic, adjective]
        
        return content, tags
    
    def should_like_message(self, message: Dict) -> bool:
        """Decide whether to like a message based on probability"""
        return random.random() < self.config["like_probability"]
    
    def generate_reply_content(self, message: Dict) -> Tuple[str, List[str]]:
        """Generate random reply content"""
        topic = random.choice(self.TOPICS)
        adjective = random.choice(self.ADJECTIVES)
        verb = random.choice(self.VERBS)
        
        content = f"I also {verb} {topic}! It's really {adjective}."
        tags = [topic, adjective]
        
        return content, tags
    
    def should_reply_to_message(self, message: Dict) -> bool:
        """Decide whether to reply to a message based on probability"""
        return random.random() < self.config["reply_probability"]


# Register this bot type with the factory
register_bot_class("random", RandomBot)