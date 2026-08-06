from datetime import datetime, timezone
from typing import Optional
from beanie import Document
from pydantic import Field, ConfigDict


class MultiplayerHistory(Document):
    room_code: str
    player1_uid: str
    player2_uid: str
    winner_uid: Optional[str] = None     # Null if it was a draw
    loser_uid: Optional[str] = None      # Null if it was a draw
    word: str
    difficulty: int
    winning_time: Optional[float] = None # How fast the winner solved it
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "multiplayer_history"
        
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "room_code": "AB12CD",
                "player1_uid": "user_123",
                "player2_uid": "user_456",
                "winner_uid": "user_123",
                "loser_uid": "user_456",
                "word": "MAGNET",
                "difficulty": 5,
                "winning_time": 14.5
            }
        }
    )
