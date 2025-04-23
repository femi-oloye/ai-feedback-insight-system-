# scripts/gpt_insight_engine.py

import os
import pandas as pd
import openai
import json
from dotenv import load_dotenv
import requests
import json
import sys


# Load API key
load_dotenv()
openai.api_key = os.getenv("OPENROUTER_API_KEY")  # You can rename this if using OpenAI

# Load prompt template
with open("/home/oluwafemi/ai-feedback-insight-system/.venv/ai-feedback-insight-system-/prompts/insight_prompt.txt", "r") as file:
    prompt_template = file.read()

def get_insight(message):
    # Load model from config
    try:
        with open("config.json") as f:
            config = json.load(f)
            selected_model = config.get("model", "openai/gpt-3.5-turbo")
    except Exception as e:
        print("❌ Error loading config.json. Using default model.")
        selected_model = "openai/gpt-3.5-turbo"

    prompt = prompt_template.replace("{{customer_message}}", message)

    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
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
            print(f"OpenRouter Error: {response.status_code} - {response.text}")
            return {"summary": "", "sentiment": "", "themes": []}

        reply = response.json()["choices"][0]["message"]["content"]
        return json.loads(reply)

    except Exception as e:
        print(f"Error processing message: {message}\n{e}")
        return {"summary": "", "sentiment": "", "themes": []}

def analyze_feedback(file_path):
    df = pd.read_csv(file_path)

    summaries, sentiments, themes = [], [], []

    for msg in df["message"]:
        insight = get_insight(msg)
        summaries.append(insight["summary"])
        sentiments.append(insight["sentiment"])
        themes.append(", ".join(insight["themes"]))

    df["summary"] = summaries
    df["sentiment"] = sentiments
    df["themes"] = themes

    output_path = "uploaded_feedback_insights.csv"
    df.to_csv(output_path, index=False)
    print(f"✅ Insights saved to: {output_path}")



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Please provide a CSV file path.")
        sys.exit(1)

    file_path = sys.argv[1]
    analyze_feedback(file_path)

