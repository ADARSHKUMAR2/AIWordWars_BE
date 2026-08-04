from datetime import datetime, timezone
from typing import Optional
from beanie import Document
from pydantic import Field, ConfigDict
from uuid import uuid4


class Puzzle(Document):
    puzzle_id: str 
    word: str                           # The actual answer
    scrambled: str                      # Scrambled version
    difficulty: int                     # 1-10
    hint: str                          # AI-generated hint
    mode: str = "simple"               # simple, time_attack, survival, category
    category: Optional[str] = None     # For category mode
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Analytics fields
    times_used: int = 0
    times_solved: int = 0
    average_solve_time: float = 0.0
    
    class Settings:
        name = "puzzles"
    
    model_config =  ConfigDict (
        json_schema_extra = {
            "example": {
                "puzzle_id": "550e8400-e29b-41d4-a716-446655440000",
                "word": "MAGNET",
                "scrambled": "NGAEMT",
                "difficulty": 5,
                "hint": "6-letter word",
                "mode": "simple",
                "times_used": 12,
                "times_solved": 10
            }
        }
    )
    

