#!/usr/bin/env python3
import argparse
import json
import logging
import os
import signal
import sys
import time
import multiprocessing
from typing import Dict, List, Any, Optional
import psutil
import tabulate
import yaml
from datetime import datetime

# Import bot framework and bot implementations
from bot_framework import run_bot, BotFactory
import bot_implementations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("bot_manager")

# Global variables
running_bots = {}
bot_processes = {}
stop_flag = False

def load_config(config_file: str) -> Dict[str, Any]:
    """
    Load bot configuration from a JSON or YAML file
    
    Args:
        config_file: Path to the configuration file
        
    Returns:
        Dictionary with configuration
    """
    try:
        if config_file.endswith('.json'):
            with open(config_file, 'r') as f:
                return json.load(f)
        elif config_file.endswith('.yaml') or config_file.endswith('.yml'):
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        else:
            logger.error(f"Unsupported config file format: {config_file}")
            return {}
    except Exception as e:
        logger.error(f"Error loading config file {config_file}: {str(e)}")
        return {}

def save_config(config: Dict[str, Any], config_file: str) -> bool:
    """
    Save bot configuration to a file
    
    Args:
        config: Configuration dictionary
        config_file: Path to the configuration file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if config_file.endswith('.json'):
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
        elif config_file.endswith('.yaml') or config_file.endswith('.yml'):
            with open(config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
        else:
            logger.error(f"Unsupported config file format: {config_file}")
            return False
        return True
    except Exception as e:
        logger.error(f"Error saving config file {config_file}: {str(e)}")
        return False

def run_bot_process(bot_id: str, bot_type: str, config: Dict[str, Any]):
    """
    Run a bot in a separate process
    
    Args:
        bot_id: Unique identifier for the bot
        bot_type: Type of bot to run
        config: Configuration for the bot
    """
    try:
        # Set the bot ID in the config
        config["bot_id"] = bot_id
        
        # Run the bot
        run_bot(bot_type, config)
    except Exception as e:
        logger.error(f"Error in bot process {bot_id}: {str(e)}")

def start_bot(bot_id: str, bot_type: str, config: Dict[str, Any] = None) -> bool:
    """
    Start a new bot
    
    Args:
        bot_id: Unique identifier for the bot
        bot_type: Type of bot to run
        config: Configuration for the bot
        
    Returns:
        True if successful, False otherwise
    """
    if bot_id in bot_processes:
        logger.warning(f"Bot {bot_id} is already running")
        return False
    
    if config is None:
        config = {}
    
    # Create and start the process
    logger.info(f"Starting bot {bot_id} of type {bot_type}")
    p = multiprocessing.Process(
        target=run_bot_process,
        args=(bot_id, bot_type, config),
        name=f"bot-{bot_id}"
    )
    p.start()
    
    # Store the process
    bot_processes[bot_id] = {
        "process": p,
        "type": bot_type,
        "config": config,
        "start_time": datetime.now(),
        "pid": p.pid
    }
    
    logger.info(f"Bot {bot_id} started with PID {p.pid}")
    return True

def stop_bot(bot_id: str) -> bool:
    """
    Stop a running bot
    
    Args:
        bot_id: Unique identifier for the bot
        
    Returns:
        True if successful, False otherwise
    """
    if bot_id not in bot_processes:
        logger.warning(f"Bot {bot_id} is not running")
        return False
    
    # Get the process
    p = bot_processes[bot_id]["process"]
    pid = p.pid
    
    # Try to terminate the process gracefully
    logger.info(f"Stopping bot {bot_id} (PID {pid})")
    p.terminate()
    
    # Wait for the process to terminate
    p.join(5)
    
    # If the process is still alive, kill it
    if p.is_alive():
        logger.warning(f"Bot {bot_id} did not terminate gracefully, killing it")
        p.kill()
        p.join(1)
    
    # Remove the process from the dictionary
    del bot_processes[bot_id]
    
    logger.info(f"Bot {bot_id} stopped")
    return True

def stop_all_bots():
    """Stop all running bots"""
    logger.info("Stopping all bots")
    for bot_id in list(bot_processes.keys()):
        stop_bot(bot_id)

def get_bot_status(bot_id: str) -> Dict[str, Any]:
    """
    Get the status of a bot
    
    Args:
        bot_id: Unique identifier for the bot
        
    Returns:
        Dictionary with bot status
    """
    if bot_id not in bot_processes:
        return {"status": "not_running"}
    
    bot_info = bot_processes[bot_id]
    p = bot_info["process"]
    
    # Check if the process is still running
    if not p.is_alive():
        return {"status": "crashed", "exit_code": p.exitcode}
    
    # Get process info
    try:
        process = psutil.Process(p.pid)
        cpu_percent = process.cpu_percent(interval=0.1)
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / (1024 * 1024)  # Convert to MB
        
        # Calculate uptime
        uptime = datetime.now() - bot_info["start_time"]
        uptime_str = str(uptime).split('.')[0]  # Remove microseconds
        
        return {
            "status": "running",
            "type": bot_info["type"],
            "pid": p.pid,
            "cpu_percent": cpu_percent,
            "memory_mb": memory_mb,
            "uptime": uptime_str,
            "start_time": bot_info["start_time"].strftime("%Y-%m-%d %H:%M:%S")
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return {"status": "unknown"}

def list_bots() -> List[Dict[str, Any]]:
    """
    List all running bots
    
    Returns:
        List of dictionaries with bot information
    """
    bot_list = []
    for bot_id in bot_processes:
        status = get_bot_status(bot_id)
        status["id"] = bot_id
        bot_list.append(status)
    return bot_list

def print_bot_list():
    """Print a table of running bots"""
    bots = list_bots()
    if not bots:
        print("No bots running")
        return
    
    # Prepare table data
    headers = ["ID", "Type", "Status", "PID", "CPU %", "Memory (MB)", "Uptime"]
    table_data = []
    
    for bot in bots:
        if bot["status"] == "running":
            row = [
                bot["id"],
                bot["type"],
                bot["status"],
                bot["pid"],
                f"{bot['cpu_percent']:.1f}",
                f"{bot['memory_mb']:.1f}",
                bot["uptime"]
            ]
        else:
            row = [
                bot["id"],
                bot.get("type", "unknown"),
                bot["status"],
                bot.get("pid", "N/A"),
                "N/A",
                "N/A",
                "N/A"
            ]
        table_data.append(row)
    
    # Print the table
    print(tabulate.tabulate(table_data, headers=headers, tablefmt="grid"))

def load_bot_config(config_file: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Load bot configuration from a file
    
    Args:
        config_file: Path to the configuration file
        
    Returns:
        Dictionary with bot configurations
    """
    config = load_config(config_file)
    if not config:
        return {"bots": []}
    
    if "bots" not in config:
        config["bots"] = []
    
    return config

def save_bot_config(config: Dict[str, List[Dict[str, Any]]], config_file: str) -> bool:
    """
    Save bot configuration to a file
    
    Args:
        config: Bot configuration dictionary
        config_file: Path to the configuration file
        
    Returns:
        True if successful, False otherwise
    """
    return save_config(config, config_file)

def start_bots_from_config(config_file: str) -> int:
    """
    Start bots from a configuration file
    
    Args:
        config_file: Path to the configuration file
        
    Returns:
        Number of bots started
    """
    config = load_bot_config(config_file)
    if not config or "bots" not in config:
        logger.error(f"Invalid configuration file: {config_file}")
        return 0
    
    bots_started = 0
    for bot_config in config["bots"]:
        if "id" not in bot_config or "type" not in bot_config:
            logger.warning("Bot configuration missing required fields (id, type)")
            continue
        
        bot_id = bot_config["id"]
        bot_type = bot_config["type"]
        
        # Extract the bot-specific configuration
        bot_specific_config = bot_config.get("config", {})
        
        # Start the bot
        if start_bot(bot_id, bot_type, bot_specific_config):
            bots_started += 1
    
    return bots_started

def signal_handler(sig, frame):
    """Handle signals to gracefully shut down"""
    global stop_flag
    if not stop_flag:
        logger.info("Received signal to stop, shutting down...")
        stop_flag = True
        stop_all_bots()
        sys.exit(0)

def interactive_mode():
    """Run the bot manager in interactive mode"""
    global stop_flag
    
    print("Bot Manager Interactive Mode")
    print("Type 'help' for a list of commands")
    
    while not stop_flag:
        try:
            command = input("> ").strip()
            if not command:
                continue
            
            parts = command.split()
            cmd = parts[0].lower()
            
            if cmd == "help":
                print("Available commands:")
                print("  list                     - List all running bots")
                print("  start <id> <type>        - Start a new bot")
                print("  stop <id>                - Stop a running bot")
                print("  stopall                  - Stop all running bots")
                print("  status <id>              - Get detailed status of a bot")
                print("  load <file>              - Load and start bots from a config file")
                print("  save <file>              - Save current bot configuration to a file")
                print("  types                    - List available bot types")
                print("  help                     - Show this help message")
                print("  exit                     - Exit the bot manager")
            
            elif cmd == "list":
                print_bot_list()
            
            elif cmd == "start" and len(parts) >= 3:
                bot_id = parts[1]
                bot_type = parts[2]
                config = {}
                
                # Parse additional config parameters
                for i in range(3, len(parts)):
                    if "=" in parts[i]:
                        key, value = parts[i].split("=", 1)
                        # Try to convert to appropriate type
                        try:
                            if value.lower() == "true":
                                value = True
                            elif value.lower() == "false":
                                value = False
                            elif value.isdigit():
                                value = int(value)
                            elif "." in value and all(p.isdigit() for p in value.split(".")):
                                value = float(value)
                        except:
                            pass
                        config[key] = value
                
                if start_bot(bot_id, bot_type, config):
                    print(f"Bot {bot_id} started")
                else:
                    print(f"Failed to start bot {bot_id}")
            
            elif cmd == "stop" and len(parts) == 2:
                bot_id = parts[1]
                if stop_bot(bot_id):
                    print(f"Bot {bot_id} stopped")
                else:
                    print(f"Failed to stop bot {bot_id}")
            
            elif cmd == "stopall":
                stop_all_bots()
                print("All bots stopped")
            
            elif cmd == "status" and len(parts) == 2:
                bot_id = parts[1]
                status = get_bot_status(bot_id)
                if status["status"] == "not_running":
                    print(f"Bot {bot_id} is not running")
                else:
                    print(f"Bot {bot_id} status:")
                    for key, value in status.items():
                        print(f"  {key}: {value}")
            
            elif cmd == "load" and len(parts) == 2:
                config_file = parts[1]
                bots_started = start_bots_from_config(config_file)
                print(f"Started {bots_started} bots from {config_file}")
            
            elif cmd == "save" and len(parts) == 2:
                config_file = parts[1]
                
                # Create a configuration with all running bots
                config = {"bots": []}
                for bot_id, bot_info in bot_processes.items():
                    config["bots"].append({
                        "id": bot_id,
                        "type": bot_info["type"],
                        "config": bot_info["config"]
                    })
                
                if save_bot_config(config, config_file):
                    print(f"Bot configuration saved to {config_file}")
                else:
                    print(f"Failed to save bot configuration to {config_file}")
            
            elif cmd == "types":
                # Get available bot types from the bot_implementations package
                bot_types = bot_implementations.get_available_bot_types()
                
                print("Available bot types:")
                for bot_type in sorted(bot_types):
                    print(f"  {bot_type}")
            
            elif cmd == "exit":
                print("Exiting...")
                stop_all_bots()
                stop_flag = True
                break
            
            else:
                print("Unknown command. Type 'help' for a list of commands.")
        
        except KeyboardInterrupt:
            print("\nExiting...")
            stop_all_bots()
            stop_flag = True
            break
        
        except Exception as e:
            print(f"Error: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Bot Manager')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--interactive', action='store_true', help='Run in interactive mode')
    args = parser.parse_args()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start bots from config file if provided
    if args.config:
        bots_started = start_bots_from_config(args.config)
        logger.info(f"Started {bots_started} bots from {args.config}")
    
    # Run in interactive mode if requested
    if args.interactive:
        interactive_mode()
    elif args.config:
        # If not interactive but config provided, keep running and monitoring
        logger.info("Bot Manager running in monitoring mode. Press Ctrl+C to exit.")
        try:
            while not stop_flag:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
            stop_all_bots()
    else:
        # If no config and not interactive, print help and exit
        parser.print_help()

if __name__ == "__main__":
    main()