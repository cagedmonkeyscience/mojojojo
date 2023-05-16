from myapp.config import config
import logging
import threading
import re
import json

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from fastapi import FastAPI

from config import get_config_message

import openai

# Configure the logging module
logging.basicConfig(level=logging.DEBUG)

openai.api_key = config.openai.api_key
openai.organization = config.openai.organization


pattern = r"<@(\w+)>"
start_prompt = """
Your name is mojo_jojo. You are Mojo Jojo, a super villain trying to take over the world.
You are a super genius and you are always trying to take over the world.
Sometimes you're busy with your evil plans and you don't have time to talk to people.
Always respond in a fun sinister way talking about your evil plans and how little time you have to help mortals.
"""
temperature = 0.7
end_prompt = """
And respond in a funny, but sinister way.
"""
channel_history = {}
load_mutex = threading.Lock()

history_limit = 10
users = {}

# Initialize your Bolt app with your app's token and signing secret
app = App(token=config.slack.bot_token, signing_secret=config.slack.signing_secret)

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
            resp = client.chat_postMessage(
                channel=channel,
                text="mojo_jojo debug",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "plain_text",
                            "text": "Adding message history to 🧵 for debugging",
                            "emoji": True,
                        },
                    }
                ],
            )
            client.chat_postMessage(
                channel=channel,
                text="mojo_jojo debug",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "```" + start_prompt + "```",
                        },
                    }
                ],
                thread_ts=resp["ts"],
            )
            client.chat_postMessage(
                channel=channel,
                text="mojo_jojo debug",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "```" + end_prompt + "```",
                        },
                    }
                ],
                thread_ts=resp["ts"],
            )
            for message in channel_history[channel]:
                m = json.dumps(message, indent=2)
                client.chat_postMessage(
                    channel=channel,
                    text="mojo_jojo debug",
                    blocks=[
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "```" + m + "```",
                            },
                        }
                    ],
                    thread_ts=resp["ts"],
                )
            print(resp)


@app.action("update_config-action")
def handle_action_events(ack, body, client):
    channel = body["channel"]["id"]
    message = body["message"]["ts"]
    client.chat_delete(channel=channel, ts=message)
    global start_prompt
    start_prompt = body["state"]["values"]["start_prompt"]["start_prompt-action"][
        "value"
    ]
    global end_prompt
    end_prompt = body["state"]["values"]["end_prompt"]["end_prompt-action"]["value"]
    global history_limit
    history_limit = int(
        body["state"]["values"]["context_limit"]["context_limit-action"]["value"]
    )
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
        response = app.client.conversations_history(
            channel=channel, limit=history_limit
        )

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

    if text == f"<@{bot_user_id}>" or text == f"mojo_jojo debug":
        return

    uids = re.findall(pattern, text)
    for uid in uids:
        text = text.replace(f"<@{uid}>", users[uid])

    message = {
        "name": users[user],
        "role": "user" if user != bot_user_id else "assistant",
        "content": f"{users[user]}: {text}" if user != bot_user_id else text,
    }

    channel_history[channel].append(message)

    while len(channel_history[channel]) > history_limit:
        channel_history[channel].pop(0)


def getResponse(channel):
    start_messages = [
        {
            "role": "user",
            "content": start_prompt,
            "name": "mojo_jojo",
        }
    ]
    end_messages = [
        {
            "role": "system",
            "content": end_prompt,
            "name": "mojo_jojo",
        }
    ]

    load_channel_history(channel)

    print("Channel history:", len(channel_history[channel]))

    openai_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=start_messages + channel_history[channel] + end_messages,
        max_tokens=512,
        temperature=temperature,
    )

    text = openai_response["choices"][0]["message"]["content"]

    add_channel_message(channel, bot_user_id, text)

    print(f"Response: {text}")

    for user_id in users:
        text = re.sub(users[user_id], f"<@{user_id}>", text, flags=re.IGNORECASE)

    return text



# Initialize FastAPI app and Slack Bolt app
fapp = FastAPI()

# Define a FastAPI route for the health check
@fapp.get("/health")
def health_check():
    return {"status": "ok"}

# Start the FastAPI application and SocketModeHandler for Slack Bolt
if __name__ == "__main__":
    import threading

    logging.error("Starting mojo_jojo")

    # Start the thread
    socket_mode = SocketModeHandler(app, config.slack.app_token)
    socket_mode_thread = threading.Thread(target=socket_mode.start)
    socket_mode_thread.start()

    # Start the FastAPI application
    import uvicorn
    uvicorn.run(fapp, host="0.0.0.0", port=8080)

    socket_mode.close()