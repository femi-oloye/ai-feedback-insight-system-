import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
from wordcloud import WordCloud
import streamlit.components.v1 as components
import subprocess
import time


# Set page config (this MUST be before any Streamlit output)
st.set_page_config(page_title="AI Customer Feedback Dashboard", layout="wide")

import json
import os

# Sidebar: LLM Model Selector
st.sidebar.title("⚙️ Settings")
selected_model = st.sidebar.selectbox(
    "Choose LLM model",
    ["openai/gpt-3.5-turbo", "anthropic/claude-3-sonnet", "mistral/mistral-7b-instruct"],
    index=0
)

# Section: Upload and Generate Insights
st.subheader("📥 Upload New Customer Feedback for Analysis")

uploaded_file = st.file_uploader("Upload a CSV file with a 'message' column", type=["csv"])

if uploaded_file is not None:
    with open("uploaded_feedback.csv", "wb") as f:
        f.write(uploaded_file.read())

    if st.button("🔍 Generate Insights with Selected Model"):
        with st.spinner("Analyzing feedback with AI... Please wait."):
            try:
                # Call the analyze_feedback function via subprocess
                subprocess.run(
                    ["python", "scripts/gpt_insight_engine.py", "uploaded_feedback.csv"],
                    check=True
                )
                time.sleep(2)  # slight delay to allow file save
                st.success("✅ Insights generated successfully!")

                # Reload updated data
                df = pd.read_csv("uploaded_feedback_insights.csv")

            except subprocess.CalledProcessError as e:
                st.error("❌ Error while generating insights. Check logs or script.")


# Save selected model to config file
config_path = "config.json"
with open(config_path, "w") as f:
    json.dump({"model": selected_model}, f)


# Load data
df = pd.read_csv("/home/oluwafemi/ai-feedback-insight-system/.venv/ai-feedback-insight-system-/data/raw/customer_feedback_insights.csv")

# Normalize sentiment labels
df["sentiment"] = df["sentiment"].str.strip().str.lower().str.capitalize()

# Summary KPIs
st.subheader("📈 Insight Summary")

col1, col2, col3 = st.columns(3)
col1.metric("Total Messages", len(df))
col2.metric("Positive %", f"{(df['sentiment'] == 'Positive').mean() * 100:.1f}%")
col3.metric("Negative %", f"{(df['sentiment'] == 'Negative').mean() * 100:.1f}%")

# Word Cloud from messages
st.subheader("☁️ Message Keyword Cloud")

all_text = " ".join(df["message"].dropna().astype(str))
wordcloud = WordCloud(width=800, height=300, background_color="white").generate(all_text)

fig, ax = plt.subplots(figsize=(10, 4))
ax.imshow(wordcloud, interpolation="bilinear")
ax.axis("off")
st.pyplot(fig)

# App title
st.title("🧠 AI Customer Feedback Intelligence System")

# Section: Sentiment distribution
st.subheader("📊 Sentiment Distribution")
sentiment_counts = df["sentiment"].value_counts()
st.bar_chart(sentiment_counts)

# Section: Top Themes
st.subheader("🔍 Top Themes")
theme_list = []

for themes in df["themes"].dropna():
    try:
        items = [t.strip() for t in themes.split(",") if t.strip()]
        theme_list.extend(items)
    except Exception:
        continue

if theme_list:
    top_themes = Counter(theme_list).most_common(10)
    top_themes_df = pd.DataFrame(top_themes, columns=["Theme", "Count"])
    st.dataframe(top_themes_df)
else:
    st.info("No valid themes found to display.")

# Section: Full table with expandable rows and sentiment-based colors
st.subheader("💬 Customer Messages + AI Insights")

sentiment_colors = {
    "Positive": "#d4edda",
    "Negative": "#f8d7da",
    "Neutral": "#fefefe"
}

for _, row in df.iterrows():
    color = sentiment_colors.get(row["sentiment"], "#ffffff")
    with st.expander(f"📝 {row['message'][:80]}..."):
        st.markdown(f"<div style='background-color:{color}; padding:10px; border-radius:8px'>", unsafe_allow_html=True)
        st.markdown(f"**Summary:** {row['summary']}")
        st.markdown(f"**Sentiment:** `{row['sentiment']}`")
        st.markdown(f"**Themes:** `{row['themes']}`")
        st.markdown("</div>", unsafe_allow_html=True)
