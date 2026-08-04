import os
import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="WordWars AI - API Gateway")


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "gateway"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
