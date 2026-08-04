import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

from services.auth.config.db import connect_db, disconnect_db
from services.auth.config.firebase import init_firebase
from services.auth.routes.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_firebase()
    await connect_db()
    yield
    await disconnect_db()


app = FastAPI(title="WordWars AI - Auth Service", version="1.0.0", lifespan=lifespan)

app.include_router(router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "auth"}


PORT = int(os.getenv("PORT", 8001))

if __name__ == "__main__":
    print(f"🚀 Auth service booting on port {PORT}...")
    uvicorn.run("services.auth.main:app", host="0.0.0.0", port=PORT, reload=True)
