# AI WordWars - Backend Microservices 🧠⚔️

The backend architecture for AI WordWars, a dynamic, AI-generated word scramble game. Built with a highly scalable, stateless microservices architecture using FastAPI, LangGraph, and Redis.

## 🏗️ Architecture

The backend is composed of several independent microservices behind an API Gateway:

*   **API Gateway (Port 8000):** The main entry point. Intercepts all requests, validates Redis sessions via `Authorization: Bearer <token>`, and proxies requests to internal services while injecting the `X-User-Id` header.
*   **Auth Service (Port 8001):** Handles Firebase token verification, MongoDB user creation, and Redis session generation.
*   **AI Word Generator (Port 8003):** Utilizes **LangGraph** and Google's **Gemini LLM** to dynamically generate word puzzles. It pulls player solve times from Redis to calculate **Adaptive Difficulty** in real-time.
*   **Game Logic Service (Port 8004):** A purely stateless engine that validates answers, calculates scores, tracks combos (Time Attack) and hearts (Survival), and saves the final game session to MongoDB.

## 🛠️ Tech Stack
*   **Framework:** FastAPI (Python 3.12+)
*   **AI Orchestration:** LangGraph & LangChain (Gemini LLM)
*   **Database:** MongoDB (User profiles, Game sessions)
*   **Caching & Sessions:** Redis (Session IDs, Adaptive Difficulty timing lists)
*   **Process Management:** Honcho (Foreman port for running services concurrently)

## 🎮 Game Modes (Stateless Design)
To ensure zero database lag during high-speed gameplay, the Game Logic service relies on a **Stateless Architecture**. Unity tracks the current session state (e.g., current combo, current hearts) and sends it to the backend. The backend calculates the resulting score, determines the next state, and returns it.
1.  **Classic Mode:** Standard solve-and-score.
2.  **Time Attack:** 60-second limit. Faster solves yield higher points and build a Combo Multiplier.
3.  **Survival:** 3 Hearts. Failing to answer within 30 seconds, or answering incorrectly, deducts a heart.

## 🚀 How to Run Locally

1.  **Prerequisites:** 
    *   Python & `uv` package manager installed.
    *   Local Redis server running (`brew services start redis`).
2.  **Install Dependencies:** 
    ```bash
    uv sync
    uv pip install honcho
    ```
3.  **Environment Variables:** Ensure `.env` files are configured in the `gateway` and individual `services/` folders.
4.  **Start All Services:**
    ```bash
    uv run honcho start
    ```
    *This uses the `Procfile` to boot Redis, the Gateway, Auth, Game Logic, and AI services concurrently with color-coded logs.*