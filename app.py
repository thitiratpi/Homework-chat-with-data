import streamlit as st
import pandas as pd
import google.generativeai as genai

# Page layout
st.set_page_config(page_title="🧠 CSV CodeBot with Gemini", layout="wide")
st.title("🧠 CSV CodeBot with Gemini")
st.write("Upload your CSV file and ask Python-style questions! The AI will generate and execute Python code to answer.")

# Gemini API Key input
gemini_api_key = st.text_input("🔐 Gemini API Key", type="password")
model = None
if gemini_api_key:
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        st.success("✅ Gemini connected.")
    except Exception as e:
        st.error(f"❌ Failed to configure Gemini: {e}")

# Session state setup
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "dataframe" not in st.session_state:
    st.session_state.dataframe = None

# Upload CSV file
uploaded_file = st.file_uploader("📂 Upload your CSV file", type=["csv"])
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        st.session_state.dataframe = df
        st.success("✅ Data loaded.")
        st.write("### Data Preview")
        st.dataframe(df.head())
    except Exception as e:
        st.error(f"❌ Failed to load CSV: {e}")

# Display chat history
for role, message in st.session_state.chat_history:
    st.chat_message(role).markdown(message)

# User input
if question := st.chat_input("Ask a Python-style question about the data..."):
    st.session_state.chat_history.append(("user", question))
    st.chat_message("user").markdown(question)

    if model and st.session_state.dataframe is not None:
        try:
            df_name = "df"
            data_dict_text = st.session_state.dataframe.dtypes.to_string()
            example_record = st.session_state.dataframe.head(2).to_string()

            # Prompt for code generation
            prompt = f"""
You are a helpful Python code generator.
Your goal is to write Python code snippets based on the user's question
and the provided DataFrame information.
Here's the context:

**User Question:**
{question}

**DataFrame Name:**
{df_name}

**DataFrame Details:**
{data_dict_text}

**Sample Data (Top 2 Rows):**
{example_record}

**Instructions:**
1. Write Python code that addresses the user's question by querying or manipulating the DataFrame.
2. **Crucially, use the exec() function to execute the generated code.**
3. Do not import pandas
4. Change date column type to datetime
5. **Store the result of the executed code in a variable named `ANSWER`.**
   This variable should hold the answer to the user's question (e.g., a filtered DataFrame, a calculated value, etc.).
6. Assume the DataFrame is already loaded into a pandas DataFrame object named `{df_name}`. Do not include code to load the DataFrame.
7. Keep the generated code concise and focused on answering the question.
8. If the question requires a specific output format (e.g., a list, a single value), ensure the query_result variable holds that format.

**Example:**
If the user asks: "Show me the rows where the 'age' column is greater than 30."
And the DataFrame has an 'age' column.
The generated code should look something like this (inside the exec() string):

```python
query_result = {df_name}[{df_name}['age'] > 30]

        # Generate Python code using Gemini
        response = model.generate_content(prompt)
        generated_code = response.text
        st.code(generated_code, language='python')

        # Execute the generated code
        exec_locals = {"df": st.session_state.dataframe}
        exec(generated_code, {}, exec_locals)

        # Display the result from variable `ANSWER`
        if "ANSWER" in exec_locals:
            st.success("✅ Result from executed code:")
            st.write(exec_locals["ANSWER"])
            st.session_state.chat_history.append(("assistant", f"```python\n{generated_code}\n```\n\n**Result:**\n{exec_locals['ANSWER']}"))
            st.chat_message("assistant").markdown(f"```python\n{generated_code}\n```\n\n**Result:**\n{exec_locals['ANSWER']}")
        else:
            st.warning("⚠️ No variable named `ANSWER` was defined in the generated code.")

    except Exception as e:
        st.error(f"❌ Error while generating or executing code: {e}")
else:
    st.warning("Please upload a CSV and provide a valid API key.")


---

### ✅ ตัวอย่างคำถามที่รองรับ:
- "แสดงยอดขายเฉลี่ยต่อเดือน"
- "กรองเฉพาะข้อมูลเดือนมกราคม"
- "ยอดขายรวมในปี 2024 เท่าไหร่"
- "มีสินค้ากี่ประเภท"

---

ถ้าต้องการให้ AI แสดงกราฟ หรือ export โค้ดที่ได้ออกเป็น .py/.ipynb ก็บอกได้เลยครับ  
จะให้รองรับหลายตาราง หรือเชื่อมหลายไฟล์ก็ทำได้เช่นกัน! 🔥
