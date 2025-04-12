import requests
import random
import time
import os
import logging
import json
from datetime import datetime
from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class Bot(ABC):
    """Base Bot class that all other bots should inherit from"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the bot with configuration
        
        Args:
            config: Dictionary with configuration options
        """
        # Default configuration
        self.config = {
            "api_url": os.getenv("API_URL", "http://localhost:8000"),
            "username": f"bot_{random.randint(1000, 9999)}",
            "email": None,  # Will be set based on username
            "password": "password123",
            "post_interval": 60,  # seconds
            "like_interval": 30,  # seconds
            "reply_interval": 45,  # seconds
            "like_probability": 0.5,  # 50% chance to like a message
            "reply_probability": 0.3,  # 30% chance to reply to a message
            "max_messages_to_fetch": 20,  # Number of messages to fetch for potential likes/replies
        }
        
        # Update with provided config
        if config:
            self.config.update(config)
            
        # Set email if not provided
        if not self.config["email"]:
            self.config["email"] = f"{self.config['username']}@example.com"
            
        # Bot state
        self.token = None
        self.user_id = None
        self.last_post_time = 0
        self.last_like_time = 0
        self.last_reply_time = 0
        
        # Set up logger
        self.logger = logging.getLogger(f"bot.{self.config['username']}")
        
    def register(self) -> bool:
        """Register the bot as a new user"""
        try:
            response = requests.post(
                f"{self.config['api_url']}/users/",
                json={
                    "username": self.config["username"],
                    "email": self.config["email"],
                    "password": self.config["password"]
                }
            )
            
            if response.status_code == 201:
                self.logger.info(f"Bot registered successfully: {self.config['username']}")
                return True
            elif response.status_code == 400 and "already registered" in response.json().get("detail", ""):
                self.logger.info(f"Bot already registered: {self.config['username']}")
                return True
            else:
                self.logger.error(f"Failed to register bot: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"Error registering bot: {str(e)}")
            return False
    
    def login(self) -> bool:
        """Login the bot and get an access token"""
        try:
            response = requests.post(
                f"{self.config['api_url']}/token",
                data={
                    "username": self.config["username"],
                    "password": self.config["password"]
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                
                # Get user ID
                user_response = requests.get(
                    f"{self.config['api_url']}/users/me",
                    headers={"Authorization": f"Bearer {self.token}"}
                )
                
                if user_response.status_code == 200:
                    user_data = user_response.json()
                    self.user_id = user_data["id"]
                    self.logger.info(f"Bot logged in successfully: {self.config['username']} (ID: {self.user_id})")
                    return True
                else:
                    self.logger.error(f"Failed to get user info: {user_response.status_code} - {user_response.text}")
                    return False
            else:
                self.logger.error(f"Failed to login: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"Error logging in: {str(e)}")
            return False
    
    def get_messages(self, limit: int = None) -> List[Dict]:
        """
        Get recent messages
        
        Args:
            limit: Maximum number of messages to fetch
        
        Returns:
            List of message dictionaries
        """
        if not self.token:
            self.logger.error("Not logged in. Cannot get messages.")
            return []
        
        if limit is None:
            limit = self.config["max_messages_to_fetch"]
        
        try:
            response = requests.get(
                f"{self.config['api_url']}/messages/?limit={limit}",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get messages: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            self.logger.error(f"Error getting messages: {str(e)}")
            return []
    
    @abstractmethod
    def generate_post_content(self) -> Tuple[str, List[str]]:
        """
        Generate content for a new post
        
        Returns:
            Tuple of (content, tags)
        """
        pass
    
    def post_message(self) -> bool:
        """Post a message"""
        if not self.token:
            self.logger.error("Not logged in. Cannot post message.")
            return False
        
        content, tags = self.generate_post_content()
        
        try:
            response = requests.post(
                f"{self.config['api_url']}/messages/",
                json={
                    "content": content,
                    "tags": tags
                },
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code == 201:
                message_data = response.json()
                self.logger.info(f"Posted message: {content[:30]}... (ID: {message_data['id']})")
                self.last_post_time = time.time()
                return True
            else:
                self.logger.error(f"Failed to post message: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"Error posting message: {str(e)}")
            return False
    
    @abstractmethod
    def should_like_message(self, message: Dict) -> bool:
        """
        Determine if the bot should like a message
        
        Args:
            message: The message to consider liking
            
        Returns:
            True if the bot should like the message, False otherwise
        """
        pass
    
    def like_message(self, message_id: int) -> bool:
        """
        Like a specific message
        
        Args:
            message_id: ID of the message to like
            
        Returns:
            True if successful, False otherwise
        """
        if not self.token:
            self.logger.error("Not logged in. Cannot like message.")
            return False
        
        try:
            response = requests.post(
                f"{self.config['api_url']}/messages/{message_id}/like",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code == 200:
                self.logger.info(f"Liked message (ID: {message_id})")
                self.last_like_time = time.time()
                return True
            elif response.status_code == 400 and "already liked" in response.json().get("detail", ""):
                self.logger.info(f"Already liked message (ID: {message_id})")
                return True
            else:
                self.logger.error(f"Failed to like message: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"Error liking message: {str(e)}")
            return False
    
    def process_likes(self) -> bool:
        """
        Process potential messages to like
        
        Returns:
            True if any message was liked, False otherwise
        """
        if not self.token:
            self.logger.error("Not logged in. Cannot process likes.")
            return False
        
        messages = self.get_messages()
        if not messages:
            self.logger.info("No messages to like.")
            return False
        
        # Filter out messages from this bot
        likeable_messages = [
            msg for msg in messages 
            if msg["user_id"] != self.user_id  # Don't like own messages
        ]
        
        if not likeable_messages:
            self.logger.info("No likeable messages found.")
            return False
        
        # Shuffle messages to avoid always liking the same ones
        random.shuffle(likeable_messages)
        
        liked_any = False
        for message in likeable_messages:
            if self.should_like_message(message):
                if self.like_message(message["id"]):
                    liked_any = True
                    # Only like one message per cycle
                    break
        
        return liked_any
    
    @abstractmethod
    def generate_reply_content(self, message: Dict) -> Tuple[str, List[str]]:
        """
        Generate content for a reply to a message
        
        Args:
            message: The message to reply to
            
        Returns:
            Tuple of (content, tags)
        """
        pass
    
    @abstractmethod
    def should_reply_to_message(self, message: Dict) -> bool:
        """
        Determine if the bot should reply to a message
        
        Args:
            message: The message to consider replying to
            
        Returns:
            True if the bot should reply to the message, False otherwise
        """
        pass
    
    def reply_to_message(self, message: Dict) -> bool:
        """
        Reply to a specific message
        
        Args:
            message: The message to reply to
            
        Returns:
            True if successful, False otherwise
        """
        if not self.token:
            self.logger.error("Not logged in. Cannot reply to message.")
            return False
        
        content, tags = self.generate_reply_content(message)
        
        # Add a reference to the original message
        content = f"@{message['username']} {content}"
        
        try:
            response = requests.post(
                f"{self.config['api_url']}/messages/",
                json={
                    "content": content,
                    "tags": tags
                },
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code == 201:
                message_data = response.json()
                self.logger.info(f"Replied to message {message['id']}: {content[:30]}... (ID: {message_data['id']})")
                self.last_reply_time = time.time()
                return True
            else:
                self.logger.error(f"Failed to reply to message: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"Error replying to message: {str(e)}")
            return False
    
    def process_replies(self) -> bool:
        """
        Process potential messages to reply to
        
        Returns:
            True if any message was replied to, False otherwise
        """
        if not self.token:
            self.logger.error("Not logged in. Cannot process replies.")
            return False
        
        messages = self.get_messages()
        if not messages:
            self.logger.info("No messages to reply to.")
            return False
        
        # Filter out messages from this bot
        replyable_messages = [
            msg for msg in messages 
            if msg["user_id"] != self.user_id  # Don't reply to own messages
        ]
        
        if not replyable_messages:
            self.logger.info("No replyable messages found.")
            return False
        
        # Shuffle messages to avoid always replying to the same ones
        random.shuffle(replyable_messages)
        
        replied_to_any = False
        for message in replyable_messages:
            if self.should_reply_to_message(message):
                if self.reply_to_message(message):
                    replied_to_any = True
                    # Only reply to one message per cycle
                    break
        
        return replied_to_any
    
    def run(self):
        """Main bot loop"""
        self.logger.info(f"Starting bot: {self.config['username']}")
        
        # Register and login
        if not self.register():
            self.logger.error("Failed to register bot. Exiting.")
            return
        
        if not self.login():
            self.logger.error("Failed to login. Exiting.")
            return
        
        self.logger.info(f"Bot is running with configuration: {json.dumps(self.config, indent=2)}")
        
        try:
            while True:
                current_time = time.time()
                
                # Post a message if it's time
                if current_time - self.last_post_time >= self.config["post_interval"]:
                    self.post_message()
                
                # Like a message if it's time
                if current_time - self.last_like_time >= self.config["like_interval"]:
                    self.process_likes()
                
                # Reply to a message if it's time
                if current_time - self.last_reply_time >= self.config["reply_interval"]:
                    self.process_replies()
                
                # Sleep to avoid busy waiting
                time.sleep(5)
        except KeyboardInterrupt:
            self.logger.info("Bot stopped by user.")
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")


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


class BotFactory:
    """Factory for creating different types of bots"""
    
    @staticmethod
    def create_bot(bot_type: str, config: Dict[str, Any] = None) -> Bot:
        """
        Create a bot of the specified type
        
        Args:
            bot_type: Type of bot to create
            config: Configuration for the bot
            
        Returns:
            A bot instance
            
        Raises:
            ValueError: If the bot type is not recognized
        """
        if bot_type.lower() == "random":
            return RandomBot(config)
        else:
            raise ValueError(f"Unknown bot type: {bot_type}")


def run_bot(bot_type: str = "random", config: Dict[str, Any] = None):
    """
    Run a bot with the specified type and configuration
    
    Args:
        bot_type: Type of bot to run
        config: Configuration for the bot
    """
    try:
        bot = BotFactory.create_bot(bot_type, config)
        bot.run()
    except Exception as e:
        logging.error(f"Error running bot: {str(e)}")


if __name__ == "__main__":
    # Example usage
    run_bot("random", {
        "post_interval": 60,
        "like_interval": 30,
        "reply_interval": 45,
        "like_probability": 0.5,
        "reply_probability": 0.3
    })