from datetime import datetime, timezone
from typing import Optional
from beanie import Document
from pydantic import Field


class LeaderboardEntry(Document):
    """
    One entry per player per board_id + mode combination.
    Only the player's BEST score is kept (upsert on higher score).
    """
    firebase_uid: str                   # Player identifier (same as auth-service)
    display_name: Optional[str] = None  # Shown on the leaderboard UI in Unity
    photo_url: Optional[str] = None     # Player avatar URL

    board_id: str                       # "global", "weekly", "daily"
    mode: str = "simple"                # "simple", "time_attack", "survival"
    score: int                          # Player's personal best score for this board+mode

    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "leaderboard_entries"    # MongoDB collection name

    class Config:
        json_schema_extra = {
            "example": {
                "firebase_uid": "abc123",
                "display_name": "WordMaster",
                "board_id": "global",
                "mode": "time_attack",
                "score": 1500,
            }
        }
