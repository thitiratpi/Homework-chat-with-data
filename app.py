import streamlit as st
import pandas as pd
import google.generativeai as genai

# ------------------ CONFIG ------------------
st.set_page_config(page_title="🤖 CSV Chatbot with Gemini", layout="wide")
st.title("🤖 CSV Chatbot with Gemini")
st.write("Upload your dataset and ask questions. Gemini will analyze and give answers.")
# --------------------------------------------

# 🔑 API Key
try:
    key = st.secrets['gemini_api_key']
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    if "chat" not in st.session_state:
        st.session_state.chat = model.start_chat(history=[])
    def role_to_streamlit(role): return "assistant" if role == "model" else role
except Exception as e:
    st.error(f"❌ Error loading Gemini: {e}")
    st.stop()

# ------------------ SESSION INIT ------------------
if "dataframe" not in st.session_state:
    st.session_state.dataframe = None
if "dictionary" not in st.session_state:
    st.session_state.dictionary = None
# ---------------------------------------------------

# ------------------ FILE UPLOAD -------------------
st.subheader("📤 Upload CSV and Optional Dictionary")
data_file = st.file_uploader("Upload Data Transaction", type=["csv"])
dict_file = st.file_uploader("Upload Data Dictionary", type=["csv", "txt"])

if data_file:
    try:
        df = pd.read_csv(data_file)
        st.session_state.dataframe = df
        st.success("✅ Data loaded")
        st.dataframe(df.head())
    except Exception as e:
        st.error(f"❌ CSV Error: {e}")

if dict_file:
    try:
        if dict_file.name.endswith(".csv"):
            dict_text = pd.read_csv(dict_file).to_string(index=False)
        else:
            dict_text = dict_file.read().decode("utf-8")
        st.session_state.dictionary = dict_text
        st.success("📘 Dictionary loaded")
    except Exception as e:
        st.error(f"❌ Dictionary Error: {e}")
# ---------------------------------------------------

# ------------------ CHAT HISTORY ------------------
for message in st.session_state.chat.history:
    with st.chat_message(role_to_streamlit(message.role)):
        st.markdown(message.parts[0].text)
# ---------------------------------------------------

# ------------------ USER PROMPT -------------------
if question := st.chat_input("💬 Ask me anything about your data..."):
    with st.chat_message("user"):
        st.markdown(question)

    df = st.session_state.dataframe
    dict_info = st.session_state.dictionary or "No dictionary provided."

    if df is not None:
        df_name = "df"
        data_dict_text = df.dtypes.to_string()
        example_record = df.head(2).to_string()

        # --- Gemini Code Generation Prompt ---
        code_prompt = f"""
You are a helpful Python code generator.
Your goal is to write Python code snippets based on the user's question
and the provided DataFrame information.

**User Question:**
{question}

**DataFrame Name:**
{df_name}

**DataFrame Details:**
{data_dict_text}

**Sample Data (Top 2 Rows):**
{example_record}

**Instructions:**
1. Write Python code that answers the question by querying or manipulating the DataFrame.
2. Use the exec() function to execute the generated code.
3. Do not import pandas.
4. Change date column type to datetime if needed.
5. Store result in a variable named ANSWER.
6. Assume the DataFrame is already loaded as {df_name}.
7. Keep the code concise and direct.
8. Return the final answer in `ANSWER`.
"""

        try:
            # 🔄 Generate and clean the code
            response = model.generate_content(code_prompt)
            generated_code = response.text.strip()
            if "```" in generated_code:
                generated_code = generated_code.split("```")[1].replace("python", "").strip()

            # 🔁 Execute code
            exec_locals = {df_name: df}
            exec(generated_code, {}, exec_locals)

            # ✅ Show result if exists
            if "ANSWER" in exec_locals:
                result = exec_locals["ANSWER"]
                st.markdown("### ✅ Result:")
                st.write(result)

                # 📄 Download .txt
                st.download_button(
                    label="📄 Download Result as .txt",
                    data=str(result),
                    file_name="gemini_answer.txt",
                    mime="text/plain"
                )

                # 💬 Add to chat (no code shown)
                st.session_state.chat.history.append({
                    "role": "model",
                    "parts": [f"**Result:**\n{result}"]
                })
                with st.chat_message("assistant"):
                    st.markdown(f"**Result:**\n{result}")
            else:
                st.warning("⚠️ No variable `ANSWER` found in generated code.")

        except Exception as e:
            st.error(f"❌ Gemini Error:\n{e}")
    else:
        st.warning("⚠️ Please upload a CSV file.")
# ---------------------------------------------------
