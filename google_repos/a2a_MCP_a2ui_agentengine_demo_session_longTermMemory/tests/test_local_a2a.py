import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

# Set up paths to locate our package (parent directory)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from a2a.server.agent_execution import RequestContext
from a2a.server.events import EventQueue
from agents.circana_pilot_agent.executor import CircanaPilotExecutor
from a2a.types import Message, Role, Part, TextPart, MessageSendParams

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

async def main():
    load_dotenv()
    
    print("Initializing CircanaPilotExecutor (A2A)...")
    executor = CircanaPilotExecutor()

    # Mock the user request
    user_message = Message(
        message_id="test-msg-1",
        role=Role.user,
        parts=[Part(root=TextPart(text="Across my portfolio, identify products where price increases over the past 52 weeks drove buyer attrition."))]
    )

    request_params = MessageSendParams(message=user_message)
    context = RequestContext(
        context_id="test-session-circana",
        task_id="test-task-circana",
        request=request_params
    )
    
    event_queue = EventQueue()

    print("\n--- STARTING LOCAL A2A AGENT EXECUTION ---")
    try:
        await executor.execute(context, event_queue)
        print("--- A2A AGENT EXECUTION COMPLETED ---")
    except Exception as e:
        print(f"\nExecution failed: {e}")
        return

    # Print out parts emitted by the A2A executor
    print("\n--- PARSING EMITTED A2A PROTOCOL PARTS ---")
    try:
        while True:
            event = event_queue.queue.get_nowait()
            if hasattr(event, "task_status") and event.task_status.message:
                parts = event.task_status.message.parts
                for idx, part in enumerate(parts):
                    if hasattr(part.root, "text"):
                        print(f"\n[Part {idx} (Standard A2A TextPart)]:\n{part.root.text}")
                    elif hasattr(part.root, "data"):
                        import pprint
                        print(f"\n[Part {idx} (Standard A2A DataPart / A2UI JSON)]:")
                        pprint.pprint(part.root.data)
            else:
                print(f"Event received: {event}")
    except asyncio.QueueEmpty:
        pass

if __name__ == "__main__":
    asyncio.run(main())
