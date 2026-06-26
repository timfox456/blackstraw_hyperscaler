import json
import subprocess
import httpx
import logging

logging.basicConfig(level=logging.INFO)

import os

# Load active IDs dynamically from the root .env configuration file
ACTIVE_IDS = set()
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(root_dir, ".env")
if os.path.exists(dotenv_path):
    with open(dotenv_path, "r") as f:
        for line in f:
            if "=" in line:
                key, val = line.strip().split("=", 1)
                if key in ("PRICING_AGENT_URL", "ACTIVATE_AGENT_URL", "LOYALTY_AGENT_URL"):
                    ACTIVE_IDS.add(val.split("/")[-1])
else:
    print(f"WARNING: .env not found at {dotenv_path}. ACTIVE_IDS will be empty.")


def get_token():
    return subprocess.check_output(["gcloud", "auth", "print-access-token"]).decode().strip()

def main():
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    list_url = "https://us-central1-aiplatform.googleapis.com/v1beta1/projects/shade-sandbox/locations/us-central1/reasoningEngines"
    
    print("Fetching Reasoning Engines list...")
    resp = httpx.get(list_url, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    
    engines = data.get("reasoningEngines", [])
    print(f"Found {len(engines)} reasoning engines in registry.")
    
    deleted_count = 0
    for eng in engines:
        resource_name = eng.get("name")
        engine_id = resource_name.split("/")[-1]
        display_name = eng.get("displayName")
        
        if engine_id in ACTIVE_IDS:
            print(f"Keeping Active Engine: {engine_id} ({display_name})")
            continue
            
        print(f"Deleting Unused Engine: {engine_id} ({display_name})...")
        delete_url = f"https://us-central1-aiplatform.googleapis.com/v1beta1/{resource_name}?force=true"
        retry_delay = 15
        for attempt in range(5):
            del_resp = httpx.delete(delete_url, headers=headers)
            if del_resp.status_code in (200, 202, 204):
                print(f"✓ Delete initiated for {engine_id}")
                deleted_count += 1
                break
            elif del_resp.status_code == 429:
                print(f"⚠ Quota exceeded (429). Retrying in {retry_delay}s... (Attempt {attempt+1}/5)")
                import time
                time.sleep(retry_delay)
                retry_delay *= 1.5
            else:
                print(f"❌ Failed to delete {engine_id}: Status {del_resp.status_code} - {del_resp.text}")
                break
        else:
            print(f"❌ Aborting engine {engine_id} delete after 5 attempts due to persistent quota limits.")

        import time
        time.sleep(5)
            
    print(f"\nCleanup complete. Initiated deletion for {deleted_count} unused reasoning engines.")

if __name__ == "__main__":
    main()
