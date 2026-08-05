import httpx
import os
from typing import Dict, Any, Optional

AI_SERVICE_URL = os.getenv("AI_WORD_GENERATOR_URL", "http://localhost:8003")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://127.0.0.1:8001")

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

async def award_progression(
    firebase_uid: str,
    xp_earned: int,
    coins_earned: int,
) -> Optional[Dict[str, Any]]:
    """
    Call the Auth Service to award XP and coins after a correct puzzle solve.
    Returns the updated progression dict, or None if the call fails (non-fatal).
    """
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{AUTH_SERVICE_URL}/api/progression/award",
                json={
                    "firebase_uid": firebase_uid,
                    "xp_earned": xp_earned,
                    "coins_earned": coins_earned,
                },
                timeout=5.0
            )
            if resp.status_code == 200:
                print(f"✅ Awarded {xp_earned} XP and {coins_earned} coins to {firebase_uid}")
                return resp.json()
            else:
                print(f"⚠️ Progression award failed: {resp.text}")
                return None
    except Exception as e:
        print(f"⚠️ Could not award progression: {e}")
        return None  