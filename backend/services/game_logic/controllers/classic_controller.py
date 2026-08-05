"""
Classic Mode Controller
Standard single-puzzle mode. Player solves one word at a time.
Score is based on difficulty and time taken.
"""


def calculate_classic_score(difficulty: int, time_taken: float, correct: bool) -> int:
    """
    Calculate score for Classic mode.
    
    Args:
        difficulty: Puzzle difficulty (1-10)
        time_taken: Time to solve in seconds
        correct: Whether the answer was correct
    
    Returns:
        int: Score
    """
    if not correct:
        return 0
    
    base_score = difficulty * 10
    
    # Time bonus (faster = more points)
    if time_taken < 5:
        time_bonus = 50
    elif time_taken < 10:
        time_bonus = 30
    elif time_taken < 20:
        time_bonus = 10
    else:
        time_bonus = 0
    
    return base_score + time_bonus
