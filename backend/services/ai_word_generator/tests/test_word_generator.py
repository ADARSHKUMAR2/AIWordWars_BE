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

@patch('services.ai_word_generator.controllers.word_generator.create_word_generator_graph')
def test_generate_word_uses_local_fallback_when_ai_fails(mock_graph):
    mock_graph.return_value.invoke.side_effect = RuntimeError("AI provider unavailable")

    result = generate_word(difficulty=5, category="technology")

    assert result["word"] in {"APPLE", "BRIDGE", "PLANET", "GARDEN", "PYTHON", "STREAM"}
    assert len(result["word"]) in (5, 6)
    assert sorted(result["scrambled"]) == sorted(result["word"])
    assert result["hint"] == f"{len(result['word'])}-letter word"
    mock_graph.return_value.invoke.assert_called_once()


@patch('services.ai_word_generator.controllers.word_generator.create_word_generator_graph')
def test_generate_word_fallback_matches_difficulty(mock_graph):
    mock_graph.return_value.invoke.side_effect = RuntimeError("AI provider unavailable")

    result = generate_word(difficulty=10)

    assert result["word"] in {"ELEPHANT", "NOTEBOOK", "MOUNTAIN", "TREASURE", "LANGUAGE", "KEYBOARD"}
    assert len(result["word"]) >= 7
    assert result["difficulty"] == 10
