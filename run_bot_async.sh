#!/bin/bash

# Optional: activate virtual environment
source .venv/bin/activate

echo "🚀 Starting multi-symbol trading bots..."
# cd "$(dirname "$0")"
python3 live_bot/async_main.py