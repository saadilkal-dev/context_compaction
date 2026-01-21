#!/usr/bin/env python3
"""
Simple example of calling Gemini API using Google genai SDK
"""

from google import genai
import os
import sys

def main():
    # Get API key
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        print("Get your key from: https://aistudio.google.com/apikey")
        print("Then run: export GEMINI_API_KEY='your-api-key'")
        sys.exit(1)

    # Initialize client
    client = genai.Client(api_key=api_key)

    print("=" * 80)
    print("Testing Gemini API Call")
    print("=" * 80)

    # Simple single request
    print("\n[Example 1] Single generate_content call:")
    print("-" * 80)

    response = client.models.generate_content(
        model='gemini-2.0-flash-exp',
        contents='Write a haiku about programming in Python.'
    )

    print(f"Response:\n{response.text}\n")

    # Show usage metadata if available
    if hasattr(response, 'usage_metadata') and response.usage_metadata:
        print(f"Token usage:")
        print(f"  Input tokens: {response.usage_metadata.prompt_token_count}")
        print(f"  Output tokens: {response.usage_metadata.candidates_token_count}")
        print(f"  Total tokens: {response.usage_metadata.total_token_count}")

    # Chat conversation
    print("\n[Example 2] Multi-turn chat conversation:")
    print("-" * 80)

    chat = client.chats.create(model='gemini-2.0-flash-exp')

    # Turn 1
    msg1 = "Hi! My favorite color is blue."
    print(f"User: {msg1}")
    resp1 = chat.send_message(msg1)
    print(f"Assistant: {resp1.text}\n")

    # Turn 2 - testing context retention
    msg2 = "What color did I just mention?"
    print(f"User: {msg2}")
    resp2 = chat.send_message(msg2)
    print(f"Assistant: {resp2.text}\n")

    # Turn 3
    msg3 = "Now tell me a fact about that color in nature."
    print(f"User: {msg3}")
    resp3 = chat.send_message(msg3)
    print(f"Assistant: {resp3.text}\n")

    print("=" * 80)
    print("API calls completed successfully!")
    print("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
