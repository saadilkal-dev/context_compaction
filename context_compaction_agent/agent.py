"""
ADK Agent with Context Compaction Configuration

This agent demonstrates Google ADK's context compaction feature which
automatically summarizes older conversation events to keep the context
window manageable for long-running conversations.
"""

from google.adk.agents import LlmAgent
from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.apps.llm_event_summarizer import LlmEventSummarizer
from google.adk.models import Gemini

# Create the root agent
root_agent = LlmAgent(
    name="context_compaction_agent",
    model="gemini-2.5-flash",
    description="An agent that demonstrates context compaction capabilities",
    instruction="""You are a helpful assistant designed to test context compaction.

Your job is simple:
1. Have natural conversations with users
2. Remember what users tell you during the conversation
3. When asked to recall information, use your conversation history to answer

DO NOT use any tools. Just respond naturally based on the conversation context.
The context compaction feature will automatically summarize older parts of
the conversation to keep it manageable.

When users share information about themselves, just acknowledge it naturally.
When users ask what you remember, recall from the conversation history.
""",
    tools=[],  # No tools - rely purely on context compaction
)

# Create App with EventsCompactionConfig for deployment
app = App(
    name="context_compaction_agent",
    root_agent=root_agent,
    events_compaction_config=EventsCompactionConfig(
        compaction_interval=3,  # Compact every 3 turns
        overlap_size=1,         # Keep 1 turn overlap for continuity
        summarizer=LlmEventSummarizer(
            llm=Gemini(model="gemini-2.5-flash")
        ),
    ),
)
