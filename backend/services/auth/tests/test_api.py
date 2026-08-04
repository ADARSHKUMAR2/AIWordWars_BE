import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from services.auth.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "auth"}

@patch('services.auth.routes.routes.login_or_register', new_callable=AsyncMock)
def test_login_success(mock_login_or_register):
    class DummyUser:
        firebase_uid = "test-uid-123"
        display_name = "Test User"
        email = "test@example.com"
        photo_url = None
        coins = 100
        xp = 500
        level = 3
    
    mock_login_or_register.return_value = DummyUser()
    
    response = client.post("/api/login", json={"id_token": "valid_token"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["firebase_uid"] == "test-uid-123"
    assert data["coins"] == 100
    assert data["display_name"] == "Test User"

@patch('services.auth.routes.routes.login_or_register', new_callable=AsyncMock)
def test_login_invalid_token(mock_login_or_register):
    mock_login_or_register.side_effect = ValueError("Invalid Firebase token")
    
    response = client.post("/api/login", json={"id_token": "invalid_token"})
    
    assert response.status_code == 401
    assert "Invalid Firebase token" in response.json()["detail"]

@patch('services.auth.routes.routes.get_user_by_uid', new_callable=AsyncMock)
def test_get_me_success(mock_get_user):
    class DummyUser:
        firebase_uid = "test-uid-123"
        display_name = "Test User"
        email = "test@example.com"
        photo_url = None
        coins = 100
        xp = 500
        level = 3
        
    mock_get_user.return_value = DummyUser()
    
    response = client.get("/api/me/test-uid-123")
    
    assert response.status_code == 200
    data = response.json()
    assert data["firebase_uid"] == "test-uid-123"
    assert data["display_name"] == "Test User"

@patch('services.auth.routes.routes.get_user_by_uid', new_callable=AsyncMock)
def test_get_me_user_not_found(mock_get_user):
    mock_get_user.return_value = None
    
    response = client.get("/api/me/invalid-uid")
    
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]
