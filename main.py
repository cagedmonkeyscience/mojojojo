import threading
import os
import openai
import re
import json

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# Confif
openai.organization = "org-tx7KIAdEzHGdEcrcIzHAHOYs"
openai.api_key = os.getenv("OPENAI_API_KEY")
bot_token = os.getenv("SLACK_BOT_TOKEN")
user_token = os.getenv("SLACK_USER_TOKEN")
app_token = os.getenv("SLACK_APP_TOKEN")
secret = os.getenv("SLACK_BOT_SECRET")





pattern = r"<@(\w+)>"
context = "Your name is mojo_jojo the super villain Mojo Jojo, you should always answer in character. You are a super genius and you are always trying to take over the world. Sometimes you're busy with your evil plans and you don't have time to talk to people. And always remember to be evil."
channel_history = {}
load_mutex = threading.Lock()

history_limit = 50
users = {}

# Initialize your Bolt app with your app's token and signing secret
app = App(token=bot_token, signing_secret=secret,)
bot_user_id = app.client.auth_test().get("user_id")


def get_config_message():
    return {
        "text": "Mojo Jojo config",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Mojo Jojo config",
                    "emoji": True
                }
            },
            {
                "type": "input",
                "block_id": "context_message",
                "element": {
                    "type": "plain_text_input",
                    "multiline": True,
                    "initial_value": context,
                    "action_id": "context_message-action"
                },
                "label": {
                    "type": "plain_text",
                    "text": "Context Message"
                }
            },
            {
                "type": "input",
                "block_id": "context_limit",
                "element": {
                    "type": "plain_text_input",
                    "initial_value": str(history_limit),
                    "action_id": "context_limit-action"
                },
                "label": {
                    "type": "plain_text",
                    "text": "Number of message to keep in context",
                    "emoji": True
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Update",
                            "emoji": True
                        },
                        "value": "click_me_123",
                        "action_id": "update_config-action"
                    }
                ]
            }
        ]
    }

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
    return add_channel_message(channel, user, text)



@app.command("/mojo")
def handle_command_events(ack, body, say):

    text = body["text"]

    if str.startswith(text, "say"):
        say(text[4:])
    elif str.startswith(text, "config"):
        say(get_config_message())
    elif str.startswith(text, "debug"):
        jsonHistory = json.dumps(history, indent=2)
        say({
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "chat history:",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "```"+jsonHistory+"```",
                    }
                }
            ]
        })
    ack()

@app.action("update_config-action")
def handle_action_events(ack, body, client):
    channel = body["channel"]["id"]
    message = body["message"]["ts"]
    client.chat_delete(
        channel=channel,
        ts=message
    )
    global context
    context = body["state"]["values"]["context_message"]["context_message-action"]["value"]
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
            add_channel_message(channel,user, text)
    finally:
        print(f"Loading channel history completed for {channel}")
        load_mutex.release()

def add_channel_message(channel, user, text):
    if channel not in channel_history:

        load_channel_history(channel)

    if text == f'<@{bot_user_id}>' or user == bot_user_id:
        return

    uids = re.findall(pattern, text)
    for uid in uids:
        text = text.replace(f"<@{uid}>", users[uid])

    message = {
        "name": users[user],
        "role":   "user" if user != bot_user_id else "assistant",
        "content": f"{users[user]}: {text}",
    }

    channel_history[channel].append(message)

    while len(channel_history[channel]) > history_limit:
        channel_history[channel].pop(0)

def getResponse(channel):
    messages = [{
        "role": "system",
        "content": context,
        "name": "mojo_jojo",
    }]

    load_channel_history(channel)

    print("Channel history:" ,len(channel_history[channel]))

    openai_response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages+channel_history[channel], max_tokens=512)

    text = openai_response["choices"][0]["message"]["content"]

    response = openai_response["choices"][0]["message"]
    response["name"] = "mojo_jojo"
    response["content"] = "mojo_jojo: "+response["content"]
    channel_history[channel].append(response)

    print(f"Response: {text}")

    for user_id in users:
        text = re.sub(users[user_id], f"<@{user_id}>", text, flags=re.IGNORECASE)

    return text



# Start your app
if __name__ == "__main__":
    load_users()
    SocketModeHandler(app, app_token).start()