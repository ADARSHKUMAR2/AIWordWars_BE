import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv
from gateway.utils import setup_cors, register_proxy, register_proxy_with_header

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Gateway starting up...")
    yield
    print("🛑 Gateway shutting down...")
    if hasattr(app.state, "proxy_clients"):
        for client in app.state.proxy_clients:
            await client.aclose()
        print("✅ All proxy clients closed")


app = FastAPI(title="WordWars AI - API Gateway", version="1.0.0", lifespan=lifespan)

setup_cors(app)

# Register proxy routes
register_proxy(
    app,
    path_prefix="/auth",
    target_url=os.getenv("AUTH_SERVICE_URL", "http://127.0.0.1:8001"),
)

register_proxy(
    app, 
    path_prefix="/game",
    target_url=os.getenv("GAME_SERVICE_URL", "http://127.0.0.1:8004")
)

# Protected routes will use register_proxy_with_header once session auth is added
# register_proxy_with_header(
#     app,
#     path_prefix="/game",
#     target_url=os.getenv("GAME_SERVICE_URL", "http://127.0.0.1:8004"),
# )


@app.get("/")
async def root():
    return {"message": "WordWars AI Gateway", "status": "healthy"}


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "gateway"}


PORT = int(os.getenv("PORT", 8000))

if __name__ == "__main__":
    print(f"🚀 Gateway booting on port {PORT}...")
    print(f"📍 /auth → {os.getenv('AUTH_SERVICE_URL', 'http://127.0.0.1:8001')}")
    print(f"📍 /game → {os.getenv('GAME_SERVICE_URL', 'http://127.0.0.1:8002')}")
    uvicorn.run("gateway.main:app", host="0.0.0.0", port=PORT, reload=True)
