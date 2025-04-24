import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
from wordcloud import WordCloud
import subprocess
import time
import json
import os
from fpdf import FPDF

# Set page config (this MUST be before any Streamlit output)
st.set_page_config(page_title="AI Customer Feedback Dashboard", layout="wide")

# Path for storing cached insights
CACHE_PATH = "uploaded_feedback_insights.csv"

# Load API key from .env file
from dotenv import load_dotenv
load_dotenv()

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
force_refresh = st.checkbox("🔁 Force refresh all rows", value=False)

def get_insight(message):
    # Function to simulate insight generation for each message (replace with your own)
    # Here, you would call OpenRouter or any other model you use
    return {
        "summary": f"Summary for: {message[:50]}...",
        "sentiment": "Positive",  # Sentiment Analysis (Positive/Negative)
        "themes": ["Theme1", "Theme2"]
    }

def process_feedback(df, force_refresh=False):
    # Load cached insights if available
    if os.path.exists(CACHE_PATH):
        cached_df = pd.read_csv(CACHE_PATH)
        cached_map = dict(zip(cached_df["message"], cached_df.to_dict(orient="records")))
        st.success(f"🔁 Loaded {len(cached_map)} cached rows.")
    else:
        cached_map = {}

    summaries, sentiments, themes = [], [], []

    for _, row in df.iterrows():
        msg = row["message"]

        # Skip if already cached
        if msg in cached_map and not force_refresh:
            cached = cached_map[msg]
            summaries.append(cached["summary"])
            sentiments.append(cached["sentiment"])
            themes.append(cached["themes"])
            st.info(f"✅ Skipped cached message: {msg[:50]}...")
            continue

        with st.spinner(f"Processing message: {msg[:50]}..."):
            insight = get_insight(msg)
            summaries.append(insight["summary"])
            sentiments.append(insight["sentiment"])
            themes.append(", ".join(insight["themes"]))

    df["summary"] = summaries
    df["sentiment"] = sentiments
    df["themes"] = themes

    df.to_csv(CACHE_PATH, index=False)
    st.success("✅ All insights saved and updated.")
    return df

# Handle file upload and insights generation
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    if st.button("Generate Insights"):
        processed_df = process_feedback(df, force_refresh=force_refresh)
        st.dataframe(processed_df)

# Save selected model to config file
config_path = "config.json"
with open(config_path, "w") as f:
    json.dump({"model": selected_model}, f)

# Load data from cached CSV (if exists)
if os.path.exists(CACHE_PATH):
    df = pd.read_csv(CACHE_PATH)

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

    # Sentiment distribution
    st.subheader("📊 Sentiment Distribution")
    sentiment_counts = df["sentiment"].value_counts()
    st.bar_chart(sentiment_counts)

    # Top Themes
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

    # Full table with expandable rows
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

# Export Summary to PDF or HTML
def export_summary_to_pdf(df):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Customer Feedback Insights", ln=True, align="C")
    pdf.ln(10)

    for _, row in df.iterrows():
        pdf.multi_cell(0, 10, f"Message: {row['message']}\nSummary: {row['summary']}\nSentiment: {row['sentiment']}\nThemes: {row['themes']}\n\n")
    
    pdf.output("insights_summary.pdf")
    st.success("✅ PDF Summary Exported!")

def export_summary_to_html(df):
    html = df.to_html(index=False)
    with open("insights_summary.html", "w") as f:
        f.write(html)
    st.success("✅ HTML Summary Exported!")

# Export button to PDF or HTML
export_option = st.selectbox("Export Insights as", ["None", "PDF", "HTML"])

if export_option == "PDF":
    if st.button("Export to PDF"):
        export_summary_to_pdf(df)

elif export_option == "HTML":
    if st.button("Export to HTML"):
        export_summary_to_html(df)
