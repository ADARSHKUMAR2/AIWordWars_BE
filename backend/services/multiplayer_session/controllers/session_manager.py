import asyncio
import json
import httpx
import os
from typing import Dict, Optional
from fastapi import WebSocket

from services.multiplayer_session.models.session import GameSession, PlayerState, SessionStatus

# ── In-memory stores ──────────────────────────────────────────────────────────
# sessions: room_code → GameSession
# connections: room_code → {user_id: WebSocket}
sessions: Dict[str, GameSession] = {}
connections: Dict[str, Dict[str, WebSocket]] = {}

# ── External service URLs ─────────────────────────────────────────────────────
AI_SERVICE_URL = os.getenv("AI_WORD_GENERATOR_URL", "http://127.0.0.1:8003")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://127.0.0.1:8001")
LEADERBOARD_SERVICE_URL = os.getenv("LEADERBOARD_SERVICE_URL", "http://127.0.0.1:8005")

GAME_TIME_LIMIT = 120  # seconds — both players must solve within this window


async def _fetch_puzzle(difficulty: int) -> dict:
    """Calls the AI Word Generator service to get a puzzle for this match."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{AI_SERVICE_URL}/api/generate",
            json={"difficulty": difficulty, "mode": "simple"},
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.json()


async def _award_win(winner_uid: str, difficulty: int):
    """Awards XP and coins to the winner via the auth service. Non-fatal if it fails."""
    xp = difficulty * 15       # e.g., difficulty 5 → 75 XP
    coins = difficulty * 5     # e.g., difficulty 5 → 25 coins
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{AUTH_SERVICE_URL}/auth/api/progression/award",
                json={"firebase_uid": winner_uid, "xp_earned": xp, "coins_earned": coins},
                timeout=10.0,
            )
        print(f"🏆 Awarded {xp} XP + {coins} coins to winner {winner_uid}")
    except Exception as e:
        print(f"⚠️ Failed to award progression to {winner_uid}: {e}")


async def _submit_leaderboard(winner_uid: str, time_taken: float, difficulty: int):
    """Submits the winner's score to the leaderboard. Non-fatal if it fails."""
    score = int((difficulty * 100) / max(time_taken, 1))
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{LEADERBOARD_SERVICE_URL}/leaderboard/api/scores",
                json={
                    "firebase_uid": winner_uid,
                    "board_id": "multiplayer",
                    "mode": "multiplayer_1v1",
                    "score": score,
                },
                timeout=10.0,
            )
        print(f"📊 Leaderboard score {score} submitted for {winner_uid}")
    except Exception as e:
        print(f"⚠️ Failed to submit leaderboard score: {e}")


async def broadcast(room_code: str, message: dict):
    """Send a JSON message to ALL connected players in a room."""
    room_connections = connections.get(room_code, {})
    payload = json.dumps(message)
    disconnected = []

    for uid, ws in room_connections.items():
        try:
            await ws.send_text(payload)
        except Exception:
            disconnected.append(uid)

    # Clean up disconnected players
    for uid in disconnected:
        room_connections.pop(uid, None)


async def send_to_player(room_code: str, user_id: str, message: dict):
    """Send a JSON message to ONE specific player."""
    ws = connections.get(room_code, {}).get(user_id)
    if ws:
        try:
            await ws.send_text(json.dumps(message))
        except Exception:
            pass


async def handle_player_connect(room_code: str, user_id: str, websocket: WebSocket):
    """
    Called when a player's WebSocket connects.
    - Stores the connection
    - If both players are now connected, fetches a puzzle and starts the game
    """
    # Register the connection
    if room_code not in connections:
        connections[room_code] = {}
    connections[room_code][user_id] = websocket

    # Create or update session
    if room_code not in sessions:
        sessions[room_code] = None  # Placeholder while we fetch puzzle

    session = sessions.get(room_code)

    if session is None:
        # First player connected — fetch puzzle and create session
        print(f"🎮 Player 1 ({user_id}) connected to room {room_code}. Fetching puzzle...")
        await send_to_player(room_code, user_id, {
            "type": "waiting",
            "message": "Waiting for your opponent to connect...",
        })

        # Fetch puzzle now so it's ready when player 2 joins
        puzzle_data = await _fetch_puzzle(difficulty=5)

        session = GameSession(
            room_code=room_code,
            puzzle_id=puzzle_data["puzzle_id"],
            word=puzzle_data["word"],
            scrambled=puzzle_data["scrambled"],
            difficulty=puzzle_data.get("difficulty", 5),
            hint=puzzle_data.get("hint"),
            status=SessionStatus.waiting,
            players={user_id: PlayerState(user_id=user_id)},
        )
        sessions[room_code] = session

    else:
        # Second player connected — add them and start the game!
        print(f"🎮 Player 2 ({user_id}) connected to room {room_code}. Starting game!")
        session.players[user_id] = PlayerState(user_id=user_id)
        session.status = SessionStatus.active
        sessions[room_code] = session

        # Broadcast game_start to BOTH players simultaneously
        await broadcast(room_code, {
            "type": "game_start",
            "puzzle_id": session.puzzle_id,
            "scrambled": session.scrambled,
            "difficulty": session.difficulty,
            "hint": session.hint,
            "time_limit": GAME_TIME_LIMIT,
            "players": list(session.players.keys()),
        })

        # Start the countdown timer in the background
        asyncio.create_task(_game_timeout(room_code, GAME_TIME_LIMIT))


async def handle_player_disconnect(room_code: str, user_id: str):
    """
    Called when a player's WebSocket disconnects unexpectedly.
    Notifies the opponent and ends the session.
    """
    connections.get(room_code, {}).pop(user_id, None)

    session = sessions.get(room_code)
    if session and session.status == SessionStatus.active:
        session.status = SessionStatus.finished
        await broadcast(room_code, {
            "type": "opponent_disconnected",
            "message": "Your opponent disconnected. You win by default!",
        })
        print(f"⚠️ {user_id} disconnected from room {room_code}. Session ended.")


async def handle_answer_submit(room_code: str, user_id: str, answer: str, time_taken: float):
    """
    Called when a player submits an answer.
    - Validates it server-side
    - If correct, declares them the winner
    - If wrong, tells only them it was incorrect
    """
    session = sessions.get(room_code)
    if not session or session.status != SessionStatus.active:
        await send_to_player(room_code, user_id, {
            "type": "error",
            "message": "No active game session found.",
        })
        return

    player = session.players.get(user_id)
    if not player or player.solved:
        return  # Already solved or unknown player

    is_correct = answer.strip().upper() == session.word.upper()

    if not is_correct:
        # Only tell this player their answer was wrong
        await send_to_player(room_code, user_id, {
            "type": "answer_result",
            "correct": False,
            "message": "Incorrect! Keep trying.",
        })
        return

    # ── Correct answer! ───────────────────────────────────────────────────────
    player.solved = True
    player.time_taken = time_taken

    # Find the other player (the loser)
    other_uids = [uid for uid in session.players if uid != user_id]
    loser_id = other_uids[0] if other_uids else None

    session.winner_id = user_id
    session.loser_id = loser_id
    session.status = SessionStatus.finished

    # Broadcast game_over to BOTH players with personalised result
    room_conns = connections.get(room_code, {})
    for uid, ws in room_conns.items():
        your_result = "win" if uid == user_id else "lose"
        try:
            await ws.send_text(json.dumps({
                "type": "game_over",
                "winner_id": user_id,
                "loser_id": loser_id,
                "correct_word": session.word,
                "winning_time": time_taken,
                "your_result": your_result,
            }))
        except Exception:
            pass

    print(f"🏆 {user_id} won room {room_code} in {time_taken}s!")

    # Award XP/coins and update leaderboard (non-blocking background tasks)
    asyncio.create_task(_award_win(user_id, session.difficulty))
    asyncio.create_task(_submit_leaderboard(user_id, time_taken, session.difficulty))

    # Clean up session after a delay
    asyncio.create_task(_cleanup_session(room_code, delay=30))


async def _game_timeout(room_code: str, time_limit: int):
    """
    Background task: if neither player solves within time_limit seconds,
    declare it a draw.
    """
    await asyncio.sleep(time_limit)

    session = sessions.get(room_code)
    if session and session.status == SessionStatus.active:
        session.status = SessionStatus.finished
        await broadcast(room_code, {
            "type": "game_over",
            "winner_id": None,
            "loser_id": None,
            "correct_word": session.word,
            "winning_time": None,
            "your_result": "draw",
        })
        print(f"⏰ Room {room_code} timed out — no winner.")
        asyncio.create_task(_cleanup_session(room_code, delay=10))


async def _cleanup_session(room_code: str, delay: int = 30):
    """Remove session and connections from memory after a delay."""
    await asyncio.sleep(delay)
    sessions.pop(room_code, None)
    connections.pop(room_code, None)
    print(f"🧹 Cleaned up room {room_code}")
