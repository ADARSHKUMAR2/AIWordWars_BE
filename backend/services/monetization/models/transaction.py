"""
Transaction Model - Records all purchase transactions from Google Play

This model stores:
- Purchase tokens from Google Play (unique identifier for each purchase)
- Product IDs (what was purchased: coins, hints, premium, etc.)
- User information
- Validation status (pending, verified, failed)
- Timestamps for auditing

Why we need this:
- Prevent duplicate purchases (same token processed twice)
- Audit trail for financial records
- Fraud detection (track suspicious patterns)
- Customer support (resolve purchase issues)
"""

from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional

class Transaction(Document):
    """
    Represents a single in-app purchase transaction
    """
    
    # Google Play purchase token - unique identifier from Google
    # This is what Unity sends after a successful purchase
    purchase_token: str = Field(..., unique=True, index=True)
    
    # Product ID from your Google Play Console (e.g., "com.wordwars.hints_10")
    product_id: str
    
    # Firebase UID of the user who made the purchase
    user_id: str = Field(..., index=True)
    
    # Purchase status: "pending", "verified", "failed", "refunded"
    status: str = Field(default="pending")
    
    # Order ID from Google Play (used for refund tracking)
    order_id: Optional[str] = None
    
    # Price in micros (e.g., 1990000 = $1.99)
    price_micros: Optional[int] = None
    
    # Currency code (e.g., "USD", "EUR")
    currency_code: Optional[str] = None
    
    # Timestamp when purchase was made (from Google)
    purchase_time_millis: Optional[int] = None
    
    # Timestamp when we processed this transaction
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Timestamp of last update
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Raw response from Google Play API (for debugging)
    google_response: Optional[dict] = None
    
    class Settings:
        name = "transactions"  # MongoDB collection name
        indexes = [
            "purchase_token",  # Fast lookup by token
            "user_id",         # Fast lookup by user
            "status",          # Filter by status
        ]
