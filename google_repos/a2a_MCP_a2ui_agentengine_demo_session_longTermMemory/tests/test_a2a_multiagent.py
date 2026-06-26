import json
import httpx
import time

SUPERVISOR_URL = "http://localhost:10101/v1/message:stream"

def parse_sse_event_string(event_str, a2ui_list):
    """Parses a complete concatenated SSE JSON event payload."""
    last_text = ""
    try:
        data_json = json.loads(event_str)
        message = {}
        if "result" in data_json:
            message = data_json["result"].get("message", {})
        elif "statusUpdate" in data_json:
            status_update = data_json["statusUpdate"]
            status_val = status_update.get("status", {})
            message = status_val.get("message", {})
            
        content_list = message.get("content", [])
        
        for part in content_list:
            if "text" in part:
                last_text = part["text"]
                # Extract embedded <a2ui-json> blocks from the text
                if "<a2ui-json>" in last_text:
                    try:
                        start_tag = "<a2ui-json>"
                        end_tag = "</a2ui-json>"
                        start_idx = last_text.find(start_tag) + len(start_tag)
                        end_idx = last_text.find(end_tag)
                        if end_idx > start_idx:
                            a2ui_json_str = last_text[start_idx:end_idx].strip()
                            a2ui_data = json.loads(a2ui_json_str)
                            if isinstance(a2ui_data, list):
                                a2ui_list.extend(a2ui_data)
                            else:
                                a2ui_list.append(a2ui_data)
                    except Exception as ex:
                        print(f"Error extracting XML a2ui-json: {ex}")
            elif "data" in part:
                a2ui_list.append(part["data"])
    except Exception as e:
        print(f"Error parsing event JSON: {e}")
    return last_text

def run_test():
    # --- PHASE 1: Attrition Query ---
    print("\n==================================================")
    print("PHASE A: Sending Attrition Query to Supervisor (Port 10101)")
    print("==================================================")
    
    payload = {
        "message": {
            "role": "ROLE_USER",
            "message_id": "session-msg-1",
            "context_id": "integration-test-session",
            "content": [
                {
                    "text": "Across my portfolio, identify products where price increases over the past 52 weeks drove buyer attrition."
                }
            ]
        }
    }

    last_text = ""
    a2ui_parts = []
    current_event_lines = []

    with httpx.stream("POST", SUPERVISOR_URL, json=payload, timeout=60.0) as r:
        print(f"Supervisor Stream Status: {r.status_code}")
        for line in r.iter_lines():
            if not line.strip():
                if current_event_lines:
                    full_event_str = "".join(current_event_lines)
                    print(f"[Phase A] Parsing accumulated event (len={len(full_event_str)})")
                    txt = parse_sse_event_string(full_event_str, a2ui_parts)
                    if txt:
                        last_text = txt
                    current_event_lines = []
            else:
                if line.startswith("data:"):
                    current_event_lines.append(line[5:])
                    
        # Flush the last event if any
        if current_event_lines:
            full_event_str = "".join(current_event_lines)
            print(f"[Phase A] Flushed final event (len={len(full_event_str)})")
            txt = parse_sse_event_string(full_event_str, a2ui_parts)
            if txt:
                last_text = txt

    print("\n--- Final Text Response ---")
    print(last_text)
    
    print("\n--- Extracted A2UI Payloads ---")
    print(json.dumps(a2ui_parts, indent=2))
    
    assert len(a2ui_parts) > 0, "Error: No A2UI parts returned by Supervisor!"
    assert "circana-pricing-table" in str(a2ui_parts), "Error: circana-pricing-table was not in the A2UI payloads!"
    print("\n✓ Phase A Successful! Table rendered correctly.")

    # --- PHASE 2: Select Cohort (Callback action) ---
    print("\n==================================================")
    print("PHASE B: Sending Selection Action callback to Supervisor")
    print("==================================================")
    
    action_payload = {
        "actionId": "product_selected",
        "payload": {
            "product": "Diet Pepsi 12pk"
        }
    }
    
    payload_action = {
        "message": {
            "role": "ROLE_USER",
            "message_id": "session-msg-2",
            "context_id": "integration-test-session",
            "content": [
                {
                    "data": {
                        "data": action_payload
                    }
                }
            ]
        }
    }

    last_text_b = ""
    a2ui_parts_b = []
    current_event_lines_b = []

    with httpx.stream("POST", SUPERVISOR_URL, json=payload_action, timeout=60.0) as r:
        print(f"Supervisor Stream Status: {r.status_code}")
        for line in r.iter_lines():
            if not line.strip():
                if current_event_lines_b:
                    full_event_str = "".join(current_event_lines_b)
                    print(f"[Phase B] Parsing accumulated event (len={len(full_event_str)})")
                    txt = parse_sse_event_string(full_event_str, a2ui_parts_b)
                    if txt:
                        last_text_b = txt
                    current_event_lines_b = []
            else:
                if line.startswith("data:"):
                    current_event_lines_b.append(line[5:])
                    
        # Flush the last event if any
        if current_event_lines_b:
            full_event_str = "".join(current_event_lines_b)
            print(f"[Phase B] Flushed final event (len={len(full_event_str)})")
            txt = parse_sse_event_string(full_event_str, a2ui_parts_b)
            if txt:
                last_text_b = txt

    print("\n--- Final Sizing Text Response ---")
    print(last_text_b)
    
    print("\n--- Extracted Sizing A2UI Payloads ---")
    print(json.dumps(a2ui_parts_b, indent=2))
    
    assert len(a2ui_parts_b) > 0, "Error: No A2UI parts returned by Supervisor for Sizing!"
    assert "circana-sizing-dashboard" in str(a2ui_parts_b), "Error: Sizing dashboard was not in the A2UI payloads!"
    print("\n✓ Phase B Successful! Sizing dashboard rendered correctly.")
    print("\n==================================================")
    print("ALL A2A LOCAL TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    run_test()
