import os


class OpenAI:
    """OpenAI class for storing the OpenAI environment variables"""

    def __init__(self):
        self._organization = os.getenv("OPENAI_ORG")
        self._api_key = os.getenv("OPENAI_API_KEY")

    @property
    def organization(self):
        return self._organization

    @property
    def api_key(self):
        return self._api_key


class Slack:
    """Slack class for storing the Slack environment variables"""

    def __init__(self):
        self._bot_token = os.getenv("SLACK_BOT_TOKEN")
        self._user_token = os.getenv("SLACK_USER_TOKEN")
        self._app_token = os.getenv("SLACK_APP_TOKEN")
        self._signing_secret = os.getenv("SLACK_BOT_SECRET")

    @property
    def bot_token(self):
        return self._bot_token

    @property
    def user_token(self):
        return self._user_token

    @property
    def app_token(self):
        return self._app_token

    @property
    def signing_secret(self):
        return self._signing_secret


class Serper:
    """Serper class for storing the Serper environment variables""" ""

    def __init__(self):
        self._api_key = os.getenv("SERPER_KEY")

    @property
    def api_key(self):
        return self._api_key


class Config:
    """Config class for storing all the environment variables"""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self._openai = OpenAI()
        self._slack = Slack()
        self._serper = Serper()

    @property
    def openai(self):
        return self._openai

    @property
    def slack(self):
        return self._slack

    @property
    def serper(self):
        return self._serper


