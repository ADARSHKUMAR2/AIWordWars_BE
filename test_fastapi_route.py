from fastapi import FastAPI, Request
import asyncio
from fastapi.testclient import TestClient

app = FastAPI()

route_pattern = "/auth/{path:path}"

async def proxy_handler(request: Request, path: str):
    return {"matched_path": path}

app.api_route(
    route_pattern,
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    include_in_schema=False,
)(proxy_handler)

client = TestClient(app)

response = client.post("/auth/api/login")
print("Response:", response.status_code, response.json())