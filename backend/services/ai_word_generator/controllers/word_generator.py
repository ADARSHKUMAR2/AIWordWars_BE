import random
from typing import TypedDict
from langchain_core.messages import HumanMessage, SystemMessage
from services.ai_word_generator.config.client import get_gemini_client
import uuid
from rich import print


class WordPuzzle(TypedDict):
    word: str
    scrambled: str
    difficulty: int
    hint: str


def generate_word(difficulty: int = 1) -> WordPuzzle:
    """
    Generates a word puzzle using Gemini.
    
    Args:
        difficulty: 1-10, where 1 is easy (3-4 letters) and 10 is hard (8+ letters)
    
    Returns:
        WordPuzzle with word, scrambled letters, difficulty, and hint
    """
    llm = get_gemini_client()
    
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
    
    # Create the prompt
    system_prompt = SystemMessage(content=
                                  """
                                  You are a highly creative word puzzle generator. 
Generate a single, unique English word for a word scramble game. 
You MUST provide a different word every time you are asked.
Return ONLY the word, nothing else. No punctuation, no explanation.
""")

    random_seed = str(uuid.uuid4())[:8]

    categories = ["animals", "nature", "emotions", "technology", "food", "sports", "professions", "music", "colors", "space", "weather", "clothing"]
    random_category = random.choice(categories)

    user_prompt = HumanMessage(content=
                               f"""
                               Generate a single {complexity} word that is {word_length} long.
                               The word MUST be related to this category: {random_category}
Randomizer seed: {random_seed} (Use this to ensure you pick a completely different word than usual!)
Return ONLY the word in uppercase, nothing else. No punctuation, no explanation.
""")
    
    # Call Gemini
    response = llm.invoke([system_prompt, user_prompt])
    word = response.content.strip().upper()
    
    # Scramble the word
    letters = list(word)
    random.shuffle(letters)
    scrambled = ''.join(letters)
    
    # Ensure scrambled is different from original
    while scrambled == word and len(word) > 1:
        random.shuffle(letters)
        scrambled = ''.join(letters)

    print(f"[bold green]Generated word:[/bold green] {word} | [bold yellow]Scrambled:[/bold yellow] {scrambled} | [bold blue]Difficulty:[/bold blue] {difficulty}")
    
    return WordPuzzle(
        word=word,
        scrambled=scrambled,
        difficulty=difficulty,
        hint=f"{len(word)}-letter word"
    )
