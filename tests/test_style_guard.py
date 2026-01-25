from app.services.style_guard import lint_text


def test_banned_pattern_detected():
    issues = lint_text("Это не про скорость, а про привычку")
    assert any("Запрещенная схема" in issue for issue in issues)


def test_long_dash_detected():
    issues = lint_text("Текст — с длинным тире")
    assert any("длинное тире" in issue for issue in issues)
