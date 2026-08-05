"""
Survival Mode Routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.game_logic.controllers.puzzle_controller import create_new_puzzle, validate_answer, save_game_session
from services.game_logic.controllers.survival_controller import (
    calculate_survival_score,
    get_hearts_after_answer,
    is_game_over,
    STARTING_HEARTS,
    MAX_TIME_PER_WORD
)
from services.game_logic.models.puzzle import Puzzle

router = APIRouter(prefix="/api/survival")

class SurvivalSolveRequest(BaseModel):
    puzzle_id: str
    answer: str
    time_taken: float
    current_hearts: int = STARTING_HEARTS
    user_id: Optional[str] = None

class SurvivalNewPuzzleRequest(BaseModel):
    difficulty: int = 5
    category: Optional[str] = None
    user_id: Optional[str] = None

@router.post("/puzzle/new")
async def get_new_survival_puzzle(request: SurvivalNewPuzzleRequest):
    """Get a new puzzle for Survival mode"""
    try:
        puzzle = await create_new_puzzle(
            difficulty=request.difficulty,
            mode="survival",
            category=request.category,
            user_id=request.user_id
        )
        return {
            "puzzle_id": puzzle.puzzle_id,
            "scrambled": puzzle.scrambled,
            "difficulty": puzzle.difficulty,
            "hint": puzzle.hint,
            "mode": "survival",
            "category": puzzle.category,
            "starting_hearts": STARTING_HEARTS,
            "time_limit_per_word": MAX_TIME_PER_WORD
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate puzzle: {str(e)}")

@router.post("/puzzle/solve")
async def solve_survival_puzzle(request: SurvivalSolveRequest):
    """Validate a player's answer in Survival mode"""
    
    # Retrieve puzzle from DB
    puzzle = await Puzzle.find_one(Puzzle.puzzle_id == request.puzzle_id)
    if not puzzle:
        raise HTTPException(status_code=404, detail="Puzzle not found")
    
    # Validate answer
    correct = validate_answer(puzzle.word, request.answer)
    
    # Calculate new hearts
    new_hearts = get_hearts_after_answer(
        hearts=request.current_hearts,
        correct=correct,
        time_taken=request.time_taken
    )
    game_over = is_game_over(new_hearts)
    
    # Calculate score
    score = calculate_survival_score(
        difficulty=puzzle.difficulty,
        time_taken=request.time_taken,
        correct=correct,
        hearts_remaining=request.current_hearts
    )
    
    # Save game session
    await save_game_session(
        puzzle_id=puzzle.puzzle_id,
        difficulty=puzzle.difficulty,
        mode="survival",
        player_answer=request.answer,
        correct=correct,
        time_taken=request.time_taken,
        score=score,
        user_id=request.user_id
    )
    
    return {
        "correct": correct,
        "score": score,
        "hearts_remaining": new_hearts,
        "game_over": game_over,
        "feedback": "Game Over! 💀 No hearts left." if game_over else (
            "Correct! ❤️" if correct else f"Wrong! 💔 {new_hearts} hearts left."
        ),
        "correct_answer": None if correct else puzzle.word
    }
