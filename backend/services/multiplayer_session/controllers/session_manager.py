import asyncio
import json
import httpx
import os
from typing import Dict, Optional
from fastapi import WebSocket
import uuid

from services.multiplayer_session.models.session import GameSession, PlayerState, SessionStatus
from services.game_logic.models.multiplayer_history import MultiplayerHistory
from shared.redis_client import get_redis_client

# ── In-memory stores ──────────────────────────────────────────────────────────
# sessions: room_code → GameSession
# connections: room_code → {user_id: WebSocket}
sessions: Dict[str, GameSession] = {}
connections: Dict[str, Dict[str, WebSocket]] = {}

# ── External service URLs ─────────────────────────────────────────────────────
AI_SERVICE_URL = os.getenv("AI_WORD_GENERATOR_URL", "http://127.0.0.1:8003")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://127.0.0.1:8001")
LEADERBOARD_SERVICE_URL = os.getenv("LEADERBOARD_SERVICE_URL", "http://127.0.0.1:8005")
GAME_LOGIC_SERVICE_URL = os.getenv("GAME_SERVICE_URL", "http://127.0.0.1:8002")

GAME_TIME_LIMIT = 30  # seconds — both players must solve within this window
TOTAL_QUESTIONS = 10


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
                f"{AUTH_SERVICE_URL}/api/progression/award",
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
                f"{LEADERBOARD_SERVICE_URL}/api/scores",
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

async def _save_match_history(room_code: str, players: list, winner_uid: Optional[str], loser_uid: Optional[str], word: str, difficulty: int, winning_time: Optional[float]):
    """Saves the match result directly to MongoDB."""
    print(f"🔄 Attempting to save match history for room {room_code}. Players: {players}")
    
    if not players:
        print(f"⚠️ No players found in room {room_code}, skipping history save.")
        return
        
    try:
        player1 = players[0] if len(players) > 0 else "unknown_1"
        player2 = players[1] if len(players) > 1 else "unknown_2"
        
        # Create the document and insert it directly into MongoDB
        history = MultiplayerHistory(
            room_code=room_code,
            player1_uid=player1,
            player2_uid=player2,
            winner_uid=winner_uid,
            loser_uid=loser_uid,
            word=word,
            difficulty=difficulty,
            winning_time=winning_time
        )
        await history.insert()
        
        print(f"💾 Match history saved to MongoDB for room {room_code}")
    except Exception as e:
        print(f"⚠️ Failed to save match history: {e}")

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
    - Queries Redis to check if the room is fully formed (both players joined via matchmaking).
    - If the room is 'ready' in Redis, and both players' WebSockets are connected, starts the game.
    """
    # Register the connection
    if room_code not in connections:
        connections[room_code] = {}
    connections[room_code][user_id] = websocket

    print(f"🔌 Player ({user_id}) connected WS for room {room_code}")

    # Tell the player they are waiting
    await send_to_player(room_code, user_id, {
        "type": "waiting",
        "message": "Waiting for your opponent to connect...",
    })

    # Fetch room state from Redis (created by Matchmaking Service)
    redis = await get_redis_client()
    raw_room = await redis.get(f"room:{room_code}")
    
    if not raw_room:
        print(f"⚠️ Room {room_code} not found in Redis!")
        return

    room_data = json.loads(raw_room)
    room_status = room_data.get("status")
    host_uid = room_data.get("host_uid")
    guest_uid = room_data.get("guest_uid")
    difficulty = room_data.get("difficulty", 5)

    # Check if both players' WebSockets have connected
    active_connections = connections.get(room_code, {})
    if host_uid in active_connections and guest_uid in active_connections:
        # Both WebSockets are here! Time to start the game.
        
        # Check if session already exists (maybe we already started it)
        session = sessions.get(room_code)
        
        if session is None:
            print(f"🎮 Both players connected to {room_code}. Fetching puzzle (diff: {difficulty})...")
            puzzle_data = await _fetch_puzzle(difficulty=difficulty)

            session = GameSession(
                room_code=room_code,
                puzzle_id=str(uuid.uuid4()),
                word=puzzle_data["word"],
                scrambled=puzzle_data["scrambled"],
                difficulty=puzzle_data.get("difficulty", difficulty),
                hint=puzzle_data.get("hint"),
                category=puzzle_data.get("category"),
                status=SessionStatus.active,
                total_questions=TOTAL_QUESTIONS,
                players={
                    host_uid: PlayerState(user_id=host_uid),
                    guest_uid: PlayerState(user_id=guest_uid)
                },
            )
            sessions[room_code] = session

            # Broadcast game_start to BOTH players simultaneously
            await broadcast(room_code, _question_payload(session, "game_start"))

            # Start the countdown timer in the background
            asyncio.create_task(_game_timeout(room_code, GAME_TIME_LIMIT))
        elif session.status == SessionStatus.active:
            # Reconnection edge case: Game is already active, send state to reconnecting player
            print(f"🔄 Player {user_id} reconnected to active game {room_code}")
            await send_to_player(room_code, user_id, _question_payload(session, "game_start"))


def _question_payload(session: GameSession, event_type: str) -> dict:
    return {
        "type": event_type,
        "puzzle_id": session.puzzle_id,
        "scrambled": session.scrambled,
        "difficulty": session.difficulty,
        "hint": session.hint,
        "category": session.category,
        "time_limit": GAME_TIME_LIMIT,
        "question_number": session.question_number,
        "total_questions": session.total_questions,
        "scores": {uid: player.score for uid, player in session.players.items()},
        "score_entries": [
            {"user_id": uid, "score": player.score}
            for uid, player in session.players.items()
        ],
        "players": list(session.players.keys()),
    }


async def handle_player_disconnect(room_code: str, user_id: str):
    """
    Called when a player's WebSocket disconnects unexpectedly.
    Notifies the opponent and ends the session.
    """
    connections.get(room_code, {}).pop(user_id, None)

    session = sessions.get(room_code)
    if session and session.status == SessionStatus.active:
        session.status = SessionStatus.finished
        winner_id = next((uid for uid in session.players if uid != user_id), None)
        session.winner_id = winner_id
        session.loser_id = user_id
        await broadcast(room_code, {
            "type": "opponent_disconnected",
            "message": "Your opponent disconnected. You win by default!",
            "winner_id": winner_id,
            "your_result": "win",
        })
        print(f"⚠️ {user_id} disconnected from room {room_code}. Session ended.")


async def handle_answer_submit(room_code: str, user_id: str, answer: str, time_taken: float):
    """Validate a submission and advance or finish the ten-question match."""
    session = sessions.get(room_code)
    if not session or session.status != SessionStatus.active:
        await send_to_player(room_code, user_id, {
            "type": "error",
            "message": "No active game session found.",
        })
        return

    player = session.players.get(user_id)
    if not player or player.solved or session.question_solved_by:
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

    # Correct answer wins this question, not the entire match. The first correct
    # answer locks the question so it cannot score twice.
    player.solved = True
    player.time_taken = time_taken
    player.score += 1
    session.question_solved_by = user_id
    session.question_results.append({"question_number": session.question_number, "winner_id": user_id})
    await broadcast(room_code, {
        "type": "question_result",
        "question_number": session.question_number,
        "winner_id": user_id,
        "correct_word": session.word,
        "scores": {uid: state.score for uid, state in session.players.items()},
        "score_entries": [
            {"user_id": uid, "score": state.score}
            for uid, state in session.players.items()
        ],
    })
    await _advance_question(room_code)


async def _game_timeout(room_code: str, time_limit: int):
    """Advance to the next question when this question's timer expires."""
    await asyncio.sleep(time_limit)

    session = sessions.get(room_code)
    # If session is None or already finished, the game ended naturally. Do nothing!
    if not session or session.status != SessionStatus.active:
        return

    if session.question_solved_by:
        # A player already solved; the timeout should not terminate or skip this round.
        return

    print(f"⏰ Room {room_code}, question {session.question_number} timed out.")
    session.question_results.append({"question_number": session.question_number, "winner_id": None})
    await broadcast(room_code, {
        "type": "question_result",
        "question_number": session.question_number,
        "winner_id": session.question_solved_by,
        "correct_word": session.word,
        "scores": {uid: state.score for uid, state in session.players.items()},
        "score_entries": [
            {"user_id": uid, "score": state.score}
            for uid, state in session.players.items()
        ],
    })
    await _advance_question(room_code)


async def _advance_question(room_code: str):
    session = sessions.get(room_code)
    if not session or session.status != SessionStatus.active:
        return

    if session.question_number >= session.total_questions:
        await _finish_match(room_code)
        return

    try:
        puzzle_data = await _fetch_puzzle(session.difficulty)
    except Exception as exc:
        print(f"⚠️ Failed to fetch next puzzle for {room_code}: {exc}")
        # Do not leave players in a live match with no question.
        await _finish_match(room_code)
        return

    session.question_number += 1
    session.puzzle_id = str(uuid.uuid4())
    session.word = puzzle_data["word"]
    session.scrambled = puzzle_data["scrambled"]
    session.difficulty = puzzle_data.get("difficulty", session.difficulty)
    session.hint = puzzle_data.get("hint")
    session.category = puzzle_data.get("category")
    session.question_solved_by = None
    for player in session.players.values():
        player.solved = False
        player.time_taken = None

    await broadcast(room_code, _question_payload(session, "next_question"))
    asyncio.create_task(_game_timeout(room_code, GAME_TIME_LIMIT))


async def _finish_match(room_code: str):
    session = sessions.get(room_code)
    if not session or session.status != SessionStatus.active:
        return

    ranked = sorted(session.players.values(), key=lambda player: player.score, reverse=True)
    tied = len(ranked) > 1 and ranked[0].score == ranked[1].score
    winner_id = None if tied else (ranked[0].user_id if ranked else None)
    loser_id = next((uid for uid in session.players if uid != winner_id), None) if winner_id else None
    session.winner_id = winner_id
    session.loser_id = loser_id
    session.status = SessionStatus.finished

    if winner_id:
        winner = session.players[winner_id]
        asyncio.create_task(_award_win(winner_id, session.difficulty))
        asyncio.create_task(_submit_leaderboard(winner_id, winner.time_taken or 1, session.difficulty))

    players_list = list(session.players.keys())
    await _save_match_history(
        room_code, players_list, winner_id, loser_id,
        f"10-question match; scores: {', '.join(f'{uid}={player.score}' for uid, player in session.players.items())}",
        session.difficulty, None,
    )

    # Send personalised final result to each player.
    for uid in session.players:
        await send_to_player(room_code, uid, {
            "type": "game_over",
            "winner_id": winner_id,
            "loser_id": loser_id,
            "scores": {player_uid: player.score for player_uid, player in session.players.items()},
            "score_entries": [
                {"user_id": player_uid, "score": player.score}
                for player_uid, player in session.players.items()
            ],
            "question_results": session.question_results,
            "your_result": "draw" if tied else ("win" if uid == winner_id else "lose"),
        })
    asyncio.create_task(_cleanup_session(room_code, delay=10))

async def _cleanup_session(room_code: str, delay: int = 30):
    """Remove session and connections from memory after a delay."""
    await asyncio.sleep(delay)
    sessions.pop(room_code, None)
    connections.pop(room_code, None)
    print(f"🧹 Cleaned up room {room_code}")
