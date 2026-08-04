import os
import sys
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

# Add the service directory to the path so imports work correctly
sys.path.insert(0, os.path.dirname(__file__))

from config.db import connect_db, disconnect_db
from config.firebase import init_firebase
from routes.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_firebase()
    await connect_db()
    yield
    # Shutdown
    await disconnect_db()


app = FastAPI(title="WordWars AI - Auth Service", lifespan=lifespan)

app.include_router(router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "auth"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
