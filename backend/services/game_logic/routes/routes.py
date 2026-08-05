from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.game_logic.controllers.puzzle_controller import (
    create_new_puzzle,
    validate_answer,
    calculate_score,
    save_game_session
)
from services.game_logic.models.puzzle import Puzzle

router = APIRouter(prefix="/api")

# Store puzzles temporarily (in production, use Redis)
puzzle_cache = {}

class NewPuzzleRequest(BaseModel):
    difficulty: int = 5
    mode: str = "simple"
    category: str | None = None

class SolveRequest(BaseModel):
    puzzle_id: str
    answer: str
    time_taken: float
    user_id: Optional[str] = None

@router.post("/puzzle/new")
async def get_new_puzzle(request: NewPuzzleRequest):
    """Generate a new puzzle"""
    try:
        if not 1 <= request.difficulty <= 10:
            raise HTTPException(status_code=400, detail="Difficulty must be between 1 and 10")
        
        puzzle = await create_new_puzzle(
            difficulty=request.difficulty,
            mode=request.mode,
            category=request.category
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
    
    return {
        "correct": correct,
        "time_taken": request.time_taken,
        "score": score,
        "feedback": "Correct! Great job!" if correct else "Incorrect. Try again!",
        "correct_answer": None if correct else puzzle.word
    }
