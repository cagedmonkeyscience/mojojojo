
def get_config_message(start_prompt,end_prompt, history_limit):
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
                "block_id": "start_prompt",
                "element": {
                    "type": "plain_text_input",
                    "multiline": True,
                    "initial_value": start_prompt,
                    "action_id": "start_prompt-action"
                },
                "label": {
                    "type": "plain_text",
                    "text": "Starting Prompt"
                }
            },
            {
                "type": "input",
                "block_id": "end_prompt",
                "element": {
                    "type": "plain_text_input",
                    "multiline": True,
                    "initial_value": end_prompt,
                    "action_id": "end_prompt-action"
                },
                "label": {
                    "type": "plain_text",
                    "text": "Ending Prompt"
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