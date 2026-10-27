from src.core import add_numbers

def test_sum():
    assert add_numbers([1, -2, 4]) == 3

def test_empty():
    assert add_numbers([]) == 0
