from src.core import slugify

def test_punctuation_case():
    assert slugify("Hello, World!") == "hello-world"

def test_whitespace():
    assert slugify("  keep   it simple  ") == "keep-it-simple"
