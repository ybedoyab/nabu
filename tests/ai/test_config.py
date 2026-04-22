from ai.src.infrastructure.config import Config


def test_config_has_openai_defaults():
    assert isinstance(Config.OPENAI_MODEL, str)
    assert Config.OPENAI_MODEL != ""
    assert isinstance(Config.OPENAI_MAX_TOKENS, int)
    assert isinstance(Config.OPENAI_TEMPERATURE, float)
