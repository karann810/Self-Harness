from src.core import clamp

def test_below():
    assert clamp(-2, 0, 5) == 0

def test_above():
    assert clamp(9, 0, 5) == 5

def test_in_range():
    assert clamp(3, 0, 5) == 3
