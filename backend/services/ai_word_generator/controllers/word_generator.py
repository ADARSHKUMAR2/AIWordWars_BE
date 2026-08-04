import random
from typing import TypedDict
from langchain_core.messages import HumanMessage, SystemMessage
from services.ai_word_generator.config.client import get_gemini_client


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
                                  You are a word puzzle generator. 
Generate a single English word for a word scramble game. 
Return ONLY the word, nothing else. No punctuation, no explanation.
""")
    
    user_prompt = HumanMessage(content=
                               f"""
                               Generate a single {complexity} word that is {word_length} long.
Return ONLY the word in uppercase, nothing else.
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
    
    return WordPuzzle(
        word=word,
        scrambled=scrambled,
        difficulty=difficulty,
        hint=f"{len(word)}-letter word"
    )
