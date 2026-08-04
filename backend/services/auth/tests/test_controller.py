import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from services.auth.controllers.controller import login_or_register, get_user_by_uid

@pytest.fixture
def mock_decoded_token():
    return {
        "uid": "test-uid-123",
        "email": "test@example.com",
        "name": "Test User",
        "picture": "https://example.com/pic.jpg"
    }

@pytest.mark.asyncio
@patch('services.auth.controllers.controller.firebase_auth.verify_id_token')
@patch('services.auth.models.user.User.find_one', new_callable=AsyncMock)
async def test_login_or_register_existing_user(mock_find_one, mock_verify, mock_decoded_token):
    mock_verify.return_value = mock_decoded_token
    
    # Create mock user with an async save method!
    mock_user = MagicMock()
    mock_user.save = AsyncMock()  # This fixes the await error
    mock_find_one.return_value = mock_user
    
    from services.auth.models.user import User
    with patch.object(User, 'firebase_uid', "dummy_uid", create=True):
        user = await login_or_register("valid_token")
    
    mock_verify.assert_called_once_with("valid_token")
    mock_find_one.assert_called_once()
    mock_user.save.assert_called_once()
    assert user == mock_user

@pytest.mark.asyncio
@patch('services.auth.controllers.controller.firebase_auth.verify_id_token')
@patch('services.auth.controllers.controller.User') # Mock the User class completely
async def test_login_or_register_new_user(mock_user_class, mock_verify, mock_decoded_token):
    mock_verify.return_value = mock_decoded_token
    
    # 1. Mock the class method find_one to return None (user not found)
    mock_user_class.find_one = AsyncMock(return_value=None)
    
    # 2. Setup what happens when User(firebase_uid=...) is called
    mock_user_instance = MagicMock()
    mock_user_instance.insert = AsyncMock() # The insert method must be awaitable
    mock_user_class.return_value = mock_user_instance
    
    # Run the controller
    user = await login_or_register("valid_token")
    
    # Asserts
    mock_verify.assert_called_once_with("valid_token")
    mock_user_class.find_one.assert_called_once()
    mock_user_class.assert_called_once()  # Asserts User(...) was called
    mock_user_instance.insert.assert_called_once()
    assert user == mock_user_instance

@pytest.mark.asyncio
@patch('services.auth.controllers.controller.firebase_auth.verify_id_token')
async def test_login_or_register_invalid_token(mock_verify):
    # Setup mock to raise error
    mock_verify.side_effect = Exception("Invalid token")
    
    # Assert ValueError is raised
    with pytest.raises(ValueError, match="Invalid Firebase token"):
        await login_or_register("invalid_token")

@pytest.mark.asyncio
@patch('services.auth.models.user.User.find_one', new_callable=AsyncMock)
async def test_get_user_by_uid(mock_find_one):
    mock_user = MagicMock()
    mock_find_one.return_value = mock_user
    
    from services.auth.models.user import User
    with patch.object(User, 'firebase_uid', "dummy_uid", create=True):
        user = await get_user_by_uid("test-uid-123")
    
    mock_find_one.assert_called_once()
    assert user == mock_user
