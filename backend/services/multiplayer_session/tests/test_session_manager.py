import json
from unittest.mock import AsyncMock, patch

import pytest

from services.multiplayer_session.controllers import session_manager
from services.multiplayer_session.models.session import GameSession, PlayerState, SessionStatus


class FakeWebSocket:
    def __init__(self):
        self.messages = []

    async def send_text(self, message):
        self.messages.append(json.loads(message))


@pytest.fixture(autouse=True)
def clear_session_stores():
    session_manager.sessions.clear()
    session_manager.connections.clear()
    yield
    session_manager.sessions.clear()
    session_manager.connections.clear()


def make_session(question_number=1, total_questions=10):
    return GameSession(
        room_code="ROOM1",
        puzzle_id="puzzle-1",
        word="APPLE",
        scrambled="PAPLE",
        difficulty=5,
        status=SessionStatus.active,
        question_number=question_number,
        total_questions=total_questions,
        players={"alice": PlayerState(user_id="alice"), "bob": PlayerState(user_id="bob")},
    )


@pytest.mark.asyncio
async def test_correct_answer_awards_question_point_and_loads_next_question():
    session = make_session()
    session_manager.sessions["ROOM1"] = session
    alice_ws, bob_ws = FakeWebSocket(), FakeWebSocket()
    session_manager.connections["ROOM1"] = {"alice": alice_ws, "bob": bob_ws}
    puzzle = {
        "word": "GRAPE",
        "scrambled": "PAGER",
        "difficulty": 5,
        "hint": "fruit",
        "category": "food",
    }

    with patch.object(session_manager, "_fetch_puzzle", new=AsyncMock(return_value=puzzle)), \
         patch.object(session_manager, "_game_timeout", new=AsyncMock()):
        await session_manager.handle_answer_submit("ROOM1", "alice", "apple", 8.2)

    assert session.players["alice"].score == 1
    assert session.players["bob"].score == 0
    assert session.status == SessionStatus.active
    assert session.question_number == 2
    assert session.word == "GRAPE"
    assert session.category == "food"
    assert session.question_solved_by is None
    assert alice_ws.messages[-1]["type"] == "next_question"
    assert alice_ws.messages[-1]["question_number"] == 2
    assert alice_ws.messages[-1]["category"] == "food"
    assert bob_ws.messages[-2]["type"] == "question_result"


@pytest.mark.asyncio
async def test_match_ends_after_last_question_with_score_winner():
    session = make_session(question_number=10)
    session.players["alice"].score = 4
    session.players["bob"].score = 6
    session_manager.sessions["ROOM1"] = session
    alice_ws, bob_ws = FakeWebSocket(), FakeWebSocket()
    session_manager.connections["ROOM1"] = {"alice": alice_ws, "bob": bob_ws}

    with patch.object(session_manager, "_finish_match", wraps=session_manager._finish_match) as finish, \
         patch.object(session_manager, "_save_match_history", new=AsyncMock()), \
         patch.object(session_manager, "_award_win"), \
         patch.object(session_manager, "_submit_leaderboard"), \
         patch.object(session_manager, "_cleanup_session"):
        await session_manager.handle_answer_submit("ROOM1", "alice", "APPLE", 3.0)

    assert finish.await_count == 1
    assert session.status == SessionStatus.finished
    assert session.winner_id == "bob"
    assert alice_ws.messages[-1]["type"] == "game_over"
    assert alice_ws.messages[-1]["your_result"] == "lose"
    assert bob_ws.messages[-1]["your_result"] == "win"


@pytest.mark.asyncio
async def test_timed_out_question_advances_and_does_not_finish_match():
    session = make_session()
    session_manager.sessions["ROOM1"] = session
    alice_ws = FakeWebSocket()
    session_manager.connections["ROOM1"] = {"alice": alice_ws}

    with patch.object(session_manager.asyncio, "sleep", new=AsyncMock()), \
         patch.object(session_manager, "_advance_question", new=AsyncMock()) as advance:
        await session_manager._game_timeout("ROOM1", 120)

    advance.assert_awaited_once_with("ROOM1")
    assert session.status == SessionStatus.active
