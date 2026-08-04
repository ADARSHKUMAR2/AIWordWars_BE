import pytest
from services.game_logic.controllers.puzzle_controller import (
    validate_answer,
    calculate_score
)

def test_validate_answer_exact_match():
    assert validate_answer("MAGNET", "MAGNET") == True

def test_validate_answer_case_insensitive():
    assert validate_answer("MAGNET", "magnet") == True
    assert validate_answer("magnet", "MAGNET") == True
    assert validate_answer("MagNet", "mAGnET") == True

def test_validate_answer_with_spaces():
    assert validate_answer("MAGNET", " MAGNET ") == True

def test_validate_answer_incorrect():
    assert validate_answer("MAGNET", "TARGET") == False
    assert validate_answer("MAGNET", "MAG") == False

def test_calculate_score_incorrect_answer():
    # Incorrect answers always yield 0 points
    assert calculate_score(difficulty=5, time_taken=10.0, correct=False) == 0

def test_calculate_score_base_points():
    # difficulty * 10
    assert calculate_score(difficulty=1, time_taken=50.0, correct=True) == 10
    assert calculate_score(difficulty=5, time_taken=50.0, correct=True) == 50
    assert calculate_score(difficulty=10, time_taken=50.0, correct=True) == 100

def test_calculate_score_time_bonus():
    # Base score (5*10=50) + Time bonus (50-10=40) = 90
    assert calculate_score(difficulty=5, time_taken=10.0, correct=True) == 90
    
    # Very fast: Base (50) + Time (50-2=48) = 98
    assert calculate_score(difficulty=5, time_taken=2.0, correct=True) == 98
    
    # Very slow (>50s): No time bonus, just base score (50)
    assert calculate_score(difficulty=5, time_taken=60.0, correct=True) == 50
