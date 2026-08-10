from shellmancer.agent import clean_model_text


def test_trailing_no_think_marker_is_hidden() -> None:
    assert clean_model_text("Ready /no_think") == "Ready"


def test_trailing_think_marker_is_hidden() -> None:
    assert clean_model_text("Ready /think") == "Ready"


def test_regular_slash_text_is_preserved() -> None:
    text = "Path: /var/log/app"
    assert clean_model_text(text) == text
