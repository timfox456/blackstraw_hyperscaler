import asyncio
import httpx
import uuid
from a2a.client import ClientFactory, ClientConfig
from a2a.types import Message, Part, TextPart, Role, TransportProtocol, Task

async def main():
    url = "http://localhost:10102/"
    httpx_client = httpx.AsyncClient(timeout=30)
    
    config = ClientConfig(
        supported_transports=[TransportProtocol.http_json],
        httpx_client=httpx_client
    )
    
    print("Connecting to Pricing agent via ClientFactory...")
    client = await ClientFactory.connect(url, client_config=config)
    print(f"Connected! Selected transport: {type(client._transport)}")
    
    message = Message(
        role=Role.user,
        message_id=str(uuid.uuid4()),
        context_id="factory-test-session",
        parts=[Part(root=TextPart(text="Identify products with buyer attrition."))]
    )
    
    print("Sending message...")
    async for event in client.send_message(message):
        print("Received Event:", type(event))
        if isinstance(event, tuple):
            task, update = event
            print(f"  Task Status: {task.status.state}")
            # print last history message
            if task.history:
                last_msg = task.history[-1]
                print(f"  Last Msg Role: {last_msg.role}")
                for part in last_msg.parts:
                    if hasattr(part.root, 'text'):
                        print(f"  Part Text: {part.root.text}")
        elif isinstance(event, Message):
            print("  Received Message directly:", event)
            
    await httpx_client.aclose()

if __name__ == "__main__":
    asyncio.run(main())
