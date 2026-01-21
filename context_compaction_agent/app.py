"""
App configuration with Context Compaction enabled.

Run with: adk web context_compaction_agent

NOTE: For Vertex AI Agent Engine deployment, the explicit summarizer
is required to ensure context compaction works properly.
"""

from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.apps.llm_event_summarizer import LlmEventSummarizer
from google.adk.models import Gemini

from .agent import root_agent

# Create an explicit summarizer for context compaction
# This is REQUIRED for Vertex AI Agent Engine deployment
# The summarizer uses the same model as the agent to maintain consistency
compaction_summarizer = LlmEventSummarizer(
    llm=Gemini(model="gemini-2.5-flash")
)

# Create App with context compaction
app = App(
    name="context_compaction_agent",
    root_agent=root_agent,
    events_compaction_config=EventsCompactionConfig(
        compaction_interval=3,  # Compact every 3 turns
        overlap_size=1,         # Keep 1 turn overlap
        summarizer=compaction_summarizer,  # Explicit summarizer for Vertex AI
    ),
)
