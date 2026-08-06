import json
from fastapi import HTTPException
from shared.redis_client import get_redis_client
from ..models.challenge import DailyChallenge

class ChallengeController:
    @staticmethod
    async def get_todays_challenge() -> DailyChallenge:
        redis = await get_redis_client()
        challenge_json = await redis.get("daily_challenge:today")
        
        if not challenge_json:
            raise HTTPException(status_code=404, detail="Daily challenge not found for today. Please wait for generation.")
            
        data = json.loads(challenge_json)
        return DailyChallenge(**data)
