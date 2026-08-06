"""
Database Configuration for Monetization Service

Uses Beanie ODM (Object Document Mapper) with MongoDB
Similar to SQLAlchemy but for MongoDB

Why MongoDB for monetization:
- Flexible schema for different item types
- Fast reads for inventory lookups
- Easy to add new cosmetic categories
- Good fit for document-based data (transactions, inventory)
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from dotenv import load_dotenv

from services.monetization.models.transaction import Transaction
from services.monetization.models.inventory import InventoryItem
from services.monetization.models.battle_pass import BattlePass

load_dotenv()

# Global MongoDB client
client: AsyncIOMotorClient = None


async def init_db():
    """
    Initialize MongoDB connection and Beanie ODM
    
    Environment Variables Required:
    - MONGODB_URL: MongoDB connection string
      Example: "mongodb://localhost:27017"
      Or for Atlas: "mongodb+srv://user:pass@cluster.mongodb.net"
    """
    global client
    
    # Get MongoDB URL from environment
    mongodb_url = os.getenv(
        "MONGODB_URL",
        "mongodb://localhost:27017"  # Default for local development
    )
    
    # Database name
    db_name = os.getenv("MONGODB_DATABASE", "wordwars_monetization")
    
    print(f"📊 Connecting to MongoDB: {mongodb_url}")
    print(f"📊 Database: {db_name}")
    
    # Create async MongoDB client
    client = AsyncIOMotorClient(mongodb_url)
    
    # Initialize Beanie with our document models
    await init_beanie(
        database=client[db_name],
        document_models=[
            Transaction,      # IAP transactions
            InventoryItem,    # User inventories
            BattlePass,       # Battle pass progression
        ]
    )
    
    print("✅ Beanie ODM initialized with all models")


async def close_db():
    """
    Close MongoDB connection gracefully
    """
    global client
    if client:
        client.close()
        print("✅ MongoDB connection closed")
