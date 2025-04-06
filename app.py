import streamlit as st
import pandas as pd
import google.generativeai as genai

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="📊 CSV Chatbot with Gemini", layout="wide")
st.title("🤖 CSV Chatbot with Gemini")
st.write("Upload your dataset and ask questions. Gemini will give natural language insights!")

# ---------- API KEY ----------
gemini_api_key = st.secrets['gemini_api_key']
model = None

if gemini_api_key:
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        st.success("✅ Gemini API Key configured.")
    except Exception as e:
        st.error(f"❌ Failed to configure Gemini: {e}")

# ---------- SESSION STATE ----------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "dataframe" not in st.session_state:
    st.session_state.dataframe = None
if "dictionary" not in st.session_state:
    st.session_state.dictionary = None

# ---------- FILE UPLOAD ----------
st.subheader("📤 Upload CSV: Data Transaction and Data Dictionary")
data_file = st.file_uploader("Upload Data Transaction", type=["csv"])
dict_file = st.file_uploader("Upload Data Dictionary", type=["csv", "txt"])

# Load CSV
if data_file:
    try:
        df = pd.read_csv(data_file)

        # ✅ แปลง date เป็น datetime หากมีคอลัมน์ชื่อ 'date'
        if 'date' in df.columns:
            try:
                df['date'] = pd.to_datetime(df['date'])
                st.info("ℹ️ Column 'date' has been converted to datetime format.")
            except:
                st.warning("⚠️ Couldn't convert 'date' column to datetime.")

        st.session_state.dataframe = df
        st.success("✅ Data loaded")
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

# ---------- DISPLAY CHAT HISTORY ----------
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------- USER CHAT INPUT ----------
st.subheader("💬 Ask Questions About Your Data")

if prompt := st.chat_input("Ask me anything about your data..."):
    # Show and store user message
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    df = st.session_state.dataframe
    dict_info = st.session_state.dictionary or "No dictionary provided."

    if model and df is not None:
        try:
            sample_data = df.head(3).to_string()
            stats = df.describe(include='all').to_string()

            # ---------- SYSTEM PROMPT WITHOUT CODE ----------
            system_prompt = f"""
You are a helpful data analyst AI. Your task is to analyze the dataset and provide insights based on user questions.

**IMPORTANT:**
- The column named 'date' (if exists) has already been converted to datetime.
- Do not include Python code in your response.
- Always answer using clear, natural language. Do not assume technical expertise.

**Sample Data (Top 3 rows):**
{sample_data}

**Statistical Summary:**
{stats}

**Data Dictionary:**
{dict_info}

User Question:
{prompt}
"""

            # Generate response from Gemini
            response = model.generate_content(system_prompt)
            answer = response.text

            # Show and store assistant response
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            with st.chat_message("assistant"):
                st.markdown(answer)

        except Exception as e:
            st.error(f"❌ Error generating response: {e}")
    else:
        st.warning("⚠️ Please upload a CSV file before asking.")
