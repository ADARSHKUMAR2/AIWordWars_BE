import httpx
import os
from typing import Dict, Any

AI_SERVICE_URL = os.getenv("AI_WORD_GENERATOR_URL", "http://localhost:8003")

async def get_word_puzzle(difficulty: int, mode: str = "simple", category: str = None, user_id: str = None) -> Dict[str, Any]:
    """Call AI Word Generator service to get a puzzle"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AI_SERVICE_URL}/api/generate",
            json={
                    "difficulty": difficulty,
                    "category": category,
                    "mode": mode,
                    "user_id": user_id
                 },
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()
