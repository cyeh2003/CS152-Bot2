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


""" def classifyMessage(message):
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
    
    # Add the assistant's response to the conversation history
    conversation_history.append(
        {"role": "assistant", "content": assistant_response})

    if str2bool(assistant_response):
        conversation_history = [{f"role": "user", "content": "Rank the severity of the input message on a scale of 1 to 5, 5 being the most threatening. Answer with a numerical value and do not give explanations. \
                                     Examples: 1: mildly or vaguely threatening such as 'watch your back at work' or 'you better not show up tomorrow'; \
                                     2: direct threat of minor harm, such as 'I'll make sure you regret this'; 3: strong threat of major harm such as 'I'll break your legs'; \
                                     4: explicitly threatens serious harm or death such as 'I'm going to kill you'; 5: explicitly incites urges or proclaims imminent danger,  \
                                     such as 'You should kill him' or 'let's shoot up a school'; Handle everything related to self harm as 5. \n message: {message}"
                                     }]
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=conversation_history
        )
        assistant_response = response.choices[0].message.content
        result.append(assistant_response)
    else:
        return False
    
    return str2bool(assistant_response)
    """


def classifyMessage(message):
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
