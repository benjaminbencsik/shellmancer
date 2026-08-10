from shellmancer.config import Config


def test_default_model(monkeypatch) -> None:
    monkeypatch.delenv("SHELLMANCER_MODEL", raising=False)
    assert Config.from_env().model == "qwen3:4b"


def test_model_can_be_overridden(monkeypatch) -> None:
    monkeypatch.setenv("SHELLMANCER_MODEL", "custom-model")
    assert Config.from_env().model == "custom-model"
