import random
from typing import TypedDict, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from services.ai_word_generator.config.client import get_gemini_client
from rich import print
import uuid
from services.ai_word_generator.graph.graph import create_word_generator_graph
from services.ai_word_generator.graph.nodes import WordGeneratorState
from shared.redis_client import get_redis_client

class WordPuzzle(TypedDict):
    """Word puzzle with word, scrambled letters, difficulty, and hint"""
    word: str
    scrambled: str
    difficulty: int
    hint: str

def generate_word(difficulty: int = 1, category: Optional[str] = None, mode: str = "simple", user_id: Optional[str] = None) -> WordPuzzle:
    """
    Generates a word puzzle using LangGraph workflow.
    
    Args:
        difficulty: 1-10, where 1 is easy (3-4 letters) and 10 is hard (8+ letters)
        category: Optional category for the word
        mode: The game mode (e.g., "simple", "challenge")
        user_id: The user's Firebase UID
    
    Returns:
        WordPuzzle with word, scrambled letters, difficulty, and hint
    """
    
    # Define difficulty parameters
    if difficulty <= 3:
        word_length = "3 to 4 letters"
        complexity = "simple, common everyday words"
    elif difficulty <= 6:
        word_length = "5 to 6 letters"
        complexity = "moderately common words"
    else:
        word_length = "7+ letters"
        complexity = "advanced or uncommon words"
    
    # If no category provided, select a random one
    if not category:
        categories = ["animals", "nature", "emotions", "technology", "food", 
                     "sports", "professions", "music", "colors", "space", 
                     "weather", "clothing"]
        category = random.choice(categories)
    
    # Initialize state
    initial_state = WordGeneratorState(
        difficulty=difficulty,
        category=category,
        random_seed=str(uuid.uuid4())[:8],
        complexity=complexity,
        word_length=word_length,
        word="",
        scrambled="",
        hint=""
    )
    
    # Create and run the workflow
    app = create_word_generator_graph()
    final_state = app.invoke(initial_state)
    
    print(f"[bold green]Generated word:[/bold green] {final_state['word']} | "
          f"[bold yellow]Scrambled:[/bold yellow] {final_state['scrambled']} | "
          f"[bold blue]Difficulty:[/bold blue] {final_state['difficulty']} | ")
    
    return WordPuzzle(
        word=final_state["word"],
        scrambled=final_state["scrambled"],
        difficulty=final_state['difficulty'],
        hint=final_state["hint"]
    )

async def calculate_adaptive_difficulty(user_id: str, base_difficulty: int) -> int:
    """
    Calculate adjusted difficulty based on user's recent performance.
    
    Args:
        user_id: The user's Firebase UID
        base_difficulty: The requested difficulty level (1-10)
    
    Returns:
        Adjusted difficulty level (1-10)
    """
    try:
        redis = await get_redis_client()
        key = f"player:{user_id}:solve_times"
        
        # Get last 10 solve times
        times = await redis.lrange(key, 0, 9)

        # Minimum 3 games before adaptive difficulty kicks in
        if not times or len(times) < 3:
            # Not enough data, return base difficulty
            print(f"[yellow]Not enough data for adaptive difficulty. Using base: {base_difficulty}[/yellow]")
            return base_difficulty
        
        # Convert to floats and calculate average
        times_float = [float(t) for t in times]
        avg_time = sum(times_float) / len(times_float)
        
        print(f"[cyan]Average solve time: {avg_time:.2f}s (from {len(times)} games)[/cyan]")
        
        # Adaptive adjustment logic
        adjustment = 0
        if avg_time < 10:
            adjustment = +2  # Very fast - increase significantly
            print("[green]Player is very fast! Increasing difficulty by +2[/green]")
        elif avg_time < 20:
            adjustment = +1  # Fast - increase slightly
            print("[green]Player is fast! Increasing difficulty by +1[/green]")
        elif avg_time > 60:
            adjustment = -2  # Very slow - decrease significantly
            print("[yellow]Player is struggling. Decreasing difficulty by -2[/yellow]")
        elif avg_time > 45:
            adjustment = -1  # Slow - decrease slightly
            print("[yellow]Player is slow. Decreasing difficulty by -1[/yellow]")
        else:
            print("[blue]Player speed is optimal. Keeping difficulty stable.[/blue]")
        
        # Apply adjustment and cap between 1-10
        adjusted = base_difficulty + adjustment
        final_difficulty = max(1, min(10, adjusted))
        
        print(f"[bold magenta]Adaptive Difficulty: {base_difficulty} → {final_difficulty}[/bold magenta]")
        
        return final_difficulty
        
    except Exception as e:
        print(f"[red]Error calculating adaptive difficulty: {e}[/red]")
        return base_difficulty
