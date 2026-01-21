#!/usr/bin/env python3
"""
Proof of Concept: Testing Context Compaction with Google ADK

This script demonstrates how Google ADK's context compaction feature works.
Context compaction automatically summarizes older conversation events to keep
the context window manageable for long-running conversations.

Key concepts:
- compaction_interval: How many events trigger compression (e.g., every 3 events)
- overlap_size: How many previously compacted events to include in new compression

Usage:
    export GEMINI_API_KEY='your-api-key'
    python test_adk_context_compaction.py
"""

import asyncio
import os
import sys
from typing import Optional

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.events import Event
from google.adk.apps.app import App, EventsCompactionConfig
from google.genai import types

# Import our agent
from context_compaction_agent import root_agent


def check_api_key() -> str:
    """Check for API key and provide setup instructions if missing."""
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("=" * 80)
        print("ERROR: GEMINI_API_KEY environment variable not set")
        print("=" * 80)
        print("\nTo get your API key:")
        print("1. Go to https://aistudio.google.com/apikey")
        print("2. Create a new API key")
        print("3. Set the environment variable:")
        print("   export GEMINI_API_KEY='your-api-key-here'")
        print("\nThen run this script again.")
        sys.exit(1)
    return api_key


async def run_conversation_with_compaction(
    messages: list[str],
    compaction_interval: int = 3,
    overlap_size: int = 1,
    verbose: bool = True,
    track_tokens: bool = False
) -> dict:
    """
    Run a conversation with context compaction enabled.

    Args:
        messages: List of user messages to send
        compaction_interval: Number of events before compaction triggers
        overlap_size: Number of events to overlap between compaction windows
        verbose: Whether to print detailed output
        track_tokens: Whether to track and display token usage

    Returns:
        Dictionary with responses and token stats
    """
    # Create session service
    session_service = InMemorySessionService()

    # Create App with context compaction configuration
    app = App(
        name="context_compaction_poc",
        root_agent=root_agent,
        events_compaction_config=EventsCompactionConfig(
            compaction_interval=compaction_interval,
            overlap_size=overlap_size,
        ),
    )

    # Create Runner with the App and session service
    runner = Runner(
        app=app,
        session_service=session_service,
    )

    # Create a new session
    session = await session_service.create_session(
        app_name="context_compaction_poc",
        user_id="test_user",
    )

    responses = []
    token_stats = []
    total_prompt_tokens = 0
    total_response_tokens = 0

    if verbose:
        print(f"\nSession created: {session.id}")
        print(f"Compaction interval: {compaction_interval}")
        print(f"Overlap size: {overlap_size}")
        print("-" * 80)

    for i, message in enumerate(messages, 1):
        if verbose:
            print(f"\n[Turn {i}] User: {message[:200]}{'...' if len(message) > 200 else ''}")

        # Run the agent with the message
        response_text = ""
        turn_prompt_tokens = 0
        turn_response_tokens = 0
        turn_total_tokens = 0

        async for event in runner.run_async(
            user_id="test_user",
            session_id=session.id,
            new_message=types.Content(
                role="user",
                parts=[types.Part(text=message)]
            ),
        ):
            # Collect token usage from event
            if track_tokens and hasattr(event, 'usage_metadata') and event.usage_metadata:
                um = event.usage_metadata
                if hasattr(um, 'prompt_token_count') and um.prompt_token_count is not None:
                    turn_prompt_tokens = um.prompt_token_count
                if hasattr(um, 'response_token_count') and um.response_token_count is not None:
                    turn_response_tokens = um.response_token_count
                if hasattr(um, 'total_token_count') and um.total_token_count is not None:
                    turn_total_tokens = um.total_token_count
                # Fallback: calculate response tokens if not provided
                if turn_response_tokens == 0 and turn_total_tokens > 0 and turn_prompt_tokens > 0:
                    turn_response_tokens = turn_total_tokens - turn_prompt_tokens

            # Collect the response
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts'):
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            response_text += part.text

        responses.append(response_text)

        # Track cumulative tokens
        total_prompt_tokens += turn_prompt_tokens
        total_response_tokens += turn_response_tokens

        turn_stats = {
            'turn': i,
            'prompt_tokens': turn_prompt_tokens,
            'response_tokens': turn_response_tokens,
            'total_tokens': turn_total_tokens,
            'cumulative_prompt': total_prompt_tokens,
            'cumulative_response': total_response_tokens,
        }
        token_stats.append(turn_stats)

        if verbose:
            print(f"[Turn {i}] Assistant: {response_text[:500]}{'...' if len(response_text) > 500 else ''}")
            if track_tokens and turn_prompt_tokens > 0:
                print(f"[Turn {i}] Tokens: prompt={turn_prompt_tokens}, response={turn_response_tokens}, total={turn_total_tokens}")

    # Print token summary
    if track_tokens and verbose:
        print("\n" + "=" * 60)
        print("TOKEN USAGE SUMMARY")
        print("=" * 60)
        print(f"{'Turn':<6} {'Prompt':<12} {'Response':<12} {'Total':<12} {'Cumulative Prompt':<18}")
        print("-" * 60)
        for stats in token_stats:
            print(f"{stats['turn']:<6} {stats['prompt_tokens']:<12} {stats['response_tokens']:<12} {stats['total_tokens']:<12} {stats['cumulative_prompt']:<18}")
        print("-" * 60)
        print(f"TOTAL: Prompt={total_prompt_tokens}, Response={total_response_tokens}")

    return {
        'responses': responses,
        'token_stats': token_stats,
        'total_prompt_tokens': total_prompt_tokens,
        'total_response_tokens': total_response_tokens,
    }


async def test_basic_memory():
    """Test 1: Basic memory across conversation turns."""
    print("\n" + "=" * 80)
    print("TEST 1: Basic Memory Retention (Context Compaction)")
    print("=" * 80)
    print("Testing whether context compaction preserves important facts...")
    print("(No tools used - testing pure conversation history compaction)")

    messages = [
        "Hi! My name is Alice and I'm a software engineer.",
        "I live in San Francisco and I love hiking on weekends.",
        "My favorite programming language is Python and my favorite color is blue.",
        "I have a cat named Whiskers who is 3 years old.",
        "What do you remember about me? Please list everything you know.",
    ]

    await run_conversation_with_compaction(messages, compaction_interval=3, overlap_size=1)
    print("\n" + "-" * 80)
    print("Test 1 Complete: Check if agent recalled facts from compacted context")


async def test_context_filling():
    """Test 2: Fill context with generated content to trigger compaction."""
    print("\n" + "=" * 80)
    print("TEST 2: Context Filling and Compaction Trigger")
    print("=" * 80)
    print("Testing if important info survives after large content generation...")
    print("(Secret code given early, then lots of filler, then recall)")

    messages = [
        "Important: The secret access code is 'ALPHA-7392'. Please acknowledge.",
        "Tell me a long story about a robot learning to paint.",
        "Now tell me another long story about a space explorer.",
        "Tell me a third story about an underwater civilization.",
        "What was the secret access code I told you at the beginning?",
    ]

    await run_conversation_with_compaction(messages, compaction_interval=2, overlap_size=1)
    print("\n" + "-" * 80)
    print("Test 2 Complete: Check if secret code was preserved through compaction")


async def test_many_facts():
    """Test 3: Extended conversation with multiple facts spread across turns."""
    print("\n" + "=" * 80)
    print("TEST 3: Multiple Facts Across Extended Conversation")
    print("=" * 80)
    print("Testing compaction with facts spread across many turns...")
    print("(Multiple compaction cycles should occur)")

    messages = [
        "Let me tell you about myself. My employee ID is EMP-98765.",
        "I work in the Engineering department on the 5th floor.",
        "My manager's name is Bob Smith and our team has 8 members.",
        "What's 25 times 17? Just curious.",
        "Oh, and my work phone extension is 4321.",
        "Our project codename is 'Phoenix' and deadline is March 15th.",
        "Can you explain what recursion is in programming?",
        "My emergency contact is my sister Jane at 555-1234.",
        "Now please tell me: What is my employee ID, what floor do I work on, and what is my project codename?",
        "Also, what is my manager's name and my phone extension?",
    ]

    await run_conversation_with_compaction(messages, compaction_interval=3, overlap_size=1)
    print("\n" + "-" * 80)
    print("Test 3 Complete: Check how many facts were preserved through multiple compactions")


async def test_compaction_intervals():
    """Test 4: Compare different compaction interval settings."""
    print("\n" + "=" * 80)
    print("TEST 4: Comparing Compaction Intervals")
    print("=" * 80)
    print("Comparing aggressive (interval=2) vs relaxed (interval=5) compaction...")

    test_messages = [
        "Critical info: My password hint is 'blue-ocean-42'. Please confirm.",
        "Tell me about the history of the internet in a few sentences.",
        "What are the main principles of object-oriented programming?",
        "Explain the difference between TCP and UDP briefly.",
        "What was my password hint that I told you earlier?",
    ]

    # Test with aggressive compaction (interval=2)
    print("\n--- Testing with compaction_interval=2 (aggressive) ---")
    print("Compaction triggers after every 2 events - more summarization")
    await run_conversation_with_compaction(test_messages, compaction_interval=2, overlap_size=1)

    # Test with relaxed compaction (interval=5)
    print("\n--- Testing with compaction_interval=5 (relaxed) ---")
    print("Compaction triggers after every 5 events - less summarization")
    await run_conversation_with_compaction(test_messages, compaction_interval=5, overlap_size=1)

    print("\n" + "-" * 80)
    print("Test 4 Complete: Compare if aggressive compaction lost more info than relaxed")


async def test_compaction_chain():
    """Test 5: Verify info survives through multiple compaction cycles via summary chain."""
    print("\n" + "=" * 80)
    print("TEST 5: Compaction Chain Survival Test")
    print("=" * 80)
    print("""
This test verifies that information from Turn 1 survives through
MULTIPLE compaction cycles via the summary chain.

With interval=3, overlap=1:
- Turns 1-3 → Summary₁ (contains Turn 1 info)
- Summary₁ + Turns 4-6 → Summary₂ (should still have Turn 1 info)
- Summary₂ + Turns 7-9 → Summary₃ (should STILL have Turn 1 info)
- Turn 10 asks about Turn 1 → Must recall from Summary₃
""")

    # Detailed prompts with specific facts at key positions
    messages = [
        # === TURN 1: Critical fact that must survive 3 compaction cycles ===
        """I need you to remember this CRITICAL information for our project:
        - Project Code: NEXUS-7749
        - Budget: $2.4 million
        - Lead Architect: Dr. Sarah Chen
        - Deadline: November 30th, 2025
        Please confirm you have noted all these details.""",

        # === TURNS 2-3: Filler before first compaction ===
        "Explain the concept of microservices architecture and its benefits over monolithic systems.",
        "What are the best practices for API versioning in REST services?",
        # → COMPACTION 1 happens here: Turns 1-3 → Summary₁

        # === TURN 4: New fact ===
        """Additional project details:
        - Database: PostgreSQL 15 with TimescaleDB extension
        - Cloud Provider: AWS us-west-2 region
        - CI/CD: GitHub Actions with ArgoCD
        Please acknowledge.""",

        # === TURNS 5-6: Filler before second compaction ===
        "Describe the differences between SQL and NoSQL databases with examples.",
        "What is the CAP theorem and how does it apply to distributed systems?",
        # → COMPACTION 2 happens here: Summary₁ + Turns 4-6 → Summary₂

        # === TURN 7: Another new fact ===
        """Security requirements update:
        - Authentication: OAuth 2.0 with PKCE
        - Encryption: AES-256 at rest, TLS 1.3 in transit
        - Compliance: SOC 2 Type II required
        Got it?""",

        # === TURNS 8-9: Filler before third compaction ===
        "Explain containerization with Docker and when to use Kubernetes.",
        "What are the principles of twelve-factor app methodology?",
        # → COMPACTION 3 happens here: Summary₂ + Turns 7-9 → Summary₃

        # === TURN 10: THE CRITICAL TEST ===
        # Turn 1's info has gone through 3 compaction cycles!
        # It should only exist in the summary chain now.
        """IMPORTANT: I need you to recall the ORIGINAL project details from the
        very beginning of our conversation:
        1. What was the Project Code?
        2. What was the Budget?
        3. Who was the Lead Architect?
        4. What was the Deadline?

        These were the FIRST things I told you. Please list them all.""",
    ]

    print("Running 10-turn conversation with 3 compaction cycles...")
    print("Turn 1 info must survive: NEXUS-7749, $2.4M, Dr. Sarah Chen, Nov 30 2025")
    print("-" * 80)

    await run_conversation_with_compaction(messages, compaction_interval=3, overlap_size=1)

    print("\n" + "-" * 80)
    print("Test 5 Complete!")
    print("SUCCESS if agent recalled: NEXUS-7749, $2.4 million, Dr. Sarah Chen, November 30th 2025")
    print("FAILURE if agent couldn't recall Turn 1 details (compaction lost the info)")


async def test_with_vs_without_compaction():
    """Test 6: Compare the same conversation WITH and WITHOUT compaction."""
    print("\n" + "=" * 80)
    print("TEST 6: WITH vs WITHOUT Context Compaction")
    print("=" * 80)
    print("""
This test runs the SAME 10-turn conversation twice:
1. WITHOUT compaction (interval=100, so it never triggers)
2. WITH compaction (interval=3, triggers 3 times)

Both should remember Turn 1 info for this short conversation.
The real difference appears in LONG conversations (50+ turns).
""")

    # Same detailed messages as Test 5
    messages = [
        """CRITICAL project information to remember:
        - Project Code: NEXUS-7749
        - Budget: $2.4 million
        - Lead Architect: Dr. Sarah Chen
        - Deadline: November 30th, 2025
        Please confirm.""",

        "Explain microservices architecture briefly.",
        "What are REST API versioning best practices?",

        """More details:
        - Database: PostgreSQL 15
        - Cloud: AWS us-west-2
        - CI/CD: GitHub Actions
        Noted?""",

        "Explain SQL vs NoSQL differences.",
        "What is the CAP theorem?",

        """Security requirements:
        - Auth: OAuth 2.0 with PKCE
        - Encryption: AES-256
        - Compliance: SOC 2 Type II
        Got it?""",

        "Explain Docker containerization.",
        "What is twelve-factor app methodology?",

        """RECALL TEST: What were the ORIGINAL project details from Turn 1?
        - Project Code?
        - Budget?
        - Lead Architect?
        - Deadline?""",
    ]

    # ========== RUN WITHOUT COMPACTION ==========
    print("\n" + "=" * 60)
    print("PART A: WITHOUT Compaction (interval=100, never triggers)")
    print("=" * 60)
    print("Agent has full conversation history - no summarization")
    print("-" * 60)

    await run_conversation_with_compaction(
        messages,
        compaction_interval=100,  # Never triggers in 10 turns
        overlap_size=1
    )

    # ========== RUN WITH COMPACTION ==========
    print("\n" + "=" * 60)
    print("PART B: WITH Compaction (interval=3, triggers 3 times)")
    print("=" * 60)
    print("Agent has summarized history - Turn 1 went through 3 compaction cycles")
    print("-" * 60)

    await run_conversation_with_compaction(
        messages,
        compaction_interval=3,  # Triggers at turns 3, 6, 9
        overlap_size=1
    )

    print("\n" + "=" * 80)
    print("Test 6 Complete!")
    print("=" * 80)
    print("""
COMPARISON:
- Part A (no compaction): Agent had full history → Should recall everything
- Part B (with compaction): Agent had summarized history → Should ALSO recall everything

For this SHORT conversation, both should work.

THE REAL TEST for compaction value:
- Run 50-100+ turns where context WITHOUT compaction would be huge/expensive
- Compaction keeps context small while preserving key info
- Benefits: Lower cost, faster responses, no token limit errors
""")


async def test_long_conversation_with_tokens():
    """Test 7: Conversation with token tracking to prove compaction saves tokens."""
    print("\n" + "=" * 80)
    print("TEST 7: Token Tracking - WITH vs WITHOUT Compaction")
    print("=" * 80)
    print("""
This test runs a 10-TURN conversation TWICE and tracks ACTUAL token usage.

PART A: interval=8 (no compaction in 10 turns) - Prompt tokens GROW
PART B: interval=3 (compaction at turns 3,6,9) - Prompt tokens STABILIZE

Key metric: PROMPT TOKENS = context size sent to model
""")

    messages = [
        # Turn 1: Critical info
        """REMEMBER THIS - Project Alpha Details:
        - Code: ZETA-9988
        - Budget: $5.7 million
        - Director: Dr. James Wilson
        - Launch Date: September 15th, 2026
        - Location: Building 7, Floor 12
        Please confirm all details.""",

        # Turns 2-9: Technical questions
        "Explain the principles of machine learning in detail.",
        "What is the difference between supervised and unsupervised learning?",
        "Describe how neural networks work with examples.",
        "Explain microservices architecture and its benefits.",
        "What is containerization and how does Docker work?",
        "Describe the CI/CD pipeline and its importance.",
        "What are design patterns in software engineering?",
        "Explain RESTful API design principles.",

        # Turn 10: Recall test
        """CRITICAL RECALL TEST:
        What were the Project Alpha details I told you at the VERY BEGINNING?
        - What was the Code?
        - What was the Budget?
        - Who was the Director?
        - What was the Launch Date?
        - What was the Location?
        List ALL five details.""",
    ]

    print(f"Total turns: {len(messages)}")
    print("Turn 1: Critical project info (ZETA-9988, $5.7M, Dr. James Wilson, etc.)")
    print("Turns 2-9: Technical questions generating substantial responses")
    print("Turn 10: Recall test for Turn 1 info")

    # ========== RUN WITHOUT COMPACTION ==========
    print("\n" + "=" * 70)
    print("PART A: interval=8 (NO compaction in 10 turns)")
    print("=" * 70)
    print("Watch the 'Prompt' tokens GROW with each turn (full history)")
    print("-" * 70)

    result_no_compact = await run_conversation_with_compaction(
        messages,
        compaction_interval=8,  # Won't trigger in 10 turns
        overlap_size=1,
        verbose=True,
        track_tokens=True
    )

    # ========== RUN WITH COMPACTION ==========
    print("\n" + "=" * 70)
    print("PART B: interval=3 (compaction at turns 3, 6, 9)")
    print("=" * 70)
    print("Watch the 'Prompt' tokens STABILIZE after compaction")
    print("-" * 70)

    result_with_compact = await run_conversation_with_compaction(
        messages,
        compaction_interval=3,  # Triggers at turns 3, 6, 9
        overlap_size=1,
        verbose=True,
        track_tokens=True
    )

    # ========== COMPARISON ==========
    print("\n" + "=" * 80)
    print("FINAL COMPARISON")
    print("=" * 80)

    no_compact_total = result_no_compact['total_prompt_tokens']
    with_compact_total = result_with_compact['total_prompt_tokens']

    print(f"\nWITHOUT Compaction:")
    print(f"  - Total prompt tokens used: {no_compact_total:,}")
    if result_no_compact['token_stats']:
        last_turn = result_no_compact['token_stats'][-1]
        print(f"  - Final turn prompt tokens: {last_turn['prompt_tokens']:,}")

    print(f"\nWITH Compaction (interval=5):")
    print(f"  - Total prompt tokens used: {with_compact_total:,}")
    if result_with_compact['token_stats']:
        last_turn = result_with_compact['token_stats'][-1]
        print(f"  - Final turn prompt tokens: {last_turn['prompt_tokens']:,}")

    if no_compact_total > 0 and with_compact_total > 0:
        savings = no_compact_total - with_compact_total
        savings_pct = (savings / no_compact_total) * 100
        print(f"\nTOKEN SAVINGS:")
        print(f"  - Saved: {savings:,} prompt tokens ({savings_pct:.1f}%)")

    print("\nRECALL TEST RESULTS:")
    print(f"  - Without compaction recalled Turn 1: {'ZETA-9988' in result_no_compact['responses'][-1]}")
    print(f"  - With compaction recalled Turn 1: {'ZETA-9988' in result_with_compact['responses'][-1]}")

    print("\n" + "-" * 80)
    print("Test 7 Complete!")


async def interactive_mode():
    """Run an interactive session with the agent."""
    print("\n" + "=" * 80)
    print("INTERACTIVE MODE")
    print("=" * 80)
    print("Chat with the agent to test context compaction manually.")
    print("Share facts, have conversation, then ask what it remembers.")
    print("Type 'quit' or 'exit' to end the session.")
    print("-" * 80)

    # Default compaction settings for interactive mode
    compaction_interval = 3
    overlap_size = 1

    session_service = InMemorySessionService()

    # Create App with context compaction configuration
    app = App(
        name="context_compaction_poc",
        root_agent=root_agent,
        events_compaction_config=EventsCompactionConfig(
            compaction_interval=compaction_interval,
            overlap_size=overlap_size,
        ),
    )

    # Create Runner with the App and session service
    runner = Runner(
        app=app,
        session_service=session_service,
    )

    session = await session_service.create_session(
        app_name="context_compaction_poc",
        user_id="interactive_user",
    )

    print(f"\nCompaction settings: interval={compaction_interval}, overlap={overlap_size}")

    turn = 0
    while True:
        try:
            user_input = input(f"\n[Turn {turn + 1}] You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nExiting interactive mode.")
            break

        if not user_input:
            continue

        if user_input.lower() in ['quit', 'exit']:
            print("Exiting interactive mode.")
            break

        turn += 1
        response_text = ""
        async for event in runner.run_async(
            user_id="interactive_user",
            session_id=session.id,
            new_message=types.Content(
                role="user",
                parts=[types.Part(text=user_input)]
            ),
        ):
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts'):
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            response_text += part.text

        print(f"\n[Turn {turn}] Assistant: {response_text}")


async def main():
    """Main entry point for the POC."""
    print("=" * 80)
    print("Google ADK Context Compaction - Proof of Concept")
    print("=" * 80)
    print("""
This POC demonstrates Google ADK's context compaction feature.

Context compaction works by:
1. Monitoring the number of events (turns) in a conversation
2. When the compaction_interval is reached, older events are summarized
3. The overlap_size determines how many events bridge compaction windows
4. This keeps the context window manageable for long conversations

Available tests:
1. Basic Memory Retention - Tests fact storage and recall
2. Context Filling - Generates large content to trigger compaction
3. Multiple Facts - Stores many facts across extended conversation
4. Compaction Intervals - Compares different interval settings
5. Compaction Chain Survival - Tests if Turn 1 info survives 3 compaction cycles
6. WITH vs WITHOUT Compaction - Same conversation, compare results
7. Long Conversation + Token Tracking (30 turns) - PROVES token savings
8. Interactive Mode - Manual testing

""")

    check_api_key()

    while True:
        print("\nSelect a test to run:")
        print("  1. Basic Memory Retention")
        print("  2. Context Filling and Compaction")
        print("  3. Multiple Facts Extended Test")
        print("  4. Compare Compaction Intervals")
        print("  5. Compaction Chain Survival")
        print("  6. WITH vs WITHOUT Compaction")
        print("  7. Long Conversation + Token Tracking (RECOMMENDED)")
        print("  8. Interactive Mode")
        print("  9. Run All Tests")
        print("  0. Exit")

        try:
            choice = input("\nEnter your choice (0-9): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nExiting.")
            break

        if choice == '0':
            print("Goodbye!")
            break
        elif choice == '1':
            await test_basic_memory()
        elif choice == '2':
            await test_context_filling()
        elif choice == '3':
            await test_many_facts()
        elif choice == '4':
            await test_compaction_intervals()
        elif choice == '5':
            await test_compaction_chain()
        elif choice == '6':
            await test_with_vs_without_compaction()
        elif choice == '7':
            await test_long_conversation_with_tokens()
        elif choice == '8':
            await interactive_mode()
        elif choice == '9':
            print("\nRunning all tests...")
            await test_basic_memory()
            await test_context_filling()
            await test_many_facts()
            await test_compaction_intervals()
            await test_compaction_chain()
            await test_with_vs_without_compaction()
            await test_long_conversation_with_tokens()
            print("\n" + "=" * 80)
            print("ALL TESTS COMPLETED")
            print("=" * 80)
        else:
            print("Invalid choice. Please enter 0-9.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
