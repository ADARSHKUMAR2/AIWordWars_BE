"""
Time Attack Mode Controller
Player solves as many words as possible within 60 seconds.
Consecutive correct answers build a combo multiplier.
"""

TIME_ATTACK_DURATION = 60  # seconds
MAX_COMBO = 5              # Max combo multiplier


def calculate_time_attack_score(
    difficulty: int, 
    time_taken: float, 
    correct: bool, 
    combo: int = 1
) -> int:
    """
    Calculate score for Time Attack mode with combo multiplier.
    
    Args:
        difficulty: Puzzle difficulty (1-10)
        time_taken: Time to solve in seconds
        correct: Whether the answer was correct
        combo: Current combo count (1 = no combo, 2 = 2x, etc.)
    
    Returns:
        int: Score (0 if incorrect)
    """
    if not correct:
        return 0
    
    base_score = difficulty * 10
    
    # Time bonus (critical in Time Attack - speed is everything)
    if time_taken < 5:
        time_bonus = 50
    elif time_taken < 10:
        time_bonus = 30
    elif time_taken < 15:
        time_bonus = 15
    else:
        time_bonus = 5
    
    # Combo multiplier (capped at MAX_COMBO)
    effective_combo = min(combo, MAX_COMBO)
    multiplied_score = (base_score + time_bonus) * effective_combo
    
    return multiplied_score


def get_next_combo(current_combo: int, correct: bool) -> int:
    """
    Determine the next combo value based on whether answer was correct.
    
    Args:
        current_combo: Current combo count
        correct: Whether the answer was correct
    
    Returns:
        int: Next combo count (1 if incorrect, current+1 if correct)
    """
    if not correct:
        return 1  # Reset combo on wrong answer
    return min(current_combo + 1, MAX_COMBO)


def is_session_expired(elapsed_seconds: float) -> bool:
    """
    Check if the Time Attack session has expired.
    
    Args:
        elapsed_seconds: Time elapsed since session started
    
    Returns:
        bool: True if the session duration has been exceeded
    """
    return elapsed_seconds >= TIME_ATTACK_DURATION
