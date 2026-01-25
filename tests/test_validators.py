from app.services.script import count_words, validate_voiceover


def test_count_words_ru():
    text = "Это короткий тест на подсчет слов"
    assert count_words(text) == 6


def test_validate_voiceover_bounds():
    text = "слово " * 70
    assert validate_voiceover(text)
    text = "слово " * 69
    assert not validate_voiceover(text)
