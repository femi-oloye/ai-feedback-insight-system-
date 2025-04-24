import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
from wordcloud import WordCloud
import time
import json
import os
import concurrent.futures
from datetime import timedelta, datetime

# Custom AI insight function
from insight_engine import get_insight

# Set Streamlit page config
st.set_page_config(page_title="AI Customer Feedback Dashboard", layout="wide")

# Sidebar: LLM Model Selector
st.sidebar.title("⚙️ Settings")
selected_model = st.sidebar.selectbox(
    "Choose LLM model",
    ["openai/gpt-3.5-turbo", "anthropic/claude-3-sonnet", "mistral/mistral-7b-instruct"],
    index=0
)

# Save selected model to config
config_path = "config.json"
with open(config_path, "w") as f:
    json.dump({"model": selected_model}, f)

# Section: Upload & Analyze
st.subheader("📥 Upload New Customer Feedback for Analysis")

uploaded_file = st.file_uploader("Upload a CSV file with a 'message' column", type=["csv"])

# ========== PARALLEL PROCESSING FUNCTION ==========
def process_messages_parallel(messages, max_workers=5):
    results = []
    start_time = datetime.now()

    status = st.empty()
    progress = st.empty()

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_msg = {executor.submit(get_insight, msg): i for i, msg in enumerate(messages)}
        total = len(future_to_msg)

        for i, future in enumerate(concurrent.futures.as_completed(future_to_msg)):
            index = future_to_msg[future]
            try:
                result = future.result()
                results.append((index, result))
            except Exception as e:
                results.append((index, {"summary": "Error", "sentiment": "Neutral", "themes": []}))
                st.error(f"Error processing message {index}: {e}")

            elapsed = (datetime.now() - start_time).total_seconds()
            avg_time = elapsed / (i + 1)
            remaining = (total - i - 1) * avg_time
            eta = timedelta(seconds=int(remaining))

            status.text(f"✅ Processed {i + 1}/{total} messages | ⏳ ETA: {eta}")
            progress.progress((i + 1) / total)

    results.sort()  # ensure original order
    return [r[1] for r in results]

# ========== UPLOAD + TRIGGER INSIGHTS ==========
if uploaded_file is not None:
    with open("uploaded_feedback.csv", "wb") as f:
        f.write(uploaded_file.read())

    if st.button("🔍 Generate Insights with Selected Model"):
        st.warning("⏱️ This may take a few moments depending on number of messages...")
        df = pd.read_csv("uploaded_feedback.csv")

        insights = process_messages_parallel(df["message"].tolist(), max_workers=5)

        df["summary"] = [i["summary"] for i in insights]
        df["sentiment"] = [i["sentiment"] for i in insights]
        df["themes"] = [", ".join(i["themes"]) for i in insights]

        df.to_csv("uploaded_feedback_insights.csv", index=False)
        st.success("✅ Insights generated and saved successfully!")

# ========== LOAD DATA ==========
try:
    df = pd.read_csv("uploaded_feedback_insights.csv")
except FileNotFoundError:
    st.warning("No insights file found. Please upload and generate analysis.")
    st.stop()

# ========== CLEAN & NORMALIZE ==========
df["sentiment"] = df["sentiment"].str.strip().str.lower().str.capitalize()

# ========== KPI SUMMARY ==========
st.subheader("📈 Insight Summary")
col1, col2, col3 = st.columns(3)
col1.metric("Total Messages", len(df))
col2.metric("Positive %", f"{(df['sentiment'] == 'Positive').mean() * 100:.1f}%")
col3.metric("Negative %", f"{(df['sentiment'] == 'Negative').mean() * 100:.1f}%")

# ========== WORD CLOUD ==========
st.subheader("☁️ Message Keyword Cloud")
all_text = " ".join(df["message"].dropna().astype(str))
wordcloud = WordCloud(width=800, height=300, background_color="white").generate(all_text)
fig, ax = plt.subplots(figsize=(10, 4))
ax.imshow(wordcloud, interpolation="bilinear")
ax.axis("off")
st.pyplot(fig)

# ========== SENTIMENT CHART ==========
st.title("🧠 AI Customer Feedback Intelligence System")
st.subheader("📊 Sentiment Distribution")
st.bar_chart(df["sentiment"].value_counts())

# ========== TOP THEMES ==========
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
    st.info("No themes found.")

# ========== INSIGHT TABLE ==========
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
