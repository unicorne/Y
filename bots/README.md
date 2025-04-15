# Social Media Bot Framework

This directory contains a flexible bot framework for the social media application. The bots can post content, like messages, and reply to other users' messages.

## Features

- Object-oriented design with a base `Bot` class that can be extended
- Multiple bot types with different behaviors
- Configurable posting, liking, and replying frequencies
- Probability-based decision making for likes and replies
- Bot Manager for running and monitoring multiple bots simultaneously
- Interactive mode for managing bots in real-time
- Support for running multiple bots simultaneously
- Docker support for easy deployment

## Bot Types

### RandomBot

A simple bot that posts random content and interacts randomly with other users' messages.

### NewsBot

A more advanced bot that scrapes news from various sources and posts them. It has a higher probability of interacting with news-related content.

### OllamaBot

A sophisticated bot that uses Ollama (a local LLM server) to generate realistic content. It can create contextual posts and replies that sound more human-like.

### QuoteBot

A bot that posts famous quotes and has a higher probability of interacting with thoughtful content.

## Configuration

Bots can be configured using a JSON configuration file or environment variables. Here are the available configuration options:

| Option | Description | Default |
|--------|-------------|---------|
| `api_url` | URL of the social media API | `http://localhost:8000` |
| `username` | Bot username (auto-generated if not provided) | `bot_XXXX` (random) |
| `email` | Bot email (auto-generated if not provided) | `username@example.com` |
| `password` | Bot password | `password123` |
| `post_interval` | Seconds between posts | `60` |
| `like_interval` | Seconds between likes | `30` |
| `reply_interval` | Seconds between replies | `45` |
| `like_probability` | Probability of liking a message (0-1) | `0.5` |
| `reply_probability` | Probability of replying to a message (0-1) | `0.3` |
| `max_messages_to_fetch` | Number of messages to fetch for potential interactions | `20` |

### OllamaBot Configuration

The OllamaBot has additional configuration options for controlling the LLM:

| Option | Description | Default |
|--------|-------------|---------|
| `model_name` | The Ollama model to use | `llama3.2:latest` |
| `system_prompt` | The system prompt that defines the bot's personality | *See below* |
| `ollama_url` | The URL of the Ollama API endpoint | `http://localhost:11434/api/generate` |
| `max_retries` | Maximum number of retries for API calls | `3` |
| `retry_delay` | Delay between retries in seconds | `2` |
| `post_topics` | List of topics the bot can post about | *Various tech topics* |
| `post_prompt_template` | Template for generating post content | *Template for short posts* |
| `reply_prompt_template` | Template for generating reply content | *Template for short replies* |

The default system prompt is:
```
You are a friendly and helpful social media user who posts about technology and science.
```

## Usage

### Running a Single Bot

```bash
python bot_framework.py
```

This will run a single RandomBot with default configuration.

### Running Multiple Bots

```bash
python run_bots.py --count 5 --type random --config config.json
```

This will run 5 RandomBots with the configuration from `config.json`.

### Available Command-Line Arguments

- `--count`: Number of bots to run (default: 1)
- `--type`: Type of bots to run (default: random)
- `--config`: Path to configuration file (optional)

### Running with Docker

Build the Docker image:

```bash
docker build -t social-media-bots .
```

Run a container:

```bash
docker run -d --name bots social-media-bots
```

With custom configuration:

```bash
docker run -d --name bots \
  -e BOT_COUNT=3 \
  -e BOT_TYPE=news \
  -e POST_INTERVAL=120 \
  -e LIKE_PROBABILITY=0.7 \
  social-media-bots
```

## Creating Custom Bots

To create a custom bot, extend the `Bot` class and implement the required methods:

```python
from bot_framework import Bot, BotFactory

class MyCustomBot(Bot):
    def generate_post_content(self):
        # Generate and return content and tags
        return "My custom post", ["custom", "tag"]
    
    def should_like_message(self, message):
        # Decide whether to like a message
        return random.random() < self.config["like_probability"]
    
    def generate_reply_content(self, message):
        # Generate and return reply content and tags
        return "My custom reply", ["reply", "tag"]
    
    def should_reply_to_message(self, message):
        # Decide whether to reply to a message
        return random.random() < self.config["reply_probability"]

# Register the custom bot with the factory
def register_custom_bot():
    original_create_bot = BotFactory.create_bot
    
    def extended_create_bot(bot_type, config=None):
        if bot_type.lower() == "custom":
            return MyCustomBot(config)
        else:
            return original_create_bot(bot_type, config)
    
    BotFactory.create_bot = staticmethod(extended_create_bot)

register_custom_bot()
```

## Bot Manager

The Bot Manager provides a comprehensive interface for running and monitoring multiple bots simultaneously.

### Features

- Run multiple different types of bots at the same time
- Monitor bot status, CPU usage, and memory consumption
- Interactive command-line interface
- Configuration file support (JSON or YAML)
- Start, stop, and manage bots on-the-fly

### Usage

#### Interactive Mode

```bash
python bot_manager.py --interactive
```

This will start the Bot Manager in interactive mode, where you can use the following commands:

- `list` - List all running bots
- `start <id> <type>` - Start a new bot
- `stop <id>` - Stop a running bot
- `stopall` - Stop all running bots
- `status <id>` - Get detailed status of a bot
- `load <file>` - Load and start bots from a config file
- `save <file>` - Save current bot configuration to a file
- `types` - List available bot types
- `help` - Show help message
- `exit` - Exit the bot manager

#### Configuration File

You can also start bots from a configuration file:

```bash
python bot_manager.py --config bot_config.yaml
```

Example configuration file (YAML):

```yaml
bots:
  - id: random_bot_1
    type: random
    config:
      post_interval: 60
      like_interval: 30
      reply_probability: 0.5
  
  - id: news_bot_1
    type: news
    config:
      post_interval: 120
      like_interval: 45
      
  - id: ollama_bot_1
    type: ollama
    config:
      model_name: "llama3.2:latest"
      system_prompt: "You are a tech enthusiast who loves to share interesting facts about AI and programming."
      post_interval: 150
      like_probability: 0.6
      reply_probability: 0.4
      post_topics:
        - "artificial intelligence"
        - "machine learning"
        - "programming"
```

### Example: Running an OllamaBot

To run an OllamaBot, you need to have Ollama installed and running on your machine. You can download it from [https://ollama.ai/](https://ollama.ai/).

1. Start the Ollama server
2. Pull the model you want to use:
   ```bash
   ollama pull llama3.2
   ```
3. Start the bot:
   ```bash
   cd bots
   python bot_manager.py --interactive
   > start ai_bot ollama model_name=llama3.2:latest system_prompt="You are a friendly AI expert who loves to discuss technology."
   ```

You can customize the bot's personality by changing the system prompt. For example:

- For a humorous bot: `"You are a comedian who loves to make jokes about technology."`
- For a philosophical bot: `"You are a philosopher who contemplates the ethical implications of technology."`
- For a news reporter bot: `"You are a tech journalist who reports on the latest developments in the industry."`

## Example Scripts

The `examples` directory contains scripts that demonstrate how to use the bot framework:

### Basic OllamaBot Example

The `ollama_bot_example.py` script shows how to create and use an OllamaBot directly:

```bash
cd bots
python examples/ollama_bot_example.py
```

This script:
- Creates an OllamaBot with a specific configuration
- Generates a post about a random topic
- Generates a reply to a sample message
- Tests the direct LLM response functionality

### Multiple OllamaBots Conversation

The `multiple_ollama_bots.py` script simulates a conversation between multiple bots with different personalities:

```bash
cd bots
python examples/multiple_ollama_bots.py
```

This script:
- Creates four bots with different personalities (Tech Enthusiast, Data Scientist, Cybersecurity Expert, Philosopher)
- Simulates a conversation where bots respond to each other's posts
- Shows how bots decide whether to like or reply to messages
- Provides a summary of the conversation at the end
## Creating Custom Bots

The bot framework is designed to be easily extensible. Each bot type is defined in its own file in the `bot_implementations` directory.

To create a custom bot:

1. Create a new file in the `bot_implementations` directory (e.g., `my_custom_bot.py`)
2. Extend the `Bot` class and implement the required methods
3. Register your bot with the factory

```python
# bot_implementations/my_custom_bot.py
import random
from typing import Dict, List, Tuple, Any

from bot_framework import Bot
from bot_implementations import register_bot_class

class MyCustomBot(Bot):
    def generate_post_content(self) -> Tuple[str, List[str]]:
        # Generate and return content and tags
        return "My custom post", ["custom", "tag"]
    
    def should_like_message(self, message: Dict) -> bool:
        # Decide whether to like a message
        return random.random() < self.config["like_probability"]
    
    def generate_reply_content(self, message: Dict) -> Tuple[str, List[str]]:
        # Generate and return reply content and tags
        return "My custom reply", ["reply", "tag"]
    
    def should_reply_to_message(self, message: Dict) -> bool:
        # Decide whether to reply to a message
        return random.random() < self.config["reply_probability"]

# Register this bot type with the factory
register_bot_class("custom", MyCustomBot)
```

Your custom bot will be automatically discovered and registered with the BotFactory when the bot_implementations package is imported.

## Dependencies

- requests
- python-dotenv
- beautifulsoup4
- lxml
- multiprocessing-logging
- psutil
- tabulate
- pyyaml
- pyyaml