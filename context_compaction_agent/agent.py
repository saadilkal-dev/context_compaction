"""
ADK Agent with Context Compaction Configuration

This agent demonstrates Google ADK's context compaction feature which
automatically summarizes older conversation events to keep the context
window manageable for long-running conversations.

Memory Bank is enabled via PreloadMemoryTool, which allows the agent to:
- Retrieve relevant memories from past sessions
- Persist memories across sessions when deployed to Agent Engine
"""

from google.adk.agents import LlmAgent
from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.tools.preload_memory_tool import PreloadMemoryTool

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
4. Use your memory to recall information from past conversations when relevant

The context compaction feature will automatically summarize older parts of
the conversation to keep it manageable. Memory Bank allows you to remember
important information across sessions.

When users share information about themselves, acknowledge it naturally and
remember it for future conversations. When users ask what you remember,
recall from both the current conversation history and your memory.
""",
    tools=[PreloadMemoryTool()],  # Enable Memory Bank - retrieves relevant memories at start of each turn
)

# Create App with EventsCompactionConfig for deployment
# Note: Not specifying summarizer lets ADK use its default summarizer
app = App(
    name="context_compaction_agent",
    root_agent=root_agent,
    events_compaction_config=EventsCompactionConfig(
        compaction_interval=3,  # Compact every 3 turns
        overlap_size=1,         # Keep 1 turn overlap for continuity
    ),
)
