"""
Battle Pass Model - Tracks seasonal battle pass progression

Battle Pass Concept:
- Free tier: Everyone gets basic rewards
- Premium tier: Purchased with real money, unlocks better rewards
- 50 tiers total, earn XP to progress
- Resets each season (e.g., every 3 months)

This model tracks:
- Current tier (1-50)
- XP progress toward next tier
- Which rewards have been claimed
- Premium status
"""

from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import List

class BattlePass(Document):
    """
    Tracks a user's battle pass progress for the current season
    """
    
    # Firebase UID
    user_id: str = Field(..., index=True)
    
    # Season identifier (e.g., "season_1", "2024_winter")
    season_id: str = Field(..., index=True)
    
    # Progression
    current_tier: int = Field(default=1, ge=1, le=50)  # Tier 1-50
    total_xp: int = Field(default=0)  # Total XP earned this season
    
    # Premium status (unlocked via IAP)
    is_premium: bool = Field(default=False)
    
    # Claimed rewards tracking
    # List of tier numbers where rewards were claimed (e.g., [1, 2, 3, 4])
    claimed_free_tiers: List[int] = Field(default_factory=list)
    claimed_premium_tiers: List[int] = Field(default_factory=list)
    
    # Timestamps
    season_start: datetime
    season_end: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "battle_pass"
        indexes = [
            ("user_id", "season_id"),  # Compound index for fast lookup
        ]
