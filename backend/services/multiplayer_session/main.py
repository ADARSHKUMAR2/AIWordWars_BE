import os
import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv

from shared.exception_handlers import register_exception_handlers
from services.multiplayer_session.routes.routes import router

load_dotenv()

app = FastAPI(
    title="WordWars AI - Multiplayer Session Service",
    version="1.0.0",
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
