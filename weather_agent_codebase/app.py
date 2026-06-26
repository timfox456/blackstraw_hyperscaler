import os

os.environ["GOOGLE_CLOUD_PROJECT"] = "rugged-nucleus-499615-p3"
os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

from agent import root_agent