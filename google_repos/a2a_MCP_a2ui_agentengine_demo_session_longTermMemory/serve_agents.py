import os
import sys
import argparse
import uvicorn
from fastapi import FastAPI

# Add project root and agents directory to python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "agents")))

# Set environment keys to mock staging configs
project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", os.environ.get("PROJECT_ID", "shade-sandbox"))
location = os.environ.get("GOOGLE_CLOUD_LOCATION", os.environ.get("LOCATION", "us-central1"))
os.environ["PROJECT_ID"] = project_id
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["LOCATION"] = location
os.environ["GOOGLE_CLOUD_LOCATION"] = location

from circana_pilot_agent.sub_agents.pricing_assortment_orchestrator import get_agent_card as get_pricing_card
from circana_pilot_agent.sub_agents.liquid_activate_orchestrator import get_agent_card as get_activate_card
from circana_pilot_agent.sub_agents.loyalty_campaign_orchestrator import get_agent_card as get_loyalty_card
from circana_pilot_agent.sub_agents.profile_agent import get_agent_card as get_profile_card

from circana_pilot_agent.sub_agents_executors import PricingAssortmentExecutor, LiquidActivateExecutor, LoyaltyCampaignExecutor, AudienceProfileExecutor

from vertexai.preview.reasoning_engines import A2aAgent
from a2a.server.apps.rest.fastapi_app import A2ARESTFastAPIApplication

def create_local_app(executor_builder, card_builder, host, port):
    card = card_builder(host=host, port=port)
    a2ui_agent = A2aAgent(
        agent_card=card,
        agent_executor_builder=executor_builder
    )
    a2ui_agent.set_up()
    
    # Overwrite the URL back to local port since set_up overrides it!
    a2ui_agent.agent_card.url = f"http://{host}:{port}"
    
    app = A2ARESTFastAPIApplication(
        agent_card=a2ui_agent.agent_card,
        http_handler=a2ui_agent.request_handler,
    ).build()
    return app

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Serve ADK agents locally.")
    parser.add_argument("--agent", choices=["pricing", "activate", "loyalty", "profile"], required=True, help="Agent type to run")
    parser.add_argument("--port", type=int, required=True, help="Port to serve agent on")
    args = parser.parse_args()
    
    host = "localhost"
    if args.agent == "pricing":
        app = create_local_app(PricingAssortmentExecutor, get_pricing_card, host, args.port)
    elif args.agent == "activate":
        app = create_local_app(LiquidActivateExecutor, get_activate_card, host, args.port)
    elif args.agent == "loyalty":
        app = create_local_app(LoyaltyCampaignExecutor, get_loyalty_card, host, args.port)
    elif args.agent == "profile":
        app = create_local_app(AudienceProfileExecutor, get_profile_card, host, args.port)
        
    print(f"================================================================================")
    print(f"Starting local A2A HTTP Server for {args.agent.upper()} on http://{host}:{args.port}")
    print(f"================================================================================")
    uvicorn.run(app, host="0.0.0.0", port=args.port)
