FROM python:3.10-slim

WORKDIR /app

# Install minimal server dependencies
RUN pip install fastapi uvicorn

# Copy the MCP server source script
COPY agents/circana_pilot_agent/mcp_servers/circana_mcp_server.py /app/mcp_server.py

# Expose HTTP port 8080
EXPOSE 8080

# Launch the FastAPI app in HTTP mode
CMD ["python", "mcp_server.py", "--http", "--host", "0.0.0.0", "--port", "8080"]
