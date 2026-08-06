import os
from pymongo import AsyncMongoClient
from beanie import init_beanie
from services.game_logic.models.puzzle import Puzzle
from services.game_logic.models.game_session import GameSession
from services.game_logic.models.multiplayer_history import MultiplayerHistory
from dotenv import load_dotenv

load_dotenv()

_client: AsyncMongoClient = None


async def connect_db():
    global _client
    try:
        mongodb_uri = os.getenv("MONGODB_URL")
        if not mongodb_uri:
            raise ValueError("MONGODB_URL environment variable is missing!")

        _client = AsyncMongoClient(mongodb_uri)
        db = _client["game_logic"]  # Separate database for game logic

        await init_beanie(
            database=db,
            document_models=[Puzzle, GameSession, MultiplayerHistory],  
        )
        print("✅ Game Logic DB connected, Puzzle, GameSession, and MultiplayerHistory registered")

    except Exception as error:
        print(f"❌ DB error: {error}")
        raise


async def disconnect_db():
    global _client
    if _client:
        _client.close()
        print("MongoDB connection closed")
