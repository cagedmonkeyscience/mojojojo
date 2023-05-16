import pytest
import os
from myapp.config import Config, OpenAIConfig, SlackConfig, SerperConfig


@pytest.fixture(autouse=True, scope="package")
def initialization():
    # This fixture is automatically used for all tests
    # It ensures the environment variables are set for each test
    os.environ["OPENAI_ORG"] = "OPENAI_ORG"
    os.environ["OPENAI_API_KEY"] = "OPENAI_API_KEY"
    os.environ["SLACK_BOT_TOKEN"] = "SLACK_BOT_TOKEN"
    os.environ["SLACK_USER_TOKEN"] = "SLACK_USER_TOKEN"
    os.environ["SLACK_APP_TOKEN"] = "SLACK_APP_TOKEN"
    os.environ["SLACK_BOT_SECRET"] = "SLACK_BOT_SECRET"
    os.environ["SERPER_KEY"] = "SERPER_KEY"

    yield
    # Teardown: Remove the environment variables after each test
    del os.environ["OPENAI_ORG"]
    del os.environ["OPENAI_API_KEY"]
    del os.environ["SLACK_BOT_TOKEN"]
    del os.environ["SLACK_USER_TOKEN"]
    del os.environ["SLACK_APP_TOKEN"]
    del os.environ["SLACK_BOT_SECRET"]
    del os.environ["SERPER_KEY"]


def test_openai_organization():
    config = Config()
    assert isinstance(config.openai, OpenAIConfig)
    assert config.openai.organization == "OPENAI_ORG"


def test_slack_bot_token():
    config = Config()
    assert isinstance(config.slack, SlackConfig)
    assert config.slack.bot_token == "SLACK_BOT_TOKEN"


def test_serper_api_key():
    config = Config()
    assert isinstance(config.serper, SerperConfig)
    assert config.serper.api_key == "SERPER_KEY"
