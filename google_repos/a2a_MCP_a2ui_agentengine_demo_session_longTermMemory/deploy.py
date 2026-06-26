# Prevent requests/urllib3 from using pyOpenSSL to avoid Python 3.13 context mutation bugs
try:
    import urllib3.contrib.pyopenssl
    urllib3.contrib.pyopenssl.inject_into_urllib3 = lambda: None
    urllib3.contrib.pyopenssl.extract_from_urllib3 = lambda: None
except ImportError:
    pass

import os
os.environ["GOOGLE_API_USE_CLIENT_CERTIFICATE"] = "false"

import sys
import vertexai
from dotenv import load_dotenv
from google.auth import default
from google.auth.transport.requests import Request
from google.genai import types
from vertexai.preview.reasoning_engines import A2aAgent

# Load dot env from current directory
load_dotenv(".env")

# Add current directory to python path
sys.path.insert(0, ".")

def main():
    # Change CWD to agents/ to ensure correct packaging namespace
    if os.path.exists("agents"):
        os.chdir("agents")
        
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", os.environ.get("PROJECT_ID"))
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", os.environ.get("LOCATION", "us-central1"))
    storage = os.environ.get("STORAGE_BUCKET")
    api_endpoint = f"{location}-aiplatform.googleapis.com"

    if not project_id or not storage:
        print("Error: GOOGLE_CLOUD_PROJECT (or PROJECT_ID) and STORAGE_BUCKET environment variables must be set.")
        return

    print("=" * 80)
    print(f"Starting deployment to project: {project_id} | location: {location}")
    print("=" * 80)

    vertexai.init(
        project=project_id,
        location=location,
        api_endpoint=api_endpoint,
        staging_bucket=storage,
    )
    print("✓ Vertex AI initialized.")

    client = vertexai.Client(
        project=project_id,
        location=location,
        http_options=types.HttpOptions(api_version="v1beta1")
    )
    print("✓ Vertex AI client created.")

    requirements = [
        "google-cloud-aiplatform[agent_engines,adk]==1.148.0",
        "google-genai==1.73.1",
        "python-dotenv==1.2.2",
        "a2a-sdk==0.3.26",
        "cloudpickle==3.1.2",
        "pydantic==2.13.4",
        "a2ui-agent-sdk==0.2.1",
        "fastapi==0.137.0",
        "google-cloud-storage",
        "httpx>=0.27.0",
        "google-auth>=2.29.0",
        "google-adk==1.31.0",
    ]

    # Package folder relative to CWD (circana_pilot_agent/)
    extra_packages = ["circana_pilot_agent"]

    # Sub-agent deployment specs
    from circana_pilot_agent.sub_agents.pricing_assortment_orchestrator import get_agent_card as get_pricing_card
    from circana_pilot_agent.sub_agents.liquid_activate_orchestrator import get_agent_card as get_activate_card
    from circana_pilot_agent.sub_agents.loyalty_campaign_orchestrator import get_agent_card as get_loyalty_card
    from circana_pilot_agent.sub_agents.profile_agent import get_agent_card as get_profile_card

    from circana_pilot_agent.sub_agents_executors import PricingAssortmentExecutor, LiquidActivateExecutor, LoyaltyCampaignExecutor, AudienceProfileExecutor

    deployments = [
        {
            "key": "PricingAssortmentOrchestrator",
            "display_name": "pricing_assortment_orchestrator",
            "executor": PricingAssortmentExecutor,
            "card_fn": get_pricing_card,
            "description": "Specialist orchestrator analyzing pricing changes and buyer attrition."
        },
        {
            "key": "LiquidActivateOrchestrator",
            "display_name": "liquid_activate_orchestrator",
            "executor": LiquidActivateExecutor,
            "card_fn": get_activate_card,
            "description": "Specialist orchestrator handling segment sizing and activate channel mappings."
        },
        {
            "key": "LoyaltyCampaignOrchestrator",
            "display_name": "loyalty_campaign_orchestrator",
            "executor": LoyaltyCampaignExecutor,
            "card_fn": get_loyalty_card,
            "description": "Specialist orchestrator executing personalized loyalty campaigns."
        },
        {
            "key": "AudienceProfileAgent",
            "display_name": "audience_profile_agent",
            "executor": AudienceProfileExecutor,
            "card_fn": get_profile_card,
            "description": "Specialist orchestrator compiling demographic distribution and audience profile breakdown."
        }
    ]

    import concurrent.futures

    def deploy_agent(dep):
        print(f"🚀 Started deploying sub-agent: {dep['key']}...")
        card = dep['card_fn'](host="localhost", port=80)
        a2ui_agent = A2aAgent(
            agent_card=card,
            agent_executor_builder=dep['executor']
        )
        config = {
            "display_name": dep['display_name'],
            "description": dep['description'],
            "agent_framework": "google-adk",
            "staging_bucket": storage,
            "gcs_dir_name": dep['display_name'],
            "requirements": requirements,
            "extra_packages": extra_packages,
            "env_vars": {
                "NUM_WORKERS": "1",
                "GOOGLE_GENAI_USE_VERTEXAI": "true",
                "PROJECT_ID": project_id,
                "LOCATION": location,
                "GOOGLE_CLOUD_LOCATION": location,
                "MCP_SERVER_URL": os.environ.get("MCP_SERVER_URL", ""),
            }
        }
        try:
            remote_agent = client.agent_engines.create(agent=a2ui_agent, config=config)
            resource_name = remote_agent.api_resource.name
            print(f"✓ Deployed successfully: {dep['key']} -> {resource_name}")
            return dep['key'], resource_name
        except Exception as ex:
            print(f"✗ Deployment failed for {dep['key']}: {ex}")
            import traceback
            traceback.print_exc()
            return dep['key'], None

    deployed_endpoints = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(deploy_agent, dep) for dep in deployments]
        for future in concurrent.futures.as_completed(futures):
            key, resource_name = future.result()
            if resource_name:
                deployed_endpoints[key] = resource_name

    print("\n" + "=" * 80)
    print("ALL SUB-AGENTS DEPLOYED SUCCESSFULLY!")
    print("=" * 80)
    
    # Automatically update .env file
    import re
    env_path = "../.env"
    env_content = ""
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            env_content = f.read()
            
    mapping = {
        "PricingAssortmentOrchestrator": "PRICING_AGENT_URL",
        "LiquidActivateOrchestrator": "ACTIVATE_AGENT_URL",
        "LoyaltyCampaignOrchestrator": "LOYALTY_AGENT_URL",
        "AudienceProfileAgent": "PROFILE_AGENT_URL"
    }
    
    for k, v in deployed_endpoints.items():
        env_var = mapping.get(k)
        if env_var:
            if f"{env_var}=" in env_content:
                env_content = re.sub(f"{env_var}=[^\n]*", f"{env_var}={v}", env_content)
            else:
                env_content = env_content.strip() + f"\n{env_var}={v}\n"
                
    with open(env_path, "w") as f:
        f.write(env_content)
        
    print("✓ Successfully synchronized local .env configuration with new agent engine resource paths!")
    print("=" * 80)

if __name__ == "__main__":
    main()
