"""
ADK Agent with Context Compaction Configuration

This agent demonstrates Google ADK's context compaction feature which
automatically summarizes older conversation events to keep the context
window manageable for long-running conversations.
"""

from google.adk.agents import LlmAgent

# Create the root agent with context compaction enabled
# NOTE: Use a model that has free-tier quota on your account (e.g. gemini-2.5-flash).
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
