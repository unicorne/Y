"""
Template Bot implementation.

Use this template as a starting point for creating your own custom bots.
"""

import random
from typing import Dict, List, Tuple, Any

from bot_framework import Bot
from bot_implementations import register_bot_class

class TemplateBot(Bot):
    """
    Template for creating custom bots
    
    To create your own bot:
    1. Copy this file and rename it (e.g., my_custom_bot.py)
    2. Rename the class (e.g., MyCustomBot)
    3. Implement the required methods
    4. Register your bot with a unique type name
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the bot with configuration
        
        You can add custom initialization code here, but make sure to call the parent's __init__
        """
        super().__init__(config)
        
        # Add your custom initialization here
        # self.my_custom_attribute = "custom value"
    
    def generate_post_content(self) -> Tuple[str, List[str]]:
        """
        Generate content for a new post
        
        Returns:
            Tuple of (content, tags)
        """
        # TODO: Implement your custom post generation logic
        content = "This is a template post"
        tags = ["template", "example"]
        
        return content, tags
    
    def should_like_message(self, message: Dict) -> bool:
        """
        Determine if the bot should like a message
        
        Args:
            message: The message to consider liking
            
        Returns:
            True if the bot should like the message, False otherwise
        """
        # TODO: Implement your custom like decision logic
        # Default implementation: random decision based on like_probability
        return random.random() < self.config["like_probability"]
    
    def generate_reply_content(self, message: Dict) -> Tuple[str, List[str]]:
        """
        Generate content for a reply to a message
        
        Args:
            message: The message to reply to
            
        Returns:
            Tuple of (content, tags)
        """
        # TODO: Implement your custom reply generation logic
        content = f"This is a template reply to: {message.get('content', '')[:30]}..."
        tags = ["reply", "template"]
        
        return content, tags
    
    def should_reply_to_message(self, message: Dict) -> bool:
        """
        Determine if the bot should reply to a message
        
        Args:
            message: The message to consider replying to
            
        Returns:
            True if the bot should reply to the message, False otherwise
        """
        # TODO: Implement your custom reply decision logic
        # Default implementation: random decision based on reply_probability
        return random.random() < self.config["reply_probability"]


# Uncomment and modify this line to register your bot with the factory
# register_bot_class("template", TemplateBot)