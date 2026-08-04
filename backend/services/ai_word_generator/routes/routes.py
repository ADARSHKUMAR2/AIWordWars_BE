from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.ai_word_generator.controllers.word_generator import generate_word

router = APIRouter(prefix="/api")


class GenerateRequest(BaseModel):
    difficulty: int = 1


@router.post("/generate")
async def generate_puzzle(body: GenerateRequest):
    """
    Generate a word puzzle.
    
    Request: { "difficulty": 1-10 }
    Response: { "word": "MAGNET", "scrambled": "NGAEMT", "difficulty": 1, "hint": "6-letter word" }
    """
    if not 1 <= body.difficulty <= 10:
        raise HTTPException(status_code=400, detail="Difficulty must be between 1 and 10")
    
    try:
        puzzle = generate_word(body.difficulty)
        return puzzle
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"Failed to generate word: {str(e)}")


@router.get("/health")
def health_check():
    return {"status": "ok", "service": "ai-word-generator"}
