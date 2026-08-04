import os
from pymongo import AsyncMongoClient
from beanie import init_beanie
from services.auth.models.user import User
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
        db = _client["auth"]

        await init_beanie(
            database=db,
            document_models=[User]
        )
        print("✅ DB connected and User model registered")

    except Exception as error:
        print(f"❌ DB error: {error}")
        raise


async def disconnect_db():
    global _client
    if _client:
        _client.close()
        print("MongoDB connection closed")
