import argparse
import json
import logging
import os
import random
import time
import multiprocessing
from typing import Dict, Any, List
from bot_framework import run_bot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("bot_runner")

def load_config(config_file: str) -> Dict[str, Any]:
    """
    Load bot configuration from a JSON file
    
    Args:
        config_file: Path to the configuration file
        
    Returns:
        Dictionary with configuration
    """
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config file {config_file}: {str(e)}")
        return {}

def run_bot_process(bot_type: str, config: Dict[str, Any]):
    """
    Run a bot in a separate process
    
    Args:
        bot_type: Type of bot to run
        config: Configuration for the bot
    """
    try:
        # Add some randomness to the intervals to avoid all bots posting at the same time
        if "post_interval" in config:
            config["post_interval"] += random.randint(-5, 5)
            config["post_interval"] = max(10, config["post_interval"])  # Ensure minimum interval
            
        if "like_interval" in config:
            config["like_interval"] += random.randint(-3, 3)
            config["like_interval"] = max(5, config["like_interval"])  # Ensure minimum interval
            
        if "reply_interval" in config:
            config["reply_interval"] += random.randint(-4, 4)
            config["reply_interval"] = max(7, config["reply_interval"])  # Ensure minimum interval
        
        # Run the bot
        run_bot(bot_type, config)
    except Exception as e:
        logger.error(f"Error in bot process: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Run multiple social media bots')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--count', type=int, default=1, help='Number of bots to run')
    parser.add_argument('--type', type=str, default='random', help='Type of bots to run')
    args = parser.parse_args()
    
    # Load configuration
    config = {}
    if args.config:
        config = load_config(args.config)
    
    # Create and run bots
    processes = []
    for i in range(args.count):
        # Create a copy of the config for each bot
        bot_config = config.copy()
        
        # Add a unique username for each bot
        bot_config["username"] = f"{args.type}_bot_{i+1}_{random.randint(1000, 9999)}"
        
        # Create and start the process
        logger.info(f"Starting bot {i+1}/{args.count}: {bot_config['username']}")
        p = multiprocessing.Process(
            target=run_bot_process,
            args=(args.type, bot_config)
        )
        p.start()
        processes.append(p)
        
        # Small delay between starting bots to avoid overwhelming the server
        time.sleep(1)
    
    logger.info(f"Started {len(processes)} bots")
    
    try:
        # Wait for all processes to finish (which they won't unless they crash)
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        logger.info("Stopping all bots...")
        for p in processes:
            p.terminate()
        
        # Wait for all processes to terminate
        for p in processes:
            p.join()
            
        logger.info("All bots stopped")

if __name__ == "__main__":
    main()