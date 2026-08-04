from unittest.mock import Mock, patch
from services.ai_word_generator.controllers.word_generator import generate_word

@patch('services.ai_word_generator.controllers.word_generator.get_gemini_client')
def test_generate_word_easy_difficulty(mock_gemini):
    # Mock the Gemini response
    mock_response = Mock()
    mock_response.content = "CAT"
    mock_gemini.return_value.invoke.return_value = mock_response
    
    result = generate_word(difficulty=1)
    
    assert result["word"] == "CAT"
    assert result["difficulty"] == 1
    assert len(result["word"]) == 3
    assert result["scrambled"] != result["word"]  # Should be scrambled
    assert "hint" in result

@patch('services.ai_word_generator.controllers.word_generator.get_gemini_client')
def test_generate_word_medium_difficulty(mock_gemini):
    mock_response = Mock()
    mock_response.content = "PYTHON"
    mock_gemini.return_value.invoke.return_value = mock_response
    
    result = generate_word(difficulty=5)
    
    assert result["word"] == "PYTHON"
    assert result["difficulty"] == 5
    assert len(result["word"]) == 6

@patch('services.ai_word_generator.controllers.word_generator.get_gemini_client')
def test_generate_word_hard_difficulty(mock_gemini):
    mock_response = Mock()
    mock_response.content = "ALGORITHM"
    mock_gemini.return_value.invoke.return_value = mock_response
    
    result = generate_word(difficulty=10)
    
    assert result["word"] == "ALGORITHM"
    assert result["difficulty"] == 10
    assert len(result["word"]) >= 7
