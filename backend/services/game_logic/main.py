import os
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

from services.game_logic.config.db import connect_db, disconnect_db
from services.game_logic.routes.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_db()
    yield
    # Shutdown
    await disconnect_db()


app = FastAPI(
    title="WordWars AI - Game Logic",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "game-logic"}


PORT = int(os.getenv("PORT", 8004))

if __name__ == "__main__":
    print(f"🎮 Game Logic Service booting on port {PORT}...")
    uvicorn.run("services.game_logic.main:app", host="0.0.0.0", port=PORT, reload=True)
