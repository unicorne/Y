import requests
import random
import time
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("bot")

# Configuration
API_URL = os.getenv("API_URL", "http://backend:8000")
BOT_USERNAME = os.getenv("BOT_USERNAME", f"bot_{random.randint(1000, 9999)}")
BOT_EMAIL = os.getenv("BOT_EMAIL", f"{BOT_USERNAME}@example.com")
BOT_PASSWORD = os.getenv("BOT_PASSWORD", "password123")
POST_INTERVAL = int(os.getenv("POST_INTERVAL", "60"))  # seconds
LIKE_INTERVAL = int(os.getenv("LIKE_INTERVAL", "30"))  # seconds

# Sample data for random posts
TOPICS = ["technology", "sports", "food", "travel", "movies", "music", "books", "gaming"]
ADJECTIVES = ["amazing", "awesome", "great", "interesting", "cool", "fantastic", "wonderful", "excellent"]
VERBS = ["love", "enjoy", "like", "appreciate", "admire", "recommend", "suggest", "prefer"]

# Bot state
token = None
user_id = None
last_post_time = 0
last_like_time = 0

def register_bot():
    """Register the bot as a new user"""
    try:
        response = requests.post(
            f"{API_URL}/users/",
            json={
                "username": BOT_USERNAME,
                "email": BOT_EMAIL,
                "password": BOT_PASSWORD
            }
        )
        
        if response.status_code == 201:
            logger.info(f"Bot registered successfully: {BOT_USERNAME}")
            return True
        elif response.status_code == 400 and "already registered" in response.json().get("detail", ""):
            logger.info(f"Bot already registered: {BOT_USERNAME}")
            return True
        else:
            logger.error(f"Failed to register bot: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error registering bot: {str(e)}")
        return False

def login_bot():
    """Login the bot and get an access token"""
    global token, user_id
    
    try:
        response = requests.post(
            f"{API_URL}/token",
            data={
                "username": BOT_USERNAME,
                "password": BOT_PASSWORD
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data["access_token"]
            
            # Get user ID
            user_response = requests.get(
                f"{API_URL}/users/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if user_response.status_code == 200:
                user_data = user_response.json()
                user_id = user_data["id"]
                logger.info(f"Bot logged in successfully: {BOT_USERNAME} (ID: {user_id})")
                return True
            else:
                logger.error(f"Failed to get user info: {user_response.status_code} - {user_response.text}")
                return False
        else:
            logger.error(f"Failed to login: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error logging in: {str(e)}")
        return False

def generate_random_post():
    """Generate a random post with tags"""
    topic = random.choice(TOPICS)
    adjective = random.choice(ADJECTIVES)
    verb = random.choice(VERBS)
    
    content = f"I {verb} this {adjective} {topic}! #{topic} #{adjective}"
    tags = [topic, adjective]
    
    return content, tags

def post_message():
    """Post a random message"""
    global last_post_time
    
    if not token:
        logger.error("Not logged in. Cannot post message.")
        return False
    
    content, tags = generate_random_post()
    
    try:
        response = requests.post(
            f"{API_URL}/messages/",
            json={
                "content": content,
                "tags": tags
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 201:
            message_data = response.json()
            logger.info(f"Posted message: {content} (ID: {message_data['id']})")
            last_post_time = time.time()
            return True
        else:
            logger.error(f"Failed to post message: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error posting message: {str(e)}")
        return False

def get_messages():
    """Get recent messages"""
    if not token:
        logger.error("Not logged in. Cannot get messages.")
        return []
    
    try:
        response = requests.get(
            f"{API_URL}/messages/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to get messages: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        logger.error(f"Error getting messages: {str(e)}")
        return []

def like_random_message():
    """Like a random message"""
    global last_like_time
    
    if not token:
        logger.error("Not logged in. Cannot like message.")
        return False
    
    messages = get_messages()
    if not messages:
        logger.info("No messages to like.")
        return False
    
    # Filter out messages from this bot and messages already liked
    likeable_messages = [
        msg for msg in messages 
        if msg["user_id"] != user_id  # Don't like own messages
    ]
    
    if not likeable_messages:
        logger.info("No likeable messages found.")
        return False
    
    # Choose a random message to like
    message = random.choice(likeable_messages)
    
    try:
        response = requests.post(
            f"{API_URL}/messages/{message['id']}/like",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            logger.info(f"Liked message: {message['content'][:30]}... (ID: {message['id']})")
            last_like_time = time.time()
            return True
        elif response.status_code == 400 and "already liked" in response.json().get("detail", ""):
            logger.info(f"Already liked message (ID: {message['id']})")
            last_like_time = time.time()
            return True
        else:
            logger.error(f"Failed to like message: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error liking message: {str(e)}")
        return False

def run_bot():
    """Main bot loop"""
    logger.info(f"Starting bot: {BOT_USERNAME}")
    
    # Register and login
    if not register_bot():
        logger.error("Failed to register bot. Exiting.")
        return
    
    if not login_bot():
        logger.error("Failed to login. Exiting.")
        return
    
    logger.info(f"Bot is running with post interval: {POST_INTERVAL}s, like interval: {LIKE_INTERVAL}s")
    
    try:
        while True:
            current_time = time.time()
            
            # Post a message if it's time
            if current_time - last_post_time >= POST_INTERVAL:
                post_message()
            
            # Like a message if it's time
            if current_time - last_like_time >= LIKE_INTERVAL:
                like_random_message()
            
            # Sleep to avoid busy waiting
            time.sleep(5)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    run_bot()