import streamlit as st
import pandas as pd
import google.generativeai as genai

# Page config
st.set_page_config(page_title="🤖 CSV Chatbot with Gemini", layout="wide")

st.title("🤖 CSV Chatbot with Gemini")
st.write("Upload your dataset and ask questions. Gemini will answer or generate Python code to help you!")

# Load API Key & configure Gemini
try:
    key = st.secrets['gemini_api_key']
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-2.0-flash-lite')

    # Create chat session with history
    if "chat" not in st.session_state:
        st.session_state.chat = model.start_chat(history=[])

    def role_to_streamlit(role: str) -> str:
        return "assistant" if role == "model" else role

except Exception as e:
    st.error(f"❌ Error initializing Gemini: {e}")
    st.stop()

# Initialize session state
if "dataframe" not in st.session_state:
    st.session_state.dataframe = None

if "dictionary" not in st.session_state:
    st.session_state.dictionary = None

# Upload files
st.subheader("📤 Upload CSV and Optional Dictionary")
data_file = st.file_uploader("Upload Data Transaction", type=["csv"])
dict_file = st.file_uploader("Upload Data Dictionary", type=["csv", "txt"])

if data_file:
    try:
        df = pd.read_csv(data_file)
        st.session_state.dataframe = df
        st.success("✅ Data loaded")
        st.write("### Data Preview")
        st.dataframe(df.head())
    except Exception as e:
        st.error(f"❌ Error reading data file: {e}")

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
for message in st.session_state.chat.history:
    with st.chat_message(role_to_streamlit(message.role)):
        st.markdown(message.parts[0].text)

# User input
if prompt := st.chat_input("💬 Ask me anything about your data..."):
    with st.chat_message("user"):
        st.markdown(prompt)

    df = st.session_state.dataframe
    dict_info = st.session_state.dictionary or "No dictionary provided."

    if df is not None:
        df_name = "df"
        data_dict_text = df.dtypes.to_string()
        example_record = df.head(2).to_string()

        # --- Code generation prompt ---
        code_prompt = f"""
You are a helpful Python code generator.
Your goal is to write Python code snippets based on the user's question
and the provided DataFrame information.

**User Question:**
{prompt}

**DataFrame Name:**
{df_name}

**DataFrame Details:**
{data_dict_text}

**Sample Data (Top 2 Rows):**
{example_record}

**Instructions:**
1. Write Python code that addresses the user's question by querying or manipulating the DataFrame.
2. **Crucially, use the exec() function to execute the generated code.**
3. Do not import pandas.
4. Change date column type to datetime.
5. **Store the result of the executed code in a variable named `ANSWER`.**
6. Assume the DataFrame is already loaded into a pandas DataFrame object named `{df_name}`. Do not include code to load the DataFrame.
7. Keep the generated code concise and focused on answering the question.
8. If the question requires a specific output format (e.g., a list, a single value), ensure the query_result variable holds that format.

**Example:**
If the user asks: "Show me the rows where the 'age' column is greater than 30."
And the DataFrame has an 'age' column.
The generated code should look something like this (inside the exec() string):

```python
query_result = {df_name}[{df_name}['age'] > 30]
"""
            try:
        # Generate code
        response = model.generate_content(code_prompt)
        generated_code = response.text.strip()

        # Clean up markdown wrappers if any
        if "```" in generated_code:
            generated_code = generated_code.split("```")[1].replace("python", "").strip()

        st.markdown("#### 🧠 Generated Python Code:")
        st.code(generated_code, language="python")

        # Execute the code
        exec_locals = {"df": df}
        exec(generated_code, {}, exec_locals)

        if "ANSWER" in exec_locals:
            st.markdown("### ✅ Result from Executed Code:")
            st.write(exec_locals["ANSWER"])

            # Add to chat history
            st.session_state.chat.history.append(
                {"role": "model", "parts": [f"```python\n{generated_code}\n```\n\n**Result:**\n{exec_locals['ANSWER']}"]}
            )
            with st.chat_message("assistant"):
                st.markdown(f"```python\n{generated_code}\n```\n\n**Result:**\n{exec_locals['ANSWER']}")
        else:
            st.warning("⚠️ Code executed but no variable named `ANSWER` was found.")

    except Exception as e:
        st.error(f"❌ Error generating or executing code: {e}")
else:
    st.warning("⚠️ Please upload a CSV file before asking questions.")
