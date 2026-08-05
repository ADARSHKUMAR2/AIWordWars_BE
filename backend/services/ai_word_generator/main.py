import os
import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv
from shared.exception_handlers import register_exception_handlers

load_dotenv()

from services.ai_word_generator.routes.routes import router

app = FastAPI(title="WordWars AI - AI Word Generator", version="1.0.0")

app.include_router(router)

register_exception_handlers(app, "AI Word Generator Service")

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ai-word-generator"}


PORT = int(os.getenv("PORT", 8003))

if __name__ == "__main__":
    print(f"🚀 AI Word Generator booting on port {PORT}...")
    uvicorn.run("services.ai_word_generator.main:app", host="0.0.0.0", port=PORT, reload=True)
