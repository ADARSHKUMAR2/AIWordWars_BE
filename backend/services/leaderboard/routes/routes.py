from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from services.leaderboard.controllers.controller import (
    submit_score,
    get_leaderboard,
    get_player_rank,
)

router = APIRouter(prefix="/api")


class SubmitScoreRequest(BaseModel):
    firebase_uid: str
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    board_id: str           # "global", "weekly", "daily"
    mode: str = "simple"    # game mode
    score: int


@router.post("/scores")
async def post_score(body: SubmitScoreRequest):
    """
    Submit a player's score to the leaderboard.
    Only updates if the new score is higher than their existing best.
    Called internally by game-logic-service after a game ends.
    """
    try:
        result = await submit_score(
            firebase_uid=body.firebase_uid,
            display_name=body.display_name,
            photo_url=body.photo_url,
            board_id=body.board_id,
            mode=body.mode,
            score=body.score,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scores/{board_id}")
async def fetch_leaderboard(board_id: str, mode: str = "simple", limit: int = 20):
    """
    Fetch the top N scores for a board.
    Called by Unity to display the Leaderboards screen.
    Example: GET /api/scores/global?mode=time_attack&limit=10
    """
    try:
        if limit > 100:
            raise HTTPException(status_code=400, detail="Limit cannot exceed 100")
        results = await get_leaderboard(board_id=board_id, mode=mode, limit=limit)
        return {
            "board_id": board_id,
            "mode": mode,
            "entries": results
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scores/{board_id}/rank/{firebase_uid}")
async def fetch_player_rank(board_id: str, firebase_uid: str, mode: str = "simple"):
    """
    Get a specific player's rank on a leaderboard.
    Called by Unity to show 'Your Rank: #42' on the HUD.
    """
    try:
        result = await get_player_rank(
            firebase_uid=firebase_uid,
            board_id=board_id,
            mode=mode,
        )
        if not result:
            raise HTTPException(status_code=404, detail="Player has no score on this board yet")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
