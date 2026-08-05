from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.game_logic.controllers.puzzle_controller import create_new_puzzle, validate_answer, save_game_session
from services.game_logic.controllers.time_attack_controller import (
    calculate_time_attack_score,
    get_next_combo,
    is_session_expired
)
from services.game_logic.models.puzzle import Puzzle

router = APIRouter(prefix="/api/time-attack")

class TimeAttackSolveRequest(BaseModel):
    puzzle_id: str
    answer: str
    time_taken: float
    current_combo: int = 1
    session_elapsed: float = 0.0  # Total time elapsed in the 60s session
    user_id: Optional[str] = None

class TimeAttackNewPuzzleRequest(BaseModel):
    difficulty: int = 5
    category: Optional[str] = None
    user_id: Optional[str] = None

@router.post("/puzzle/new")
async def get_new_time_attack_puzzle(request: TimeAttackNewPuzzleRequest):
    """Get a new puzzle for Time Attack mode"""
    try:
        puzzle = await create_new_puzzle(
            difficulty=request.difficulty,
            mode="time_attack",
            category=request.category,
            user_id=request.user_id
        )
        return {
            "puzzle_id": puzzle.puzzle_id,
            "scrambled": puzzle.scrambled,
            "difficulty": puzzle.difficulty,
            "hint": puzzle.hint,
            "mode": "time_attack",
            "category": puzzle.category,
            "session_duration": 60  # inform the client of total session time
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate puzzle: {str(e)}")

@router.post("/puzzle/solve")
async def solve_time_attack_puzzle(request: TimeAttackSolveRequest):
    """Validate a player's answer in Time Attack mode"""
    
    # Check if session is still valid
    if is_session_expired(request.session_elapsed):
        return {
            "correct": False,
            "score": 0,
            "new_combo": 1,
            "session_expired": True,
            "feedback": "Time's up! Session has ended."
        }
    
    # Retrieve puzzle from DB
    puzzle = await Puzzle.find_one(Puzzle.puzzle_id == request.puzzle_id)
    if not puzzle:
        raise HTTPException(status_code=404, detail="Puzzle not found")
    
    # Validate answer
    correct = validate_answer(puzzle.word, request.answer)
    
    # Calculate combo and score
    new_combo = get_next_combo(request.current_combo, correct)
    score = calculate_time_attack_score(
        difficulty=puzzle.difficulty,
        time_taken=request.time_taken,
        correct=correct,
        combo=request.current_combo  # Use the combo BEFORE this answer
    )
    
    # Save game session
    await save_game_session(
        puzzle_id=puzzle.puzzle_id,
        difficulty=puzzle.difficulty,
        mode="time_attack",
        player_answer=request.answer,
        correct=correct,
        time_taken=request.time_taken,
        score=score,
        user_id=request.user_id
    )
    
    return {
        "correct": correct,
        "score": score,
        "new_combo": new_combo,
        "session_expired": False,
        "feedback": f"{'Correct! 🔥 Combo x{new_combo}!' if correct else 'Wrong! Combo reset.'}",
        "correct_answer": None if correct else puzzle.word
    }
