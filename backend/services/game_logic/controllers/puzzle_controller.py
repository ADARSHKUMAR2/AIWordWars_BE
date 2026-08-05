import uuid
from datetime import datetime, timezone
from services.game_logic.models.puzzle import Puzzle
from services.game_logic.models.game_session import GameSession
from services.game_logic.services.ai_client import get_word_puzzle
from typing import Optional

async def create_new_puzzle(difficulty: int, mode: str = None, category: Optional[str] = None, user_id: Optional[str] = None) -> Puzzle:
    """Generate a new puzzle using AI service"""
    
    # Call AI service
    ai_puzzle = await get_word_puzzle(difficulty, mode, category, user_id)

    # Add game logic metadata
    puzzle = Puzzle(
        puzzle_id=str(uuid.uuid4()), 
        word=ai_puzzle["word"],
        scrambled=ai_puzzle["scrambled"],
        difficulty=ai_puzzle["difficulty"],
        hint=ai_puzzle["hint"],
        mode=mode,
        category=category
    )

    # Save to MongoDB
    await puzzle.insert()
    
    return puzzle

def validate_answer(puzzle_word: str, player_answer: str) -> bool:
    """Check if the player's answer is correct"""
    return puzzle_word.upper().strip() == player_answer.upper().strip()

def calculate_score(difficulty: int, time_taken: float, correct: bool) -> int:
    """Calculate score based on difficulty and time"""
    if not correct:
        return 0
    
    base_score = difficulty * 10
    time_bonus = max(0, 50 - int(time_taken))  # Bonus for speed
    
    return base_score + time_bonus

async def save_game_session(
    puzzle_id: str,
    difficulty: int,
    mode: str,
    player_answer: str,
    correct: bool,
    time_taken: float,
    score: int,
    user_id: str = None
) -> GameSession:
    """Save game session result to DB"""
    
    session = GameSession(
        session_id=str(uuid.uuid4()),
        user_id=user_id,
        puzzle_id=puzzle_id,
        mode=mode,
        difficulty=difficulty,
        player_answer=player_answer,
        correct=correct,
        time_taken=time_taken,
        score=score,
        completed_at=datetime.now(timezone.utc)
    )
    
    await session.insert()
    
    # Update puzzle analytics
    puzzle = await Puzzle.find_one(Puzzle.puzzle_id == puzzle_id)
    if puzzle:
        puzzle.times_used += 1
        if correct:
            puzzle.times_solved += 1
        # Update average solve time
        if puzzle.times_solved > 0:
            puzzle.average_solve_time = (
                (puzzle.average_solve_time * (puzzle.times_solved - 1) + time_taken) / puzzle.times_solved
            )
        await puzzle.save()
    
    return session