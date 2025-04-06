import streamlit as st
import pandas as pd
import google.generativeai as genai

# Page config
st.set_page_config(page_title="📊 CSV Chatbot with Gemini", layout="wide")
st.title("🤖 CSV Chatbot with Gemini")
st.write("Upload your dataset and ask questions in natural language!")

# API Key input
gemini_api_key = st.secrets['gemini_api_key']
model = None

if gemini_api_key:
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        st.success("✅ Gemini API Key configured.")
    except Exception as e:
        st.error(f"❌ Failed to configure Gemini: {e}")

# Session state init
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "dataframe" not in st.session_state:
    st.session_state.dataframe = None
if "dictionary" not in st.session_state:
    st.session_state.dictionary = None

# Upload section
st.subheader("📤 Upload CSV and Optional Dictionary")
data_file = st.file_uploader("Upload Data Transaction", type=["csv"])
dict_file = st.file_uploader("Upload Data Dictionary", type=["csv", "txt"])

# Load CSV
if data_file:
    try:
        df = pd.read_csv(data_file)

        # ✅ Convert 'date' column to datetime if it exists
        if 'date' in df.columns:
            try:
                df['date'] = pd.to_datetime(df['date'])
                st.info("ℹ️ 'date' column converted to datetime format.")
            except:
                st.warning("⚠️ Failed to convert 'date' to datetime.")

        st.session_state.dataframe = df
        st.success("✅ Data loaded successfully")
        st.write("### Preview of Data")
        st.dataframe(df.head())

    except Exception as e:
        st.error(f"❌ Error reading CSV: {e}")

# Load Dictionary
if dict_file:
    try:
        if dict_file.name.endswith(".csv"):
            dict_df = pd.read_csv(dict_file)
            dict_text = dict_df.to_string(index=False)
        else:
            dict_text = dict_file.read().decode("utf-8")
        st.session_state.dictionary = dict_text
        st.success("📘 Dictionary loaded")
    except Exception as e:
        st.error(f"❌ Error reading dictionary file: {e}")

# Show chat history
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
st.subheader("💬 Ask Questions About Your Data")

if prompt := st.chat_input("Ask me anything about your data..."):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    df = st.session_state.dataframe
    dict_info = st.session_state.dictionary or "No dictionary provided."

    if model and df is not None:
        try:
            sample_data = df.head(3).to_string()
            stats = df.describe(include='all').to_string()

            # 🧠 Tell Gemini that date column is already datetime
            system_prompt = f"""
You are a helpful data analyst AI. You are helping the user analyze the dataset.

**IMPORTANT:** If the dataset contains a 'date' column, it has already been converted to datetime format. You can use `.dt.year`, `.dt.month`, `.dt.date` safely.

**Data Preview (Top 3 rows):**
{sample_data}

**Statistical Summary:**
{stats}

**Data Dictionary:**
{dict_info}

Now, answer the following question based on this dataset.
"""

            full_prompt = system_prompt + "\n\nUser Question:\n" + prompt
            response = model.generate_content(full_prompt)
            answer = response.text

            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            with st.chat_message("assistant"):
                st.markdown(answer)

        except Exception as e:
            st.error(f"❌ Error generating response: {e}")
    else:
        st.warning("⚠️ Please upload a CSV file before asking questions.")

