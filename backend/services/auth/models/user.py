from datetime import datetime, timezone
from typing import Optional
from beanie import Document
from pydantic import Field


class User(Document):
    firebase_uid: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    photo_url: Optional[str] = None
    coins: int = 0
    xp: int = 0
    level: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"  # MongoDB collection name

    class Config:
        json_schema_extra = {
            "example": {
                "firebase_uid": "abc123xyz",
                "display_name": "WordMaster",
                "email": "player@example.com",
                "coins": 100,
                "xp": 500,
                "level": 3,
            }
        }
