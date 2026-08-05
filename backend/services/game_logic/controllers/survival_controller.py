"""
Survival Mode Controller
Player has a limited number of hearts (lives).
Wrong answers or too-slow solves cost a heart.
Game ends when all hearts are lost.
"""

STARTING_HEARTS = 3
MAX_TIME_PER_WORD = 30  # Seconds before a heart is automatically lost


def calculate_survival_score(
    difficulty: int, 
    time_taken: float, 
    correct: bool, 
    hearts_remaining: int
) -> int:
    """
    Calculate score for Survival mode.
    Includes a bonus based on remaining hearts.
    
    Args:
        difficulty: Puzzle difficulty (1-10)
        time_taken: Time to solve in seconds
        correct: Whether the answer was correct
        hearts_remaining: Hearts remaining before this answer
    
    Returns:
        int: Score (0 if incorrect or time exceeded)
    """
    if not correct:
        return 0
    
    if time_taken >= MAX_TIME_PER_WORD:
        return 0  # Timed out - no score, heart penalty applied separately
    
    base_score = difficulty * 10
    
    # Time bonus
    if time_taken < 5:
        time_bonus = 50
    elif time_taken < 10:
        time_bonus = 30
    elif time_taken < 20:
        time_bonus = 10
    else:
        time_bonus = 0
    
    # Heart bonus: more hearts remaining = higher score
    heart_bonus = hearts_remaining * 10
    
    return base_score + time_bonus + heart_bonus


def get_hearts_after_answer(hearts: int, correct: bool, time_taken: float) -> int:
    """
    Update the heart count after a player's answer.
    
    Args:
        hearts: Current number of hearts
        correct: Whether the answer was correct
        time_taken: Time taken to answer in seconds
    
    Returns:
        int: New number of hearts (0 = game over)
    """
    if not correct:
        return max(0, hearts - 1)  # Wrong answer: lose a heart
    
    if time_taken >= MAX_TIME_PER_WORD:
        return max(0, hearts - 1)  # Timed out: lose a heart
    
    return hearts  # Correct and in time: no change


def is_game_over(hearts: int) -> bool:
    """
    Check if the survival game is over.
    
    Args:
        hearts: Current number of hearts
    
    Returns:
        bool: True if game over
    """
    return hearts <= 0
