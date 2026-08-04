from fastapi.testclient import TestClient
from services.ai_word_generator.main import app
from unittest.mock import patch

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ai-word-generator"}

@patch('services.ai_word_generator.controllers.word_generator.get_gemini_client')
def test_generate_endpoint_valid(mock_gemini):
    # Mock the Gemini API response
    mock_gemini.return_value.invoke.return_value.content = "HELLO"
    
    response = client.post("/api/generate", json={"difficulty": 5})
    
    assert response.status_code == 200
    data = response.json()
    assert "word" in data
    assert "scrambled" in data
    assert "difficulty" in data
    assert "hint" in data
    assert data["difficulty"] == 5

def test_generate_endpoint_invalid_difficulty_low():
    response = client.post("/api/generate", json={"difficulty": 0})
    assert response.status_code == 400

def test_generate_endpoint_invalid_difficulty_high():
    response = client.post("/api/generate", json={"difficulty": 11})
    assert response.status_code == 400
