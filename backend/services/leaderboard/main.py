import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv

from shared.exception_handlers import register_exception_handlers
from services.leaderboard.config.db import connect_db, disconnect_db
from services.leaderboard.routes.routes import router

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Leaderboard Service starting up...")
    await connect_db()
    yield
    print("🛑 Leaderboard Service shutting down...")
    await disconnect_db()


app = FastAPI(
    title="WordWars AI - Leaderboard Service",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(router)

register_exception_handlers(app, "Leaderboard Service")


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "leaderboard"}


PORT = int(os.getenv("PORT", 8005))

if __name__ == "__main__":
    print(f"🏆 Leaderboard service booting on port {PORT}...")
    uvicorn.run("services.leaderboard.main:app", host="0.0.0.0", port=PORT, reload=True)
