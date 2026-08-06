import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv

from shared.exception_handlers import register_exception_handlers
from shared.redis_client import get_redis_client, close_redis_client
from services.matchmaking.routes.routes import router

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Matchmaking Service starting up...")
    await get_redis_client()
    yield
    print("🛑 Matchmaking Service shutting down...")
    await close_redis_client()


app = FastAPI(
    title="WordWars AI - Matchmaking Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)

register_exception_handlers(app, "Matchmaking Service")


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "matchmaking"}


PORT = int(os.getenv("PORT", 8006))

if __name__ == "__main__":
    print(f"🎮 Matchmaking service booting on port {PORT}...")
    uvicorn.run("services.matchmaking.main:app", host="0.0.0.0", port=PORT, reload=True)
