#!/usr/bin/env python3
"""
Example script demonstrating how to run multiple OllamaBots with different personalities.

This script creates multiple OllamaBot instances with different system prompts
and configurations, then simulates a conversation between them.

Prerequisites:
- Ollama must be installed and running
- The specified model must be available in Ollama

Usage:
    python multiple_ollama_bots.py
"""

import sys
import os
import logging
import time
import random
from typing import Dict, List, Any

# Add the parent directory to the path so we can import the bot modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bot_implementations.ollama_bot import OllamaBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("multiple_ollama_bots")

# Define different bot personalities
BOT_PERSONALITIES = [
    {
        "name": "Tech Enthusiast",
        "system_prompt": "You are a tech enthusiast who loves to discuss the latest gadgets and technology trends. You're excited about innovation and always optimistic about the future of tech.",
        "topics": ["gadgets", "technology trends", "innovation", "future tech", "smart devices"]
    },
    {
        "name": "Data Scientist",
        "system_prompt": "You are a data scientist who specializes in machine learning and AI. You enjoy discussing technical concepts and sharing insights about data analysis and predictive modeling.",
        "topics": ["machine learning", "data analysis", "AI ethics", "neural networks", "big data"]
    },
    {
        "name": "Cybersecurity Expert",
        "system_prompt": "You are a cybersecurity expert who is concerned about online privacy and security. You often warn about potential threats and provide tips for staying safe online.",
        "topics": ["cybersecurity", "privacy", "hacking", "data protection", "secure coding"]
    },
    {
        "name": "Philosopher",
        "system_prompt": "You are a philosopher who contemplates the ethical implications of technology. You ask deep questions about how tech is changing society and human relationships.",
        "topics": ["ethics", "philosophy of technology", "digital society", "human-computer interaction", "technological determinism"]
    }
]

def create_bots(model_name: str = "llama3.2:latest") -> List[Dict[str, Any]]:
    """
    Create multiple OllamaBot instances with different personalities
    
    Args:
        model_name: The Ollama model to use
        
    Returns:
        List of dictionaries containing bot name and instance
    """
    bots = []
    
    for personality in BOT_PERSONALITIES:
        # Create a configuration for this bot
        config = {
            "model_name": model_name,
            "system_prompt": personality["system_prompt"],
            "ollama_url": "http://localhost:11434/api/generate",
            "post_topics": personality["topics"],
            "like_probability": 0.7,
            "reply_probability": 0.8
        }
        
        try:
            # Create an OllamaBot instance
            bot = OllamaBot(config)
            bots.append({
                "name": personality["name"],
                "instance": bot,
                "personality": personality
            })
            logger.info(f"Created bot: {personality['name']}")
        except Exception as e:
            logger.error(f"Error creating bot {personality['name']}: {str(e)}")
    
    return bots

def simulate_conversation(bots: List[Dict[str, Any]], num_rounds: int = 3):
    """
    Simulate a conversation between multiple bots
    
    Args:
        bots: List of bot dictionaries
        num_rounds: Number of conversation rounds
    """
    if not bots:
        logger.error("No bots available for conversation")
        return
    
    # Start with a random bot posting
    current_bot = random.choice(bots)
    print(f"\n=== {current_bot['name']} starts the conversation ===")
    
    # Generate the initial post
    content, tags = current_bot["instance"].generate_post_content()
    
    # Create a message object
    message = {
        "id": 1,
        "content": content,
        "user_id": 1,
        "username": current_bot["name"],
        "tags": [{"id": i+1, "name": tag} for i, tag in enumerate(tags)],
        "like_count": 0
    }
    
    print(f"{current_bot['name']}: {content}")
    print(f"Tags: {', '.join(tags)}")
    print()
    
    # Keep track of messages
    messages = [message]
    message_id = 2
    
    # Simulate conversation rounds
    for round_num in range(num_rounds):
        print(f"=== Round {round_num + 1} ===")
        
        # Each bot gets a chance to respond to the last message
        for bot in bots:
            # Skip the bot that posted the last message
            if bot["name"] == current_bot["name"]:
                continue
            
            # Decide whether to like the message
            if bot["instance"].should_like_message(message):
                print(f"{bot['name']} liked the message from {current_bot['name']}")
                message["like_count"] += 1
            
            # Decide whether to reply to the message
            if bot["instance"].should_reply_to_message(message):
                # Generate a reply
                reply_content, reply_tags = bot["instance"].generate_reply_content(message)
                
                # Create a new message object for the reply
                reply_message = {
                    "id": message_id,
                    "content": reply_content,
                    "user_id": bots.index(bot) + 2,
                    "username": bot["name"],
                    "tags": [{"id": i+1, "name": tag} for i, tag in enumerate(reply_tags)],
                    "like_count": 0
                }
                
                print(f"{bot['name']} replies: {reply_content}")
                print(f"Tags: {', '.join(reply_tags)}")
                print()
                
                # Update tracking variables
                messages.append(reply_message)
                message_id += 1
                message = reply_message
                current_bot = bot
                
                # Add a small delay to make the output more readable
                time.sleep(0.5)
    
    # Print conversation summary
    print("\n=== Conversation Summary ===")
    print(f"Total messages: {len(messages)}")
    print(f"Total likes: {sum(m['like_count'] for m in messages)}")
    
    # Find the most popular message
    if messages:
        most_popular = max(messages, key=lambda m: m["like_count"])
        print(f"\nMost popular message ({most_popular['like_count']} likes):")
        print(f"{most_popular['username']}: {most_popular['content']}")

def main():
    try:
        # Create bots with the specified model
        model_name = "llama3.2:latest"  # Change this to a model you have installed
        print(f"Creating bots using model: {model_name}")
        bots = create_bots(model_name)
        
        if not bots:
            print("No bots were created. Check the logs for errors.")
            return 1
        
        print(f"Created {len(bots)} bots with different personalities:")
        for bot in bots:
            print(f"- {bot['name']}")
        
        # Simulate a conversation between the bots
        print("\nSimulating conversation...")
        simulate_conversation(bots, num_rounds=3)
        
    except Exception as e:
        logger.error(f"Error in example: {str(e)}")
        print(f"\nError: {str(e)}")
        print("\nMake sure Ollama is running and the specified model is available.")
        print("You can install Ollama from: https://ollama.ai/")
        print("And pull a model with: ollama pull llama3.2")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())