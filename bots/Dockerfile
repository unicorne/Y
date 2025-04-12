FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all bot scripts
COPY *.py .
COPY config.json .

# Environment variables with defaults
ENV API_URL=http://backend:8000
ENV BOT_PASSWORD=password123
ENV POST_INTERVAL=60
ENV LIKE_INTERVAL=30
ENV REPLY_INTERVAL=45
ENV LIKE_PROBABILITY=0.5
ENV REPLY_PROBABILITY=0.3
ENV BOT_COUNT=1
ENV BOT_TYPE=random

# Run the bots
# Default to running a single random bot, but can be overridden with command-line arguments
CMD ["python", "run_bots.py", "--count", "1", "--type", "random"]