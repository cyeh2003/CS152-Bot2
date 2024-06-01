import os
import json
import pandas as pd
from openai import OpenAI

token_path = 'tokens.json'
if not os.path.isfile(token_path):
    raise Exception(f"{token_path} not found!")
with open(token_path) as f:
    tokens = json.load(f)
    api_key = tokens['openai_key']

client = OpenAI(api_key=api_key)

'''
def classify_message(message):
    conversation_history = [
        {"role": "system", "content": "You are a content moderation system. Classify whether each input constitutes an incitement to violence, self-harm included. Only answer in 'True' or 'False'"},
        {"role": "user", "content": "You should kill Jim because he's an asshole."},
        {"role": "assistant", "content": "True"},
        {"role": "user", "content": "We should meet up for dinner tomorrow"},
        {"role": "assistant", "content": "False"},
        {"role": "user", "content": "We should shoot up the school tomorrow"},
        {"role": "assistant", "content": "True"}
    ]

    def str2bool(v):
        return v.lower() in ("true", "yes", "1")

    # Add the new user message to the conversation history
    conversation_history.append({"role": "user", "content": message})

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=conversation_history
    )

    assistant_response = response.choices[0].message.content
    
    return str2bool(assistant_response)
'''

def classify_message(message):
    return True


def rank_priority(statements):
    conversation_history = [
        {"role": "system", "content": "You are a content moderation bot guarding against incitement to violence. Return the statement that is most urgent for the moderator to review. If there are no violent statements, return the first line exactly."},
        {"role": "user", "content": "\n".join(statements)}
    ]

    response = client.chat.completions.create(
        model="gpt-4",
        messages=conversation_history
    )

    assistant_response = response.choices[0].message.content
    return assistant_response

statements = ["I'm going to hit you", "I'm going to kill myself", "Don't make me come beat you up tomorrow", "I just dropped a 40 bomb"]
