"""
Inventory Model - Tracks what items each user owns

This stores:
- Consumable items (hints that get used up)
- Non-consumable items (permanent purchases like "remove ads")
- Premium status
- Owned themes, avatars, etc.

Why separate from User model:
- Different database (MongoDB vs PostgreSQL for users)
- Faster queries for inventory-specific operations
- Easier to add new item types
"""

from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import List, Optional

class InventoryItem(Document):
    """
    Represents a user's inventory - what they own
    """
    
    # Firebase UID
    user_id: str = Field(..., unique=True, index=True)
    
    # Consumable items
    hints: int = Field(default=0)  # Number of hints owned
    
    # Non-consumable items (boolean - either owned or not)
    remove_ads: bool = Field(default=False)
    
    # Premium/Battle Pass
    is_premium: bool = Field(default=False)
    premium_expires_at: Optional[datetime] = None  # For subscription-based premium
    
    # Cosmetic items (themes, avatars, titles)
    owned_themes: List[str] = Field(default_factory=list)  # e.g., ["dark_mode", "neon"]
    owned_avatars: List[str] = Field(default_factory=list)
    owned_titles: List[str] = Field(default_factory=list)
    
    # Active cosmetics (what user currently has equipped)
    active_theme: Optional[str] = None
    active_avatar: Optional[str] = None
    active_title: Optional[str] = None
    
    # Tracking
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "inventory"
