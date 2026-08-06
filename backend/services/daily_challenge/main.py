import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv

from shared.redis_client import get_redis_client, close_redis_client
from shared.exception_handlers import register_exception_handlers
from services.daily_challenge.routes.routes import router as challenge_router
from services.daily_challenge.scheduler import start_scheduler, generate_daily_challenge

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Daily Challenge Service starting up...")
    redis = await get_redis_client()
    
    # Start scheduler to generate new words at midnight
    start_scheduler()
    
    # Check if we have a challenge for today, if not generate one immediately (useful for first startup)
    challenge = await redis.get("daily_challenge:today")
    if not challenge:
        await generate_daily_challenge()
        
    yield
    print("🛑 Daily Challenge Service shutting down...")
    await close_redis_client()

app = FastAPI(title="WordWars AI - Daily Challenge Service", version="1.0.0", lifespan=lifespan)

app.include_router(challenge_router)
register_exception_handlers(app, "Daily Challenge Service")

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "daily_challenge"}

PORT = int(os.getenv("PORT", 8009))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
