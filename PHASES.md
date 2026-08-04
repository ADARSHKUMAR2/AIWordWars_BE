### WordWars AI: Phase-wise Distribution Document

This document outlines the development and testing plan in discrete phases.

---

**Phase 0: Project Scaffolding & Foundation**

*   **Objective:** Set up the development environment, source control, and the basic structure for all microservices and the Unity client.
*   **Backend Deliverables:**
    *   Initialize Git repositories for each microservice (`user-service`, `game-logic-service`, etc.).
    *   Set up a `docker-compose.yml` for a unified local development environment.
    *   Create the basic FastAPI application structure for the API Gateway and other services.
    *   Establish database schemas for initial services (e.g., `users` table).
*   **Frontend Deliverables:**
    *   Create a new Unity 6 project.
    *   Set up the basic folder structure and import essential assets (TextMeshPro, DOTween).
    *   Establish a Git repository for the Unity client.
*   **Testing Goal:** Developers can run the entire backend stack with a single command (`docker-compose up`). The Unity project opens without errors.

---

### **Project Folder Structure (Polyrepo Approach)**

This project uses a **polyrepo** structure—two separate repositories for the frontend and backend. This is the recommended approach.

1.  **Backend Repository (`AIWordWars_BE`):** A lightweight repository containing all Python microservices.
2.  **Frontend Repository (`AIWordWars_Unity_FE`):** A separate, dedicated repository for the Unity project, using Git LFS for large assets.

You must add **both folders** to your VS Code workspace for me to have full access.

**1. Backend Structure (`/Users/adarsh/AIWordWars_BE`)**
```
/AIWordWars_BE/
|
├── 🐳 docker-compose.yml
|
└── 📁 services/
    |
    ├── 👤 user-service/
    |   ├── Dockerfile
    |   ├── requirements.txt
    |   └── app/
    |       ├── __init__.py
    |       ├── main.py
    |       ├── core/
    |       ├── models/
    |       └── api/
    |
    ├── 🧠 game-logic-service/
    |   └── ... (similar structure)
    |
    ├── 🤖 ai-word-generator-service/
    |   └── ... (similar structure)
    |
    ├── 🏆 leaderboard-service/
    |   └── ... (similar structure)
    |
    └──  GATEWAY api-gateway/
        └── ... (similar structure)
```

**2. Frontend Structure (`/Users/adarsh/AIWordWars_Unity_FE`)**
```
/AIWordWars_Unity_FE/
|
├── Assets/
|   ├── Scenes/
|   ├── Scripts/
|   |   └── ApiService.cs
|   └── ...
|
├── Packages/
|
└── ProjectSettings/
```

---

**Phase 1: Core Single-Player Loop & User Authentication**

*   **Objective:** Implement the absolute minimum required for a player to register, log in, and play a single, hardcoded word puzzle.
*   **Backend Deliverables:**
    *   **`user-service`**: Implement user registration (username/password) and login, issuing JWTs.
    *   **`api-gateway`**: Route `/auth` and `/game` requests.
    *   **`game-logic-service`**: Create an endpoint that returns a hardcoded scrambled word (e.g., `N G A E M T`). Create another endpoint to verify a submitted answer (e.g., check if it equals `MAGNET`).
    *   **Database**: `users` table in PostgreSQL is functional.
*   **Frontend Deliverables:**
    *   Create UI scenes for Login and Registration.
    *   Create the main Game scene: display scrambled letters, an input field for the answer, and a submit button.
    *   Implement C# logic to communicate with the backend: authenticate the user and fetch the puzzle/submit the answer.
*   **Testing Goal:** A user can create an account, log in, see "N G A E M T", type "MAGNET", and see a "Correct!" message.

---

**Phase 2: The "AI" Word Generator**

*   **Objective:** Replace the hardcoded puzzle with a dynamic, AI-powered word generator and introduce adaptive difficulty.
*   **Backend Deliverables:**
    *   **`ai-word-generator-service`**:
        *   Integrate with OpenAI/Gemini API.
        *   Create a LangGraph agent that generates a word and its scramble (Simple Mode).
        *   Implement basic adaptive difficulty: track player solution speed in Redis. If consistently fast, increase word complexity; if slow, decrease it.
    *   **`game-logic-service`**: Call the `ai-word-generator-service` instead of using a hardcoded word.
*   **Frontend Deliverables:**
    *   No major UI changes. The game should now feel dynamic, with a new word appearing each time.
*   **Testing Goal:** The game now presents endless, varied puzzles. The difficulty should noticeably adjust based on the player's performance over 5-10 games.

---

**Phase 3: Expanding Single-Player Modes**

*   **Objective:** Build out the primary single-player game modes that leverage the core mechanics.
*   **Backend Deliverables:**
    *   **`ai-word-generator-service`**: Add logic for Category Mode (accepts a category, generates a relevant word).
    *   **`game-logic-service`**:
        *   Add state management for Time Attack (60-second timer, combo tracking).
        *   Add state management for Survival Mode (track hearts).
*   **Frontend Deliverables:**
    *   Create a mode selection screen.
    *   Update the Game scene UI to handle different states: a timer for Time Attack, a heart display for Survival, and a category display.
*   **Testing Goal:** Users can successfully play a full session of Time Attack, Category Mode, and Survival Mode.

---

**Phase 4: Progression, Leaderboards & Daily Challenge**

*   **Objective:** Introduce systems that encourage long-term player engagement.
*   **Backend Deliverables:**
    *   **`user-service`**: Add XP, level, and coin data to the user profile.
    *   **`game-logic-service`**: Award coins and XP for winning games.
    *   **`leaderboard-service`**:
        *   Integrate with Unity Gaming Services Leaderboards (or chosen provider).
        *   Create endpoints to submit scores and retrieve leaderboard data (Global, Weekly, etc.).
    *   **`daily-challenge-service`** (New Service): A cron job or scheduled task that generates a single puzzle for the day and stores it in Redis.
*   **Frontend Deliverables:**
    *   UI to show player level and coin balance.
    *   A dedicated Leaderboards screen.
    *   A Daily Challenge entry point and UI.
*   **Testing Goal:** After a game, coins are awarded. Leaderboards update correctly. Everyone sees the same Daily Challenge.

---

**Phase 5: Real-time 1v1 Multiplayer**

*   **Objective:** Implement the core real-time multiplayer experience.
*   **Backend Deliverables:**
    *   **`matchmaking-service`** (New Service):
        *   Integrate with Photon Fusion (or chosen provider).
        *   Implement "Create Room" and "Join Room" logic.
    *   **`multiplayer-session-service`** (New Service):
        *   Manages the state of a 1v1 match.
        *   Ensures both players receive the same puzzle from `ai-word-generator-service`.
        *   Determines the winner (first to solve) and reports the result to `game-logic-service` to award points/coins.
*   **Frontend Deliverables:**
    *   Multiplayer lobby UI: Create/Join room, invite friend.
    *   Update the Game scene for multiplayer: show opponent's progress (e.g., a simple progress bar), a countdown timer, and a winner/loser screen.
*   **Testing Goal:** Two players can join a private room, play the same puzzle in real-time, and a winner is correctly declared.

---

**Phase 6: Advanced AI Features & Game Modes**

*   **Objective:** Implement the unique AI-driven features that make the game stand out.
*   **Backend Deliverables:**
    *   **`ai-word-generator-service`**:
        *   **AI Hint System**: Endpoint to provide a natural language hint for a given word.
        *   **AI Teacher Mode**: Endpoint to provide a definition/explanation for a word.
        *   **AI Generated Categories**: Logic to accept a custom string (e.g., "Pokemon") and generate words for it.
        *   **AI Phrase Battles**: A new mode to generate and scramble phrases.
*   **Frontend Deliverables:**
    *   Add a hint button to the UI.
    *   Create a post-game "Learn" screen for the AI Teacher Mode.
    *   UI for players to input their own categories.
    *   A new game scene or mode for AI Phrase Battles.
*   **Testing Goal:** All AI features work as described. Phrase battles are functional and fun.

---

**Phase 7: Monetization & Polish**

*   **Objective:** Integrate monetization features and add a final layer of polish.
*   **Backend Deliverables:**
    *   Service integration for IAP validation with App Store/Google Play.
    *   Database schemas for premium items, themes, and battle pass progression.
*   **Frontend Deliverables:**
    *   Implement UI for the in-game shop (Coins, Hints, Remove Ads).
    *   Implement UI for the Battle Pass.
    *   Integrate ad SDKs.
    *   Add themes, avatars, titles, and other cosmetic rewards.
*   **Testing Goal:** A user can make a test purchase. The battle pass progresses correctly. Ads are shown at appropriate times.
