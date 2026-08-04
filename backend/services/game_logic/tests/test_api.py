import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from services.game_logic.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "game-logic"}

# Mock the entire controller function instead of the DB
@patch('services.game_logic.routes.routes.create_new_puzzle', new_callable=AsyncMock)
def test_get_new_puzzle_success(mock_create_new_puzzle):
    
    # Use MagicMock instead of a custom class
    from unittest.mock import MagicMock
    mock_puzzle = MagicMock()
    mock_puzzle.puzzle_id = "test-uuid"
    mock_puzzle.scrambled = "NTHYPO"
    mock_puzzle.difficulty = 5
    mock_puzzle.hint = "6-letter word"
    mock_puzzle.mode = "simple"
    mock_puzzle.category = None
        
    mock_create_new_puzzle.return_value = mock_puzzle
    
    response = client.post("/api/puzzle/new", json={"difficulty": 5})
    
    # If this fails, let's print the error!
    if response.status_code == 500:
        print("ERROR DETAILS:", response.json())
        
    assert response.status_code == 200
    data = response.json()
    assert data["puzzle_id"] == "test-uuid"
    assert data["scrambled"] == "NTHYPO"
    assert data["difficulty"] == 5
    assert "word" not in data

def test_get_new_puzzle_invalid_difficulty():
    response = client.post("/api/puzzle/new", json={"difficulty": 11})
    assert response.status_code == 400
    assert "between 1 and 10" in response.json()["detail"]

# Mock the DB retrieval and the session saving
@patch('services.game_logic.routes.routes.Puzzle.find_one', new_callable=AsyncMock)
@patch('services.game_logic.routes.routes.save_game_session', new_callable=AsyncMock)
def test_solve_puzzle_correct(mock_save_session, mock_find_one):
    
    class DummyDbPuzzle:
        puzzle_id = "test-uuid"
        word = "PYTHON"
        difficulty = 5
        mode = "simple"
        
    mock_find_one.return_value = DummyDbPuzzle()
    
    # We must patch Puzzle.puzzle_id during the test to avoid AttributeError
    from services.game_logic.models.puzzle import Puzzle
    with patch.object(Puzzle, 'puzzle_id', "dummy_id", create=True):
        response = client.post("/api/puzzle/solve", json={
            "puzzle_id": "test-uuid",
            "answer": "PYTHON",
            "time_taken": 15.0
        })
    
    assert response.status_code == 200
    data = response.json()
    assert data["correct"] == True
    # Base (50) + Time Bonus (50-15 = 35) = 85
    assert data["score"] == 85
    assert data["correct_answer"] is None
    # Verify we tried to save the session
    mock_save_session.assert_called_once()

@patch('services.game_logic.routes.routes.Puzzle.find_one', new_callable=AsyncMock)
@patch('services.game_logic.routes.routes.save_game_session', new_callable=AsyncMock)
def test_solve_puzzle_incorrect(mock_save_session, mock_find_one):
    
    class DummyDbPuzzle:
        puzzle_id = "test-uuid"
        word = "PYTHON"
        difficulty = 5
        mode = "simple"
        
    mock_find_one.return_value = DummyDbPuzzle()
    
    from services.game_logic.models.puzzle import Puzzle
    with patch.object(Puzzle, 'puzzle_id', "dummy_id", create=True):
        response = client.post("/api/puzzle/solve", json={
            "puzzle_id": "test-uuid",
            "answer": "WRONG",
            "time_taken": 10.0
        })
    
    assert response.status_code == 200
    data = response.json()
    assert data["correct"] == False
    assert data["score"] == 0
    assert data["correct_answer"] == "PYTHON"

@patch('services.game_logic.routes.routes.Puzzle.find_one', new_callable=AsyncMock)
def test_solve_puzzle_not_found(mock_find_one):
    mock_find_one.return_value = None
    
    from services.game_logic.models.puzzle import Puzzle
    with patch.object(Puzzle, 'puzzle_id', "dummy_id", create=True):
        response = client.post("/api/puzzle/solve", json={
            "puzzle_id": "invalid-uuid",
            "answer": "PYTHON",
            "time_taken": 10.0
        })
    
    assert response.status_code == 404
