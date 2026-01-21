#!/usr/bin/env python3
"""
Proof of Concept: Testing Context Compaction with Google Gemini API
This script tests how Gemini handles context window management and compaction.
"""

from google import genai
from google.genai import types
import os
import sys

def test_context_compaction():
    """Test context compaction with progressively larger conversations."""

    # Get API key from environment variable
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        print("Usage: export GEMINI_API_KEY='your-api-key-here'")
        sys.exit(1)

    # Initialize the client
    client = genai.Client(api_key=api_key)

    print("=" * 80)
    print("Testing Gemini Context Compaction")
    print("=" * 80)

    # Test 1: Simple conversation
    print("\n[Test 1] Simple conversation:")
    print("-" * 80)

    chat = client.chats.create(model='gemini-2.0-flash-exp')

    response1 = chat.send_message("Hello! Please remember this number: 42")
    print(f"User: Hello! Please remember this number: 42")
    print(f"Assistant: {response1.text}\n")

    response2 = chat.send_message("What number did I ask you to remember?")
    print(f"User: What number did I ask you to remember?")
    print(f"Assistant: {response2.text}\n")

    # Test 2: Large context test
    print("\n[Test 2] Building large context with multiple facts:")
    print("-" * 80)

    # Create a new chat with lots of information
    chat2 = client.chats.create(model='gemini-2.0-flash-exp')

    # Send multiple messages with facts to build context
    facts = [
        "The capital of France is Paris",
        "Python was created by Guido van Rossum",
        "The speed of light is 299,792,458 meters per second",
        "Shakespeare wrote Hamlet in approximately 1600",
        "Mount Everest is 8,849 meters tall",
    ]

    for i, fact in enumerate(facts, 1):
        response = chat2.send_message(f"Remember fact #{i}: {fact}")
        print(f"Sent fact #{i}: {fact}")

    print("\n" + "-" * 80)
    print("Now testing recall of early facts:")

    recall_response = chat2.send_message(
        "Can you recall all the facts I told you, especially fact #1 and #2?"
    )
    print(f"\nAssistant's recall: {recall_response.text}\n")

    # Test 3: Token usage information
    print("\n[Test 3] Checking token usage:")
    print("-" * 80)

    # Create a longer message to see token counts
    long_message = "Analyze this: " + " ".join([f"Word{i}" for i in range(100)])
    response3 = client.models.generate_content(
        model='gemini-2.0-flash-exp',
        contents=long_message
    )

    print(f"Long message sent (100+ words)")
    print(f"Response: {response3.text[:200]}...")

    # Try to get token count if available
    try:
        if hasattr(response3, 'usage_metadata'):
            print(f"\nToken usage metadata:")
            print(f"  Prompt tokens: {response3.usage_metadata.prompt_token_count}")
            print(f"  Candidate tokens: {response3.usage_metadata.candidates_token_count}")
            print(f"  Total tokens: {response3.usage_metadata.total_token_count}")
    except Exception as e:
        print(f"Token count not available: {e}")

    # Test 4: Context window limits
    print("\n[Test 4] Testing context window with very long input:")
    print("-" * 80)

    # Generate a very long prompt
    very_long_text = "Here is a long document. " * 1000  # ~5000 words
    try:
        response4 = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=f"{very_long_text}\n\nQuestion: What is the approximate length of the document above?"
        )
        print(f"Successfully processed long context")
        print(f"Response: {response4.text}\n")
    except Exception as e:
        print(f"Error with long context: {e}\n")

    print("=" * 80)
    print("Context compaction testing complete!")
    print("=" * 80)

if __name__ == "__main__":
    try:
        test_context_compaction()
    except Exception as e:
        print(f"\nError during execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
