from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import json

from services.multiplayer_session.controllers.session_manager import (
    handle_player_connect,
    handle_player_disconnect,
    handle_answer_submit,
)

router = APIRouter()


@router.websocket("/ws/{room_code}")
async def multiplayer_websocket(
    websocket: WebSocket,
    room_code: str,
    user_id: str = Query(..., description="Firebase UID of the connecting player"),
):
    """
    WebSocket endpoint for a multiplayer game session.

    Connect URL: ws://localhost:8007/ws/{ROOM_CODE}?user_id={FIREBASE_UID}

    Messages the CLIENT sends to SERVER (JSON):
      { "type": "submit_answer", "answer": "PUZZLE", "time_taken": 23.4 }
      { "type": "ping" }  ← optional heartbeat

    Messages the SERVER sends to CLIENT (JSON):
      { "type": "waiting", "message": "..." }
      { "type": "game_start", "puzzle_id": "...", "scrambled": "...", ... }
      { "type": "answer_result", "correct": false, "message": "..." }
      { "type": "player_solved", "user_id": "...", "time_taken": 23.4 }
      { "type": "game_over", "winner_id": "...", "your_result": "win|lose|draw", ... }
      { "type": "opponent_disconnected", "message": "..." }
      { "type": "error", "message": "..." }
    """
    await websocket.accept()
    room_code = room_code.upper()
    print(f"🔌 {user_id} connected to room {room_code}")

    try:
        await handle_player_connect(room_code, user_id, websocket)

        # Keep listening for messages from this player
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type")

            if msg_type == "submit_answer":
                answer = data.get("answer", "")
                time_taken = float(data.get("time_taken", 0))
                await handle_answer_submit(room_code, user_id, answer, time_taken)

            elif msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        print(f"🔌 {user_id} disconnected from room {room_code}")
        await handle_player_disconnect(room_code, user_id)
