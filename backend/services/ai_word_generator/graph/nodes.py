from typing import TypedDict, Optional
import random
from langchain_core.messages import HumanMessage, SystemMessage
from services.ai_word_generator.config.client import get_gemini_client

class WordGeneratorState(TypedDict):
    """State for the word generation workflow"""
    difficulty: int
    category: Optional[str]
    random_seed: str
    complexity: str
    word_length: str
    word: str
    scrambled: str
    hint: str


def generate_word_node(state: WordGeneratorState) -> WordGeneratorState:
    """
    Generates a word puzzle using Gemini.
    
    Args:
        state: WordGeneratorState containing generation parameters
    
    Returns:
        WordGeneratorState with word, scrambled letters, difficulty, and hint
    """
    llm = get_gemini_client()
    
    # Create the prompt
    system_prompt = SystemMessage(content=
                                  """
                                  You are a highly creative word puzzle generator. 
Generate a single, unique English word for a word scramble game. 
You MUST provide a different word every time you are asked.
Return ONLY the word, nothing else. No punctuation, no explanation.
""")

    category_text = f"related to {state['category']}" if state['category'] else "from any category"
    
    user_prompt = HumanMessage(content=
                               f"""
                                Generate a single {state['complexity']} word that is {state['word_length']} long.
    The word MUST be {category_text}.
    Randomizer seed: {state['random_seed']}
    Return ONLY the word in uppercase, nothing else. No punctuation, no explanation.
""")
    
    # Call Gemini
    response = llm.invoke([system_prompt, user_prompt])
    state["word"] = response.content.strip().upper()

    return state

def scramble_word_node(state: WordGeneratorState) -> WordGeneratorState:
    """Scramble the generated word"""
    letters = list(state["word"])
    random.shuffle(letters)
    scrambled = ''.join(letters)
    
    # Ensure scrambled is different from original
    attempts = 0
    while scrambled == state["word"] and len(state["word"]) > 1 and attempts < 10:
        random.shuffle(letters)
        scrambled = ''.join(letters)
        attempts += 1
    
    state["scrambled"] = scrambled
    return state

def generate_hint_node(state: WordGeneratorState) -> WordGeneratorState:
    """Generate a hint for the word"""
    # Simple hint for now - can be enhanced with LLM call later
    state["hint"] = f"{len(state['word'])}-letter word"
    
    # Optional: Enhanced version with LLM (Phase 6)
    # llm = get_gemini_client()
    # prompt = f"Give a short, cryptic hint for the word '{state['word']}' without revealing it directly."
    # response = llm.invoke([HumanMessage(content=prompt)])
    # state["hint"] = response.content.strip()
    
    return state