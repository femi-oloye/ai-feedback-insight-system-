import httpx
import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}

# You can change this to another model (like 'mistralai/mistral-7b-instruct')
DEFAULT_MODEL = "openai/gpt-3.5-turbo"

def call_openrouter(prompt, model=DEFAULT_MODEL):
    body = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    response = httpx.post(BASE_URL, headers=HEADERS, json=body)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
