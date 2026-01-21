"""
App configuration with Context Compaction enabled.

Run with: adk web context_compaction_agent
"""

from google.adk.apps.app import App, EventsCompactionConfig
from .agent import root_agent

# Create App with context compaction
app = App(
    name="context_compaction_agent",
    root_agent=root_agent,
    events_compaction_config=EventsCompactionConfig(
        compaction_interval=3,  # Compact every 3 turns
        overlap_size=1,         # Keep 1 turn overlap
    ),
)
