#!/usr/bin/env python3
"""
Example script demonstrating how to use the OllamaBot directly.

This script creates an OllamaBot instance and generates a post and a reply
using the Ollama API.

Prerequisites:
- Ollama must be installed and running
- The specified model must be available in Ollama

Usage:
    python ollama_bot_example.py
"""

import sys
import os
import logging

# Add the parent directory to the path so we can import the bot modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bot_implementations.ollama_bot import OllamaBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ollama_example")

def main():
    # Create a configuration for the OllamaBot
    config = {
        "model_name": "llama3.2:latest",  # Change this to a model you have installed
        "system_prompt": "You are a friendly AI expert who loves to discuss technology.",
        "ollama_url": "http://localhost:11434/api/generate",
        "post_interval": 60,
        "like_interval": 30,
        "reply_interval": 45,
        "like_probability": 0.5,
        "reply_probability": 0.3,
        "post_topics": [
            "artificial intelligence",
            "machine learning",
            "programming",
            "data science",
            "technology trends"
        ]
    }
    
    try:
        # Create an OllamaBot instance
        bot = OllamaBot(config)
        
        # Generate a post
        print("\n=== Generating a post ===")
        content, tags = bot.generate_post_content()
        print(f"Content: {content}")
        print(f"Tags: {tags}")
        
        # Generate a reply to a sample message
        print("\n=== Generating a reply ===")
        sample_message = {
            "content": "I've been learning about machine learning lately. It's fascinating how neural networks can recognize patterns!",
            "tags": [{"name": "machinelearning"}, {"name": "ai"}]
        }
        
        reply_content, reply_tags = bot.generate_reply_content(sample_message)
        print(f"Original message: {sample_message['content']}")
        print(f"Reply: {reply_content}")
        print(f"Reply tags: {reply_tags}")
        
        # Test the LLM response directly
        print("\n=== Testing direct LLM response ===")
        prompt = "What are three interesting applications of AI in healthcare?"
        response = bot.get_llm_response(prompt)
        print(f"Prompt: {prompt}")
        print(f"Response: {response}")
        
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