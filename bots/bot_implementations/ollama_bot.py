"""
OllamaBot implementation.

A bot that uses Ollama to generate realistic content for posts and replies.
"""

import random
import re
import requests
import logging
from typing import Dict, List, Tuple, Any, Optional
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from bot_framework import Bot
from bot_implementations import register_bot_class

class OllamaBot(Bot):
    """A bot that uses Ollama to generate realistic content"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        
        # Set default Ollama configuration
        self.model_name = self.config.get("model_name", "llama3.2:latest")
        self.system_prompt = self.config.get("system_prompt", "You are a friendly and helpful social media user who posts about technology and science.")
        self.ollama_url = self.config.get("ollama_url", "http://localhost:11434/api/generate")
        self.max_retries = self.config.get("max_retries", 3)
        self.retry_delay = self.config.get("retry_delay", 2)
        
        # Optional configuration for post and reply generation
        self.post_topics = self.config.get("post_topics", ["technology", "science", "programming", "AI", "data science"])
        self.post_prompt_template = self.config.get(
            "post_prompt_template", 
            "Write a short social media post (max 280 characters) about {topic}. Include 2-3 relevant hashtags at the end."
        )
        self.reply_prompt_template = self.config.get(
            "reply_prompt_template",
            "Write a short reply (max 280 characters) to this social media post: \"{content}\". Be engaging and relevant. Include 1-2 hashtags at the end."
        )
        
        self.logger.info(f"Initialized OllamaBot with model: {self.model_name}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type((requests.RequestException, ConnectionError)),
        reraise=True
    )
    def get_llm_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Get a response from the Ollama API
        
        Args:
            prompt: The prompt to send to the LLM
            system_prompt: Optional system prompt to override the default
            
        Returns:
            The generated response text
            
        Raises:
            requests.RequestException: If there's an error communicating with the API
            ValueError: If the API returns an error response
        """
        if system_prompt is None:
            system_prompt = self.system_prompt
            
        try:
            self.logger.debug(f"Sending prompt to Ollama: {prompt[:50]}...")
            
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model_name,
                    "system": system_prompt,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_ctx": 8192},
                },
                timeout=30  # 30 second timeout
            )
            
            response.raise_for_status()  # Raise exception for HTTP errors
            
            result = response.json()
            if "error" in result:
                raise ValueError(f"Ollama API error: {result['error']}")
                
            if "response" not in result:
                raise ValueError(f"Unexpected response format from Ollama API: {result}")
                
            return result["response"]
            
        except requests.RequestException as e:
            self.logger.error(f"Error connecting to Ollama API: {str(e)}")
            raise
        except ValueError as e:
            self.logger.error(f"Error processing Ollama response: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error with Ollama API: {str(e)}")
            raise ValueError(f"Unexpected error: {str(e)}")
    
    def extract_tags_from_text(self, text: str) -> List[str]:
        """
        Extract hashtags from text
        
        Args:
            text: The text to extract hashtags from
            
        Returns:
            List of hashtags (without the # symbol)
        """
        # Find all hashtags in the text
        hashtags = re.findall(r'#(\w+)', text)
        
        # If no hashtags found, extract potential keywords
        if not hashtags:
            # Extract words that might be good tags (4+ characters, not common words)
            common_words = ["this", "that", "with", "from", "have", "about", "would", "could", "should"]
            words = re.findall(r'\b(\w{4,})\b', text.lower())
            potential_tags = [word for word in words if word not in common_words]
            
            # Take up to 3 potential tags
            hashtags = potential_tags[:3]
        
        return hashtags
    
    def generate_post_content(self) -> Tuple[str, List[str]]:
        """Generate post content using Ollama"""
        try:
            # Select a random topic
            topic = random.choice(self.post_topics)
            
            # Create the prompt
            prompt = self.post_prompt_template.format(topic=topic)
            
            # Get response from Ollama
            response = self.get_llm_response(prompt)
            
            # Extract hashtags
            tags = self.extract_tags_from_text(response)
            
            # Clean up the response (remove excessive newlines, etc.)
            content = response.strip()
            
            return content, tags
            
        except Exception as e:
            self.logger.error(f"Error generating post content: {str(e)}")
            # Fallback to a simple message
            return f"Interesting thoughts about {random.choice(self.post_topics)}...", ["fallback"]
    
    def should_like_message(self, message: Dict) -> bool:
        """Decide whether to like a message based on probability"""
        # For efficiency, we use a simple probability-based approach
        # rather than asking the LLM for each potential like
        return random.random() < self.config["like_probability"]
    
    def generate_reply_content(self, message: Dict) -> Tuple[str, List[str]]:
        """Generate reply content based on the message using Ollama"""
        try:
            # Get the original message content
            original_content = message.get('content', '')
            
            # Create the prompt
            prompt = self.reply_prompt_template.format(content=original_content)
            
            # Get response from Ollama
            response = self.get_llm_response(prompt)
            
            # Extract hashtags
            tags = self.extract_tags_from_text(response)
            
            # Clean up the response
            content = response.strip()
            
            return content, tags
            
        except Exception as e:
            self.logger.error(f"Error generating reply content: {str(e)}")
            # Fallback to a simple reply
            return "Interesting point! Thanks for sharing.", ["fallback"]
    
    def should_reply_to_message(self, message: Dict) -> bool:
        """Decide whether to reply to a message based on probability"""
        # For efficiency, we use a simple probability-based approach
        return random.random() < self.config["reply_probability"]


# Register this bot type with the factory
register_bot_class("ollama", OllamaBot)