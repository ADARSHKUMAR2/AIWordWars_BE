from fastapi import APIRouter
from ..controllers.challenge_controller import ChallengeController
from ..models.challenge import DailyChallenge

router = APIRouter(prefix="/api/daily-challenge", tags=["Daily Challenge"])

@router.get("/today", response_model=DailyChallenge)
async def get_todays_challenge():
    """Retrieve the daily challenge for today."""
    return await ChallengeController.get_todays_challenge()
