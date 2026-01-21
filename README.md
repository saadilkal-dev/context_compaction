# Google ADK Context Compaction POC

A proof of concept demonstrating context compaction using Google's Agent Development Kit (ADK).

## What is Context Compaction?

Context compaction is a feature in Google ADK that automatically summarizes older conversation events to keep the context window manageable for long-running conversations.

**Key Parameters:**
- `compaction_interval`: Number of completed events that trigger compression (e.g., every 3 events)
- `overlap_size`: How many previously compacted events to include in new compression for continuity

**Example:** With `compaction_interval=3` and `overlap_size=1`, compression happens after events 3, 6, 9, etc., with each new window including 1 event from the previous window.

## Project Structure

```
context_compaction/
├── README.md
├── requirements.txt
├── run_poc.sh                      # Quick start script
├── test_adk_context_compaction.py  # Main POC script (ADK)
├── context_compaction_agent/       # ADK Agent package
│   ├── __init__.py
│   ├── agent.py                    # Agent definition
│   └── tools.py                    # Agent tools
├── simple_gemini_call.py           # Basic Gemini API test
└── test_gemini_context.py          # Raw API context test
```

## Quick Start

### Option 1: Using the run script (recommended)

```bash
chmod +x run_poc.sh
```

### Option 2: Manual setup

1. Create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# or .venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Get your Gemini API key from: https://aistudio.google.com/apikey

4. Set your API key:
```bash
export GEMINI_API_KEY='your-api-key-here'
```

5. Run the POC:
```bash
python test_adk_context_compaction.py
```

## Available Tests

The POC includes several tests:

1. **Basic Memory Retention** - Tests fact storage and recall across turns
2. **Context Filling** - Generates large content to trigger compaction
3. **Multiple Facts** - Stores many facts across an extended conversation
4. **Compare Compaction Intervals** - Tests different interval settings
5. **Interactive Mode** - Manual testing with live chat

## Using the ADK Agent

The agent (`context_compaction_agent`) includes these tools:

- `remember_fact(key, value)` - Store a fact in memory
- `recall_facts(key?)` - Recall stored facts
- `get_memory_stats()` - Get memory statistics
- `generate_long_text(num_paragraphs)` - Generate text to fill context
- `calculate_fibonacci(n)` - Perform calculations

## Running with ADK CLI

You can also use the ADK CLI tools:

```bash
# Interactive web UI
adk web context_compaction_agent

# CLI interface
adk run context_compaction_agent
```

## Legacy Tests (Raw Gemini API)

For basic Gemini API testing without ADK:

```bash
# Simple API call test
python simple_gemini_call.py

# Context retention test
python test_gemini_context.py
```

## How Context Compaction Works

```
Turn 1: User asks question → Agent responds
Turn 2: User asks question → Agent responds
Turn 3: User asks question → Agent responds
        ↓ Compaction triggers (if interval=3)
        → Turns 1-3 summarized into compact form

Turn 4: User asks question → Agent responds (has summary + turn 3)
Turn 5: User asks question → Agent responds
Turn 6: User asks question → Agent responds
        ↓ Compaction triggers again
        → Previous summary + turns 4-6 compacted
```

## Benefits of Context Compaction

- Keeps session contexts manageable for long conversations
- Reduces processing requirements and costs
- Maintains continuity through overlap events
- Optimizes token usage while preserving key information

## Resources

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [Context Compaction Guide](https://google.github.io/adk-docs/context/compaction/)
- [ADK GitHub Repository](https://github.com/google/adk-python)
- [Gemini API Key](https://aistudio.google.com/apikey)
