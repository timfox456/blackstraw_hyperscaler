import os
import re
import subprocess
import sys

def deploy_mcp():
    project_id = "shade-sandbox"
    region = "us-central1"
    service_name = "circana-mcp-server"
    
    print(f"Starting deployment of MCP Server to Google Cloud Run in project '{project_id}'...")
    
    cmd = [
        "gcloud", "run", "deploy", service_name,
        "--source", ".",
        "--port", "8080",
        "--region", region,
        "--project", project_id,
        "--no-allow-unauthenticated" # Secure access control
    ]
    
    try:
        # Execute the deployment process
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        service_url = None
        for line in process.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            # Match service URL from gcloud output
            if "Service URL:" in line:
                match = re.search(r"Service URL:\s*(https://[^\s]+)", line)
                if match:
                    service_url = match.group(1)
                    
        process.wait()
        if process.returncode != 0:
            print("❌ Deployment failed.")
            sys.exit(process.returncode)
            
        if not service_url:
            print("❌ Deployment completed, but could not extract the service URL.")
            sys.exit(1)
            
        print(f"\n✓ MCP Server deployed successfully! URL: {service_url}")
        
        # Update .env file
        env_path = ".env"
        env_content = ""
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                env_content = f.read()
                
        # Replace or append MCP_SERVER_URL
        if "MCP_SERVER_URL=" in env_content:
            env_content = re.sub(r"MCP_SERVER_URL=[^\n]*", f"MCP_SERVER_URL={service_url}", env_content)
        else:
            env_content = env_content.strip() + f"\nMCP_SERVER_URL={service_url}\n"
            
        with open(env_path, "w") as f:
            f.write(env_content)
            
        print("✓ Updated .env file with remote MCP_SERVER_URL.")
        
    except Exception as e:
        print(f"❌ Error during deployment: {e}")
        sys.exit(1)

if __name__ == "__main__":
    deploy_mcp()
