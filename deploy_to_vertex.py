#!/usr/bin/env python3
"""
Deploy Context Compaction Agent to Vertex AI Agent Engine

This script deploys the App object (not just the agent) to ensure
EventsCompactionConfig is properly passed to the Agent Engine.

Usage:
    # Set your GCP project and location
    export GCP_PROJECT_ID='your-project-id'
    export GCP_LOCATION='us-central1'
    export GCP_STAGING_BUCKET='gs://your-bucket-name'

    # Run deployment
    python deploy_to_vertex.py
"""

import os
import sys

# Verify environment variables before importing heavy dependencies
def check_env_vars():
    """Check required environment variables."""
    required_vars = {
        'GCP_PROJECT_ID': 'Your Google Cloud project ID',
        'GCP_LOCATION': 'Vertex AI location (e.g., us-central1)',
        'GCP_STAGING_BUCKET': 'GCS bucket for staging (e.g., gs://my-bucket)',
    }

    missing = []
    for var, description in required_vars.items():
        if not os.environ.get(var):
            missing.append(f"  {var}: {description}")

    if missing:
        print("=" * 70)
        print("ERROR: Missing required environment variables")
        print("=" * 70)
        print("\nPlease set the following environment variables:\n")
        print("\n".join(missing))
        print("\nExample:")
        print("  export GCP_PROJECT_ID='my-project-123'")
        print("  export GCP_LOCATION='us-central1'")
        print("  export GCP_STAGING_BUCKET='gs://my-staging-bucket'")
        print("\nThen run this script again.")
        sys.exit(1)

    return {
        'project_id': os.environ['GCP_PROJECT_ID'],
        'location': os.environ['GCP_LOCATION'],
        'staging_bucket': os.environ['GCP_STAGING_BUCKET'],
    }


def main():
    """Deploy the App with EventsCompactionConfig to Vertex AI Agent Engine."""

    # Check environment variables first
    config = check_env_vars()

    print("=" * 70)
    print("Deploying Context Compaction Agent to Vertex AI Agent Engine")
    print("=" * 70)
    print(f"\nProject ID: {config['project_id']}")
    print(f"Location: {config['location']}")
    print(f"Staging Bucket: {config['staging_bucket']}")
    print()

    # Now import the heavy dependencies
    print("Initializing Vertex AI SDK...")
    import vertexai
    from vertexai import agent_engines

    from google.adk.apps.app import App, EventsCompactionConfig
    from google.adk.apps.llm_event_summarizer import LlmEventSummarizer
    from google.adk.models import Gemini

    # Import the agent
    from context_compaction_agent.agent import root_agent

    # Initialize Vertex AI
    print(f"Connecting to Vertex AI in {config['location']}...")
    vertexai.init(
        project=config['project_id'],
        location=config['location']
    )

    # Create explicit summarizer for context compaction
    print("Creating LlmEventSummarizer...")
    compaction_summarizer = LlmEventSummarizer(
        llm=Gemini(model="gemini-2.5-flash")
    )

    # Create App with EventsCompactionConfig
    # This is the KEY - we pass the App object, not just the agent
    print("Creating App with EventsCompactionConfig...")
    app = App(
        name="context_compaction_agent",
        root_agent=root_agent,
        events_compaction_config=EventsCompactionConfig(
            compaction_interval=3,  # Compact every 3 turns
            overlap_size=1,         # Keep 1 turn overlap for continuity
            summarizer=compaction_summarizer,  # Explicit summarizer
        ),
    )

    print("\nApp Configuration:")
    print(f"  - Name: {app.name}")
    print(f"  - Compaction Interval: 3")
    print(f"  - Overlap Size: 1")
    print(f"  - Summarizer: LlmEventSummarizer (gemini-2.5-flash)")

    # Deploy to Agent Engine
    print("\n" + "-" * 70)
    print("Deploying to Vertex AI Agent Engine...")
    print("This may take a few minutes...")
    print("-" * 70 + "\n")

    try:
        remote_agent = agent_engines.create(
            agent=app,  # Pass the App object with compaction config
            config={
                "requirements": [
                    "google-cloud-aiplatform[agent_engines,adk]",
                    "google-adk>=1.17.0",
                ],
                "staging_bucket": config['staging_bucket'],
            },
            display_name="Context Compaction Agent",
        )

        print("\n" + "=" * 70)
        print("DEPLOYMENT SUCCESSFUL!")
        print("=" * 70)
        print(f"\nResource Name: {remote_agent.resource_name}")
        print(f"\nYou can now test the agent in the Google Cloud Console:")
        print(f"  https://console.cloud.google.com/vertex-ai/agents")
        print("\nOr query it programmatically:")
        print(f"""
    from vertexai import agent_engines

    agent = agent_engines.get("{remote_agent.resource_name}")

    # Create a session
    session = agent.create_session(user_id="test-user")

    # Send messages
    response = agent.query(
        session_id=session.id,
        message="Hello! My name is Alice.",
    )
    print(response)
""")

        # Save deployment info
        deployment_info_file = "deployment_info.txt"
        with open(deployment_info_file, "w") as f:
            f.write(f"Resource Name: {remote_agent.resource_name}\n")
            f.write(f"Project: {config['project_id']}\n")
            f.write(f"Location: {config['location']}\n")
            f.write(f"Display Name: Context Compaction Agent\n")
        print(f"\nDeployment info saved to: {deployment_info_file}")

        return remote_agent

    except Exception as e:
        print("\n" + "=" * 70)
        print("DEPLOYMENT FAILED")
        print("=" * 70)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
