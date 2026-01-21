#!/bin/bash
# Run script for Context Compaction POC

set -e

echo "=========================================="
echo "Google ADK Context Compaction POC"
echo "=========================================="

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check for API key
if [ -z "$GEMINI_API_KEY" ]; then
    echo ""
    echo "WARNING: GEMINI_API_KEY environment variable not set!"
    echo ""
    echo "To get your API key:"
    echo "1. Go to https://aistudio.google.com/apikey"
    echo "2. Create a new API key"
    echo "3. Run: export GEMINI_API_KEY='your-api-key-here'"
    echo ""
    read -p "Enter your GEMINI_API_KEY (or press Enter to skip): " api_key
    if [ -n "$api_key" ]; then
        export GEMINI_API_KEY="$api_key"
    else
        echo "Skipping - you'll need to set GEMINI_API_KEY before running tests"
    fi
fi

echo ""
echo "Running POC..."
echo "=========================================="
python test_adk_context_compaction.py "$@"
