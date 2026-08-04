from datetime import datetime, timezone
from typing import Optional
from beanie import Document
from pydantic import Field, ConfigDict
from uuid import uuid4


class GameSession(Document):
    session_id: str 
    user_id: Optional[str] = None       # Firebase UID (optional for now)
    puzzle_id: str                      # Reference to Puzzle
    
    # Game data
    mode: str = "simple"
    difficulty: int
    
    # Result data
    player_answer: str
    correct: bool
    time_taken: float                   # seconds
    score: int
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    
    class Settings:
        name = "game_sessions"
    
    model_config = ConfigDict (
        json_schema_extra = {
            "example": {
                "session_id": "660e8400-e29b-41d4-a716-446655440001",
                "user_id": "firebase_uid_123",
                "puzzle_id": "550e8400-e29b-41d4-a716-446655440000",
                "mode": "simple",
                "difficulty": 5,
                "player_answer": "MAGNET",
                "correct": True,
                "time_taken": 12.5,
                "score": 100
            }
        }
    ) 
    
