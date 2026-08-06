import httpx
import json
import os
import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from shared.redis_client import get_redis_client

scheduler = AsyncIOScheduler()

async def generate_daily_challenge(retries=3, delay=5):
    """Fetches a new puzzle from AI generator and saves it to Redis."""
    print("⏳ Generating new daily challenge...")
    
    ai_url = os.getenv("AI_WORD_GENERATOR_URL", "http://127.0.0.1:8003")
        
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{ai_url}/api/generate",
                    json={
                        "difficulty": 8, 
                        "mode": "daily_challenge", 
                        "category": "Daily Challenge"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    redis = await get_redis_client()
                    
                    challenge_data = {
                        "word": data["word"],
                        "scrambled": data["scrambled"],
                        "hint": data.get("hint", ""),
                        "category": data.get("category", "Daily Challenge"),
                        "date": datetime.utcnow().strftime("%Y-%m-%d")
                    }
                    
                    await redis.set("daily_challenge:today", json.dumps(challenge_data), ex=90000)
                    print(f"✅ Daily challenge generated successfully: {data['word']}")
                    return # Success, exit the loop!
                else:
                    print(f"❌ Failed to generate daily challenge. Status: {response.status_code}")
                    
        except Exception as e:
            print(f"⚠️ Attempt {attempt + 1}/{retries} failed to connect to AI Service: {e}")
            if attempt < retries - 1:
                print(f"   Waiting {delay} seconds before retrying...")
                await asyncio.sleep(delay)
            else:
                print("❌ All attempts to generate daily challenge failed.")

def start_scheduler():
    # Run every day at midnight (UTC)
    scheduler.add_job(generate_daily_challenge, 'cron', hour=0, minute=0)
    scheduler.start()
