from myapp.config import Config, OpenAI, Slack, Serper

def test_openai_organization():
    config = Config()
    assert isinstance(config.openai, OpenAI)
    assert config.openai.organization == "EXPECTED_VALUE"

def test_slack_bot_token():
    config = Config()
    assert isinstance(config.slack, Slack)
    assert config.slack.bot_token == "EXPECTED_VALUE"

def test_serper_api_key():
    config = Config()
    assert isinstance(config.serper, Serper)
    assert config.serper.api_key == "EXPECTED_VALUE"
