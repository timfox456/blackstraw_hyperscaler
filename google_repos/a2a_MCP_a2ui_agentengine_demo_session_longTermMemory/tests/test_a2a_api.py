import json
import httpx

def test_a2a():
    # 1. Fetch the Agent Card
    print("--- 1. Fetching Agent Card ---")
    resp = httpx.get("http://localhost:10101/.well-known/agent-card.json")
    print(f"Status: {resp.status_code}")
    print(json.dumps(resp.json(), indent=2))

    # 2. Send message streaming
    print("\n--- 2. Sending Message Stream ---")
    payload = {
        "message": {
            "role": "ROLE_USER",
            "message_id": "test-msg-id-123",
            "context_id": "test-session-circana",
            "content": [
                {
                    "text": "Across my portfolio, identify products where price increases over the past 52 weeks drove buyer attrition."
                }
            ]
        }
    }
    
    with httpx.stream("POST", "http://localhost:10101/v1/message:stream", json=payload, timeout=60.0) as r:
        print(f"Stream Status: {r.status_code}")
        for line in r.iter_lines():
            if line.strip():
                print(line)

if __name__ == "__main__":
    test_a2a()
