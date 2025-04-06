import streamlit as st
import pandas as pd
import google.generativeai as genai

# Set up the Streamlit app layout
st.title("🐧 My Chatbot and Data Analysis App")
st.subheader("Conversation and Data Analysis")

# --- API Key ---
gemini_api_key = st.text_input("Gemini API Key: ", placeholder="Type your API Key here...", type="password")

# --- Load Gemini Model ---
model = None
if gemini_api_key:
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        st.success("Gemini API Key successfully configured.")
    except Exception as e:
        st.error(f"An error occurred while setting up the Gemini model: {e}")

# --- Session State Setup ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "uploaded_data" not in st.session_state:
    st.session_state.uploaded_data = None

if "uploaded_dict" not in st.session_state:
    st.session_state.uploaded_dict = None

# --- Display Chat History ---
for role, message in st.session_state.chat_history:
    st.chat_message(role).markdown(message)

# --- File Uploads ---
st.subheader("Upload CSV for Analysis")
uploaded_file = st.file_uploader("Choose a **CSV data file**", type=["csv"])

st.subheader("Upload Dictionary File (optional)")
dict_file = st.file_uploader("Choose a **dictionary file** (CSV or TXT)", type=["csv", "txt"])

# --- Load Files ---
if uploaded_file is not None:
    try:
        st.session_state.uploaded_data = pd.read_csv(uploaded_file)
        st.success("Data file uploaded successfully.")
        st.write("### Data Preview")
        st.dataframe(st.session_state.uploaded_data.head())
    except Exception as e:
        st.error(f"Failed to read the data file: {e}")

if dict_file is not None:
    try:
        if dict_file.name.endswith(".csv"):
            dict_df = pd.read_csv(dict_file)
            st.session_state.uploaded_dict = dict_df.to_string()
        else:
            st.session_state.uploaded_dict = dict_file.read().decode("utf-8")
        st.success("Dictionary file uploaded successfully.")
    except Exception as e:
        st.error(f"Failed to read the dictionary file: {e}")

# --- Checkbox for Analysis ---
analyze_data_checkbox = st.checkbox("Analyze CSV Data with AI")

# --- User Chat Input ---
if user_input := st.chat_input("Type your message here..."):
    st.session_state.chat_history.append(("user", user_input))
    st.chat_message("user").markdown(user_input)

    if model:
        try:
            if st.session_state.uploaded_data is not None and analyze_data_checkbox:
                if "analyze" in user_input.lower() or "insight" in user_input.lower():
                    # Generate prompt using data description + dictionary (if any)
                    data_description = st.session_state.uploaded_data.describe().to_string()
                    prompt = f"Analyze the following dataset and provide insights:\n\n{data_description}"

                    if st.session_state.uploaded_dict:
                        prompt += f"\n\nHere is a dictionary of the columns for context:\n{st.session_state.uploaded_dict}"

                    response = model.generate_content(prompt)
                    bot_response = response.text

                else:
                    response = model.generate_content(user_input)
                    bot_response = response.text

            elif not analyze_data_checkbox:
                bot_response = "Data analysis is disabled. Please check 'Analyze CSV Data with AI'."
            else:
                bot_response = "Please upload a CSV data file first."

            st.session_state.chat_history.append(("assistant", bot_response))
            st.chat_message("assistant").markdown(bot_response)

        except Exception as e:
            st.error(f"An error occurred while generating the response: {e}")
    else:
        st.warning("Please configure the Gemini API Key to enable chat responses.")
