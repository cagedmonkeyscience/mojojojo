# Logging
import logging
import logging.handlers


# Configure the logger
logger = logging.getLogger('mylogger')
logger.setLevel(logging.INFO)

# Create an instance of the SysLogHandler
handler = logging.handlers.SysLogHandler()

# Set the formatter for the log messages (optional)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(handler)

# Send log messages
logger.info('This is an info message.')
logger.warning('This is a warning message.')
logger.error('This is an error message.')


import threading
import os
import openai
import re
import json

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from flask import Flask, jsonify

from config import get_config_message

# Config
openai.organization = os.getenv("OPENAI_ORG")
openai.api_key = os.getenv("OPENAI_API_KEY")
bot_token = os.getenv("SLACK_BOT_TOKEN")
user_token = os.getenv("SLACK_USER_TOKEN")
app_token = os.getenv("SLACK_APP_TOKEN")
secret = os.getenv("SLACK_BOT_SECRET")
serper_key = os.getenv("SERPER_KEY")




pattern = r"<@(\w+)>"
start_prompt = """
Your name is mojo_jojo. You are Mojo Jojo, a super villain trying to take over the world.
You are a super genius and you are always trying to take over the world.
Sometimes you're busy with your evil plans and you don't have time to talk to people.
Always respond in a fun sinister way talking about your evil plans and how little time you have to help mortals.
"""
temperature=0.7
end_prompt = """
And respond in a funny, but sinister way.
"""
channel_history = {}
load_mutex = threading.Lock()

history_limit =10
users = {}

# Initialize your Bolt app with your app's token and signing secret
app = App(token=bot_token, signing_secret=secret,)
bot_user_id = app.client.auth_test().get("user_id")




@app.event("app_mention")
def handle_mention(body, say):
    event = body["event"]
    channel = event["channel"]
    response = getResponse(channel)
    say(response)

@app.event("message")
def handle_message_events(body, say):
    event = body["event"]
    text = event["text"]
    user = event["user"]
    channel = event["channel"]
    if "thread_ts" not in event:
        add_channel_message(channel, user, text)
    else:
        print("thread message")



@app.command("/mojo")
def handle_command_events(ack, body, client, say):
    ack()
    text = body["text"]
    channel = body["channel_id"]
    print(channel)
    if str.startswith(text, "say"):
        say(text[4:])
    elif str.startswith(text, "config"):
        say(get_config_message(start_prompt, end_prompt, history_limit))
    elif str.startswith(text, "temp"):
        global temperature
        temperature = float(text[5:])
    elif str.startswith(text, "debug"):
        if channel in channel_history:
            resp = client.chat_postMessage(channel=channel,
                text="mojo_jojo debug",
                blocks= [
                    {
                        "type": "section",
                        "text": {
                            "type": "plain_text",
                            "text": "Adding message history to 🧵 for debugging",
                            "emoji": True
                        }
                    }
                ]
            )
            client.chat_postMessage(channel=channel,
                text= "mojo_jojo debug",
                blocks= [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "```"+start_prompt+"```",
                        }
                    }
                ]
            ,thread_ts=resp["ts"])
            client.chat_postMessage(channel=channel,
                text= "mojo_jojo debug",
                blocks= [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "```"+end_prompt+"```",
                        }
                    }
                ]
            ,thread_ts=resp["ts"])
            for message in channel_history[channel]:
                m = json.dumps(message, indent=2)
                client.chat_postMessage(channel=channel,
                    text= "mojo_jojo debug",
                    blocks= [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "```"+m+"```",
                            }
                        }
                    ]
                ,thread_ts=resp["ts"])
            print(resp)

@app.action("update_config-action")
def handle_action_events(ack, body, client):
    channel = body["channel"]["id"]
    message = body["message"]["ts"]
    client.chat_delete(
        channel=channel,
        ts=message
    )
    global start_prompt
    start_prompt = body["state"]["values"]["start_prompt"]["start_prompt-action"]["value"]
    global end_prompt
    end_prompt = body["state"]["values"]["end_prompt"]["end_prompt-action"]["value"]
    global history_limit
    history_limit= int(body["state"]["values"]["context_limit"]["context_limit-action"]["value"])
    ack()

def load_users():
    response = app.client.users_list()
    for member in response["members"]:
        user = member["id"]
        name = member["name"]
        users[user] = name
        print(f"Loaded user: {name} ({user})")

def load_channel_history(channel):
    print(f"Loading channel history for {channel}")
    load_mutex.acquire()
    try:
        if channel in channel_history:
            return
        channel_history[channel] = []
        response = app.client.conversations_history(channel=channel,limit=history_limit)

        for message in response["messages"]:
            user = message["user"]
            text = message["text"]
            add_channel_message(channel, user, text)
    finally:
        print(f"Loading channel history completed for {channel}")
        load_mutex.release()

def add_channel_message(channel, user, text):
    if channel not in channel_history:

        load_channel_history(channel)

    if text == f'<@{bot_user_id}>' or text == f'mojo_jojo debug':
        return

    uids = re.findall(pattern, text)
    for uid in uids:
        text = text.replace(f"<@{uid}>", users[uid])

    message = {
        "name": users[user],
        "role":   "user" if user != bot_user_id else "assistant",
        "content": f"{users[user]}: {text}" if user != bot_user_id else text,
    }

    channel_history[channel].append(message)

    while len(channel_history[channel]) > history_limit:
        channel_history[channel].pop(0)

def getResponse(channel):
    start_messages = [{
        "role": "user",
        "content": start_prompt,
        "name": "mojo_jojo",
    }]
    end_messages = [{
        "role": "system",
        "content": end_prompt,
        "name": "mojo_jojo",
    }]

    load_channel_history(channel)

    print("Channel history:" ,len(channel_history[channel]))

    openai_response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=start_messages+channel_history[channel]+end_messages, max_tokens=512,temperature=temperature)

    text = openai_response["choices"][0]["message"]["content"]

    add_channel_message(channel, bot_user_id, text)

    print(f"Response: {text}")

    for user_id in users:
        text = re.sub(users[user_id], f"<@{user_id}>", text, flags=re.IGNORECASE)

    return text


def start_slack():
    SocketModeHandler(app, app_token).start()


fapp = Flask(__name__)
@fapp.route('/health', methods=['GET'])
def health_check():
    return jsonify(status='ok')

def start_flask():
    fapp.run(port=8080,host="0.0.0.0")


# Start your app
if __name__ == "__main__":
    load_users()

    flask_thread = threading.Thread(target=start_flask)
    slack_thread = threading.Thread(target=start_slack)
    flask_thread.start()
    slack_thread.start()
    flask_thread.join()
    slack_thread.join()

