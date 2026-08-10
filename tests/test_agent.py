from shellmancer.agent import clean_model_text, is_false_capability_refusal


def test_trailing_no_think_marker_is_hidden() -> None:
    assert clean_model_text("Ready /no_think") == "Ready"


def test_trailing_think_marker_is_hidden() -> None:
    assert clean_model_text("Ready /think") == "Ready"


def test_regular_slash_text_is_preserved() -> None:
    text = "Path: /var/log/app"
    assert clean_model_text(text) == text


def test_false_terminal_capability_refusal_is_detected() -> None:
    assert is_false_capability_refusal(
        "I don't have access to the terminal, so I cannot run that command."
    )


def test_normal_answer_is_not_treated_as_capability_refusal() -> None:
    assert not is_false_capability_refusal("I can help explain how the command works.")
