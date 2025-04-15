"""
Bot implementations package.

This package contains various bot implementations that can be used with the bot framework.
Each bot is defined in its own file and automatically registered with the BotFactory.
"""

import os
import importlib
import pkgutil
from typing import Dict, Any, List, Type
import logging

from bot_framework import Bot, BotFactory

logger = logging.getLogger(__name__)

# Dictionary to store all bot classes
bot_classes = {}

def register_bot_class(bot_type: str, bot_class: Type[Bot]):
    """
    Register a bot class with the BotFactory
    
    Args:
        bot_type: The type name for the bot
        bot_class: The bot class
    """
    bot_classes[bot_type.lower()] = bot_class
    logger.info(f"Registered bot type: {bot_type}")

def register_all_bots():
    """
    Register all bot classes with the BotFactory
    """
    # Store the original create_bot method
    original_create_bot = BotFactory.create_bot
    
    def extended_create_bot(bot_type: str, config: Dict[str, Any] = None) -> Bot:
        """
        Extended bot factory method that includes all registered bot types
        
        Args:
            bot_type: Type of bot to create
            config: Configuration for the bot
            
        Returns:
            A bot instance
            
        Raises:
            ValueError: If the bot type is not recognized
        """
        bot_type_lower = bot_type.lower()
        
        # Check if we have this bot type registered
        if bot_type_lower in bot_classes:
            return bot_classes[bot_type_lower](config)
        else:
            # Fall back to the original implementation
            return original_create_bot(bot_type, config)
    
    # Replace the factory method
    BotFactory.create_bot = staticmethod(extended_create_bot)
    logger.info("Registered all bot types with the BotFactory")

def get_available_bot_types() -> List[str]:
    """
    Get a list of all available bot types
    
    Returns:
        List of bot type names
    """
    return list(bot_classes.keys())

# Import all modules in this package to register their bot classes
for _, module_name, _ in pkgutil.iter_modules([os.path.dirname(__file__)]):
    try:
        module = importlib.import_module(f"{__name__}.{module_name}")
        logger.info(f"Imported bot module: {module_name}")
    except ImportError as e:
        logger.error(f"Error importing bot module {module_name}: {str(e)}")

# Register all bots with the factory
register_all_bots()