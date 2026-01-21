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

The agent (`context_compaction_agent`) includes:

- **Memory Bank** (`PreloadMemoryTool`) - Automatically retrieves relevant memories from past sessions at the start of each turn
- **Context Compaction** - Automatically summarizes older conversation turns to keep context manageable

When deployed to Agent Engine, Memory Bank uses **Vertex AI Memory Bank** for persistent, cross-session memory. Locally, it uses in-memory storage for testing.

## Running with ADK CLI

You can also use the ADK CLI tools:

```bash
# Interactive web UI
adk web context_compaction_agent

# CLI interface
adk run context_compaction_agent
```

## Deploying to Vertex AI Agent Engine

### Prerequisites

- Enable APIs: **Vertex AI API** + **Cloud Resource Manager API**
- Create a GCS staging bucket (example: `gs://my-agent-engine-staging`)
- Auth locally:

```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

### Install deploy dependency

This repo includes it in `requirements.txt`:

- `google-cloud-aiplatform[adk,agent_engines]>=1.111.0`

### Deploy (recommended)

### Observability / Telemetry (recommended)

To populate the Agent Engine observability dashboard (OpenTelemetry traces/logs), set:

```bash
export ENABLE_TELEMETRY=true
export TRACE_TO_CLOUD=true
```

To also capture full prompt + response content (may include sensitive data/PII), set:

```bash
export CAPTURE_MESSAGE_CONTENT=true
```


```bash
export PROJECT_ID=YOUR_PROJECT_ID
export REGION=us-central1
export STAGING_BUCKET=gs://YOUR_BUCKET
# optional
export DISPLAY_NAME=context-compaction-agent

./deploy_agent_engine.sh
```

### Deploy (manual CLI)

```bash
adk deploy agent_engine \
  --project=YOUR_PROJECT_ID \
  --region=us-central1 \
  --staging_bucket=gs://YOUR_BUCKET \
  --display_name="context-compaction-agent" \
  context_compaction_agent
```

> Note: On Agent Engine, authentication uses Google Cloud credentials (ADC/service account). You typically do **not** use `GEMINI_API_KEY` for production deployments.

> **Memory Bank**: When deployed to Agent Engine, the agent automatically uses **Vertex AI Memory Bank** for persistent, cross-session memory. The `PreloadMemoryTool` enables automatic memory retrieval at the start of each turn.


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
