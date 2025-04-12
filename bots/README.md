# Social Media Bot Framework

This directory contains a flexible bot framework for the social media application. The bots can post content, like messages, and reply to other users' messages.

## Features

- Object-oriented design with a base `Bot` class that can be extended
- Multiple bot types with different behaviors
- Configurable posting, liking, and replying frequencies
- Probability-based decision making for likes and replies
- Support for running multiple bots simultaneously
- Docker support for easy deployment

## Bot Types

### RandomBot

A simple bot that posts random content and interacts randomly with other users' messages.

### NewsBot

A more advanced bot that scrapes news from various sources and posts them. It has a higher probability of interacting with news-related content.

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

## Dependencies

- requests
- python-dotenv
- beautifulsoup4
- lxml
- multiprocessing-logging