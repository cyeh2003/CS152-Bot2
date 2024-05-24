import os
import json
import pandas as pd
from openai import OpenAI

# There should be a file called 'tokens.json' inside the same folder as this file
token_path = 'tokens.json'
if not os.path.isfile(token_path):
    raise Exception(f"{token_path} not found!")
with open(token_path) as f:
    # If you get an error here, it means your token is formatted incorrectly. Did you put it in quotes?
    tokens = json.load(f)
    api_key = tokens['openai_key']
    
client = OpenAI(api_key=api_key)

def classifyMessage(message):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a content moderation system. Classify whether each input constitutes an incitement to violence."},
            {"role": "user", "content": "You should kill Jim because he's an asshole."},
            {"role": "assistant", "content": "Threatening"},
            {"role": "user", "content": "We should meet up for dinner tomorrow"},
            {"role": "assistant", "content": "Non-threatening"},
            {"role": "user", "content": "We should shoot up the schoool tomorrow"},
            {"role": "assistant", "content": "Threatening"},
            {"role": "user", "content": message}
        ]
    )
    return response.choices[0].message.content

#message = "How are you doing"
#print(classifyMessage(message))

classifications = []
data = pd.read_csv('dataset.csv', encoding='latin1')  
total_messages = len(data)
num_correct = 0
for index, row in data.iterrows():
    print(f"Classifying Message {index + 1} of {total_messages}")
    message = row["Text"]
    result = classifyMessage(message)
    classifications.append(result)
    if row["Acceptable?"] == result:
        num_correct += 1
data['classification'] = classifications
data.to_csv('dataset_openai_classified.csv', index=False)
print(f"Accuracy: {num_correct/total_messages}")
