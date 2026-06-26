import json
import httpx

SUPERVISOR_URL = "http://localhost:10101/v1/message:stream"

def parse_sse_event_string(event_str, a2ui_list):
    last_text = ""
    try:
        data_json = json.loads(event_str)
        message = {}
        if "result" in data_json:
            message = data_json["result"].get("message", {})
        elif "statusUpdate" in data_json:
            status_val = data_json["statusUpdate"].get("status", {})
            message = status_val.get("message", {})
            
        content_list = message.get("content", [])
        for part in content_list:
            if "text" in part:
                last_text = part["text"]
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
        pass
    return last_text

def run_e2e_test():
    context_id = "full-e2e-session-999"
    
    # --------------------------------------------------
    # PHASE 1: Pricing Audit Request
    # --------------------------------------------------
    print("\n=== PHASE A: Pricing opportunities audit query ===")
    payload_1 = {
        "message": {
            "role": "ROLE_USER",
            "message_id": "msg-1",
            "context_id": context_id,
            "content": [{"text": "Identify portfolio products with buyer attrition due to price increases."}]
        }
    }
    
    a2ui_parts = []
    current_event_lines = []
    with httpx.stream("POST", SUPERVISOR_URL, json=payload_1, timeout=60.0) as r:
        for line in r.iter_lines():
            if not line.strip():
                if current_event_lines:
                    parse_sse_event_string("".join(current_event_lines), a2ui_parts)
                    current_event_lines = []
            else:
                if line.startswith("data:"):
                    current_event_lines.append(line[5:])
        if current_event_lines:
            parse_sse_event_string("".join(current_event_lines), a2ui_parts)
            
    print(f"✓ Phase A Completed. Extracted A2UI count: {len(a2ui_parts)}")
    assert len(a2ui_parts) > 0, "Failed Phase A"

    # --------------------------------------------------
    # PHASE 2: Select Diet Pepsi
    # --------------------------------------------------
    print("\n=== PHASE B: Selecting Cohort callback action ===")
    action_1 = {
        "actionId": "product_selected",
        "payload": {"product": "Diet Pepsi 12pk"}
    }
    payload_2 = {
        "message": {
            "role": "ROLE_USER",
            "message_id": "msg-2",
            "context_id": context_id,
            "content": [{"data": {"data": action_1}}]
        }
    }
    
    a2ui_parts = []
    current_event_lines = []
    with httpx.stream("POST", SUPERVISOR_URL, json=payload_2, timeout=60.0) as r:
        for line in r.iter_lines():
            if not line.strip():
                if current_event_lines:
                    parse_sse_event_string("".join(current_event_lines), a2ui_parts)
                    current_event_lines = []
            else:
                if line.startswith("data:"):
                    current_event_lines.append(line[5:])
        if current_event_lines:
            parse_sse_event_string("".join(current_event_lines), a2ui_parts)
            
    print(f"✓ Phase B Completed. Extracted A2UI count: {len(a2ui_parts)}")
    assert len(a2ui_parts) > 0, "Failed Phase B"

    # --------------------------------------------------
    # PHASE 3: Activate Channel
    # --------------------------------------------------
    print("\n=== PHASE C: Channel Activation callback action ===")
    action_2 = {
        "actionId": "btn_activate",
        "payload": {"partners": ["LiveRamp", "Google"]}
    }
    payload_3 = {
        "message": {
            "role": "ROLE_USER",
            "message_id": "msg-3",
            "context_id": context_id,
            "content": [{"data": {"data": action_2}}]
        }
    }
    
    last_text = ""
    current_event_lines = []
    with httpx.stream("POST", SUPERVISOR_URL, json=payload_3, timeout=60.0) as r:
        for line in r.iter_lines():
            if not line.strip():
                if current_event_lines:
                    last_text = parse_sse_event_string("".join(current_event_lines), [])
                    current_event_lines = []
            else:
                if line.startswith("data:"):
                    current_event_lines.append(line[5:])
        if current_event_lines:
            last_text = parse_sse_event_string("".join(current_event_lines), [])
            
    print(f"✓ Phase C Completed. Response: {last_text[:120]}...")

    # --------------------------------------------------
    # PHASE 4: Initiate Loyalty campaign personalization
    # --------------------------------------------------
    print("\n=== PHASE D.1: Initiate loyalty rewards customization ===")
    payload_4 = {
        "message": {
            "role": "ROLE_USER",
            "message_id": "msg-4",
            "context_id": context_id,
            "content": [{"text": "Initiate the personalized loyalty campaign personalization options for this Diet Pepsi cohort."}]
        }
    }
    
    a2ui_parts = []
    current_event_lines = []
    with httpx.stream("POST", SUPERVISOR_URL, json=payload_4, timeout=60.0) as r:
        for line in r.iter_lines():
            if not line.strip():
                if current_event_lines:
                    parse_sse_event_string("".join(current_event_lines), a2ui_parts)
                    current_event_lines = []
            else:
                if line.startswith("data:"):
                    current_event_lines.append(line[5:])
        if current_event_lines:
            parse_sse_event_string("".join(current_event_lines), a2ui_parts)
            
    print(f"✓ Phase D.1 Completed. Extracted A2UI count: {len(a2ui_parts)}")
    print(json.dumps(a2ui_parts, indent=2))
    assert len(a2ui_parts) > 0, "No A2UI dashboard returned for loyalty initialization!"
    assert "circana-loyalty-dashboard" in str(a2ui_parts), "circana-loyalty-dashboard missing from A2UI parts!"

    # --------------------------------------------------
    # PHASE 5: Launch Campaign
    # --------------------------------------------------
    print("\n=== PHASE D.2: Send Loyalty Campaign launch action ===")
    action_3 = {
        "actionId": "btn_launch_campaign",
        "payload": {
            "product": "Diet Pepsi 12pk",
            "discount_pct": "15",
            "points_mult": "3"
        }
    }
    payload_5 = {
        "message": {
            "role": "ROLE_USER",
            "message_id": "msg-5",
            "context_id": context_id,
            "content": [{"data": {"data": action_3}}]
        }
    }
    
    last_text = ""
    current_event_lines = []
    with httpx.stream("POST", SUPERVISOR_URL, json=payload_5, timeout=60.0) as r:
        for line in r.iter_lines():
            if not line.strip():
                if current_event_lines:
                    last_text = parse_sse_event_string("".join(current_event_lines), [])
                    current_event_lines = []
            else:
                if line.startswith("data:"):
                    current_event_lines.append(line[5:])
        if current_event_lines:
            last_text = parse_sse_event_string("".join(current_event_lines), [])
            
    print(f"✓ Phase D.2 Completed. Response: {last_text}")
    assert "success" in last_text.lower(), "Campaign launch confirmation failed!"
    print("\n==================================================")
    print("ALL E2E PILELINE TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    run_e2e_test()
