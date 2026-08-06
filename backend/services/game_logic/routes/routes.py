from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from services.game_logic.controllers.puzzle_controller import (
    create_new_puzzle,
    validate_answer,
    calculate_score,
    save_game_session,
    calculate_rewards
)
from services.game_logic.models.puzzle import Puzzle
from services.game_logic.services.ai_client import award_progression, submit_leaderboard_score
from services.game_logic.models.multiplayer_history import MultiplayerHistory
from shared.redis_client import get_redis_client

router = APIRouter(prefix="/api")

# Store puzzles temporarily (in production, use Redis)
puzzle_cache = {}

class NewPuzzleRequest(BaseModel):
    difficulty: int = 5
    mode: str = "simple"
    category: str | None = None
    user_id: str | None = None

class SolveRequest(BaseModel):
    puzzle_id: str
    answer: str
    time_taken: float
    user_id: Optional[str] = None
    display_name: Optional[str] = None  # Optional: passed from Unity for leaderboard display name
    photo_url: Optional[str] = None 

class MultiplayerHistoryRequest(BaseModel):
    room_code: str
    player1_uid: str
    player2_uid: str
    winner_uid: Optional[str] = None
    loser_uid: Optional[str] = None
    word: str
    difficulty: int
    winning_time: Optional[float] = None

@router.post("/puzzle/new")
async def get_new_puzzle(request: NewPuzzleRequest, x_user_id: str = Header(None)):
    """Generate a new puzzle"""
    try:
        if not 1 <= request.difficulty <= 10:
            raise HTTPException(status_code=400, detail="Difficulty must be between 1 and 10")
        
        puzzle = await create_new_puzzle(
            difficulty=request.difficulty,
            mode=request.mode,
            category=request.category,
            user_id=request.user_id
        )
        
        # Cache the puzzle for validation
        puzzle_cache[puzzle.puzzle_id] = puzzle

        
        return {
            "puzzle_id": puzzle.puzzle_id,
            "scrambled": puzzle.scrambled,
            "difficulty": puzzle.difficulty,
            "hint": puzzle.hint,
            "mode": puzzle.mode,
            "category": puzzle.category
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate puzzle: {str(e)}")


@router.post("/puzzle/solve")
async def solve_puzzle(request: SolveRequest):
    """Validate a player's answer"""
    
    # Retrieve puzzle from cache
    # puzzle = puzzle_cache.get(request.puzzle_id)

     # Retrieve puzzle from DB
    puzzle = await Puzzle.find_one(Puzzle.puzzle_id == request.puzzle_id)
    if not puzzle:
        raise HTTPException(status_code=404, detail="Puzzle not found")
    
    # Validate answer
    correct = validate_answer(puzzle.word, request.answer)
    
    # Calculate score
    score = calculate_score(puzzle.difficulty, request.time_taken, correct)

    # Store solve time in Redis if user solved correctly
    if request.user_id and correct:
        try:
            redis = await get_redis_client()
            key = f"player:{request.user_id}:solve_times"
            
            # Add the solve time to the list (most recent first)
            await redis.lpush(key, str(request.time_taken))
            
            # Keep only the last 10 solve times
            await redis.ltrim(key, 0, 9)
            
            # Set expiry to 30 days
            await redis.expire(key, 60 * 60 * 24 * 30)
            
            print(f"✅ Stored solve time {request.time_taken}s for user {request.user_id}")
        except Exception as e:
            print(f"⚠️ Failed to store solve time in Redis: {e}")
            # Don't fail the request if Redis fails
    
    # Save game session to DB
    await save_game_session(
        puzzle_id=puzzle.puzzle_id,
        difficulty=puzzle.difficulty,
        mode=puzzle.mode,
        player_answer=request.answer,
        correct=correct,
        time_taken=request.time_taken,
        score=score,
        user_id=request.user_id
    )

    #  Award XP & Coins ──────────────────────────────
    xp_earned, coins_earned = calculate_rewards(puzzle.difficulty, correct)
    progression_result = None
    leaderboard_result = None

    if request.user_id and correct:
        progression_result = await award_progression(
            firebase_uid=request.user_id,
            xp_earned=xp_earned,
            coins_earned=coins_earned,
        )

        leaderboard_result = await submit_leaderboard_score(
            firebase_uid=request.user_id,
            display_name=request.display_name,
            photo_url=request.photo_url,
            board_id="global",
            mode=puzzle.mode or "simple",
            score=score,
        )

    print(f"📤 Solve response → correct={correct}, score={score}, xp_earned={xp_earned}, coins_earned={coins_earned}")

    
    return {
        "correct": correct,
        "time_taken": request.time_taken,
        "score": score,
        "feedback": "Correct! Great job!" if correct else "Incorrect. Try again!",
        "correct_answer": None if correct else puzzle.word,
        "xp_earned": xp_earned,
        "coins_earned": coins_earned,
        "progression": progression_result,
        "leaderboard": leaderboard_result,
    }

@router.post("/multiplayer/history")
async def save_multiplayer_history(request: MultiplayerHistoryRequest):
    """Save the result of a multiplayer match to the database."""
    try:
        history = MultiplayerHistory(
            room_code=request.room_code,
            player1_uid=request.player1_uid,
            player2_uid=request.player2_uid,
            winner_uid=request.winner_uid,
            loser_uid=request.loser_uid,
            word=request.word,
            difficulty=request.difficulty,
            winning_time=request.winning_time
        )
        await history.insert()
        return {"status": "success", "message": "Match history saved."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save history: {str(e)}")