import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from shared.exception_handlers import register_exception_handlers
from services.multiplayer_session.routes.routes import router
from services.game_logic.config.db import connect_db, disconnect_db

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Multiplayer Session Service starting up...")
    await connect_db()
    yield
    print("🛑 Multiplayer Session Service shutting down...")
    await disconnect_db()

app = FastAPI(
    title="WordWars AI - Multiplayer Session Service",
    version="1.0.0",
    lifespan=lifespan,
)

# Crucial: Allow all origins, specifically for WebSockets
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
register_exception_handlers(app, "Multiplayer Session Service")

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "multiplayer_session"}

PORT = int(os.getenv("PORT", 8007))

if __name__ == "__main__":
    print(f"⚡ Multiplayer Session service booting on port {PORT}...")
    uvicorn.run("services.multiplayer_session.main:app", host="0.0.0.0", port=PORT, reload=True)
