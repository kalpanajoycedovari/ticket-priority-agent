"""
test_groq.py

A quick check that our key works and the model answers.
Nothing to do with the agent, this is just a smoke test.
"""

import os
from dotenv import load_dotenv
from groq import Groq

# Reads the .env file and makes the key available.
load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {"role": "user", "content": "Say hello in exactly five words."}
    ],
)

print(response.choices[0].message.content)