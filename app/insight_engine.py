# scripts/gpt_insight_engine.py

import os
import json
import requests
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Load prompt template
with open("/home/oluwafemi/ai-feedback-insight-system/.venv/ai-feedback-insight-system-/prompts/insight_prompt.txt", "r") as file:
    prompt_template = file.read()

def get_insight(message: str) -> dict:
    # Load selected model from config
    try:
        with open("config.json") as f:
            config = json.load(f)
            selected_model = config.get("model", "openai/gpt-3.5-turbo")
    except Exception as e:
        print("⚠️ Failed to load model from config.json. Defaulting to gpt-3.5-turbo.")
        selected_model = "openai/gpt-3.5-turbo"

    # Replace placeholder in prompt template
    prompt = prompt_template.replace("{{customer_message}}", message)

    # Prepare OpenRouter API payload
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": selected_model,
        "messages": [
            {"role": "system", "content": "You are an AI customer feedback analyzer."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )

        if response.status_code != 200:
            print(f"❌ OpenRouter Error {response.status_code}: {response.text}")
            return {"summary": "Error", "sentiment": "Neutral", "themes": []}

        reply = response.json()["choices"][0]["message"]["content"]

        # Must return dict with summary, sentiment, themes
        parsed_reply = json.loads(reply)

        return {
            "summary": parsed_reply.get("summary", ""),
            "sentiment": parsed_reply.get("sentiment", "Neutral"),
            "themes": parsed_reply.get("themes", [])
        }

    except Exception as e:
        print(f"❌ Error in get_insight for message: {message[:50]}... \n{e}")
        return {"summary": "Error", "sentiment": "Neutral", "themes": []}
