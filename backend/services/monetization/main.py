"""
Monetization Service - Main Entry Point

This microservice handles:
- In-App Purchase validation with Google Play
- User inventory management
- Battle Pass progression and rewards

Port: 8008 (configurable via PORT env variable)
"""

import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv

from shared.exception_handlers import register_exception_handlers
from services.monetization.routes.routes import router
from services.monetization.config.db import init_db, close_db

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for the FastAPI app
    
    Startup:
    - Initialize MongoDB connection for Beanie ODM
    - Verify Google Play API credentials
    
    Shutdown:
    - Close database connections gracefully
    """
    print("🚀 Monetization service starting up...")
    
    # Initialize MongoDB connection
    await init_db()
    print("✅ MongoDB connected")
    
    # Verify Google Play credentials exist
    google_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not google_creds:
        print("⚠️  WARNING: GOOGLE_APPLICATION_CREDENTIALS not set")
        print("   IAP validation will fail without Google Play credentials")
    else:
        print(f"✅ Google Play credentials loaded from: {google_creds}")
    
    yield
    
    print("🛑 Monetization service shutting down...")
    await close_db()
    print("✅ Database connections closed")


app = FastAPI(
    title="WordWars AI - Monetization Service",
    version="1.0.0",
    lifespan=lifespan
)

# Register routes
app.include_router(router)

# Register global exception handlers
register_exception_handlers(app, "Monetization Service")


@app.get("/")
async def root():
    return {
        "service": "monetization",
        "status": "healthy",
        "endpoints": {
            "purchase_validation": "/api/purchase/validate",
            "inventory": "/api/inventory/{user_id}",
            "battle_pass": "/api/battlepass/{user_id}",
        }
    }


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "monetization"}


PORT = int(os.getenv("PORT", 8008))

if __name__ == "__main__":
    print(f"⚡ Monetization service booting on port {PORT}...")
    uvicorn.run(
        "services.monetization.main:app",
        host="0.0.0.0",
        port=PORT,
        reload=True
    )
