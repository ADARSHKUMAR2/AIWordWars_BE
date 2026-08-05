import random
from typing import TypedDict, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from services.ai_word_generator.config.client import get_gemini_client
from rich import print
import uuid
from services.ai_word_generator.graph.graph import create_word_generator_graph
from services.ai_word_generator.graph.nodes import WordGeneratorState

class WordPuzzle(TypedDict):
    """Word puzzle with word, scrambled letters, difficulty, and hint"""
    word: str
    scrambled: str
    difficulty: int
    hint: str

def generate_word(difficulty: int = 1, category: Optional[str] = None) -> WordPuzzle:
    """
    Generates a word puzzle using LangGraph workflow.
    
    Args:
        difficulty: 1-10, where 1 is easy (3-4 letters) and 10 is hard (8+ letters)
        category: Optional category for the word
    
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

