
import os
import re
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# Configure page
st.set_page_config(
    page_title="Krishi Mitra",
    page_icon="🌱",
    layout="centered"
)

st.title("🌱 Krishi Mitra")
st.subheader("AI Farmer Query Support & Advisory Chatbot")

# Initialize Gemini
client = genai.Client(api_key=API_KEY) if API_KEY else None

# Load agricultural dataset
@st.cache_data
def load_data():
    return pd.read_csv(
        "data/agriculture_faq.csv"
    ).fillna("")

data = load_data()

# Language selection
language = st.selectbox(
    "Choose your language / ಭಾಷೆ ಆಯ್ಕೆಮಾಡಿ / भाषा चुनें",
    ["Kannada", "Hindi", "English"]
)

# Language messages
messages = {
    "Kannada": {
        "welcome": "ನಮಸ್ಕಾರ! ನಿಮ್ಮ ಕೃಷಿ ಪ್ರಶ್ನೆಗಳನ್ನು ಕೇಳಿ.",
        "placeholder": "ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಇಲ್ಲಿ ಬರೆಯಿರಿ...",
        "loading": "ಉತ್ತರ ಸಿದ್ಧಪಡಿಸಲಾಗುತ್ತಿದೆ...",
        "error": "ಕ್ಷಮಿಸಿ, ಈಗ ಉತ್ತರ ಪಡೆಯಲು ಸಾಧ್ಯವಾಗುತ್ತಿಲ್ಲ."
    },
    "Hindi": {
        "welcome": "नमस्ते! अपने कृषि संबंधी सवाल पूछें।",
        "placeholder": "अपना सवाल यहां लिखें...",
        "loading": "उत्तर तैयार किया जा रहा है...",
        "error": "क्षमा करें, अभी उत्तर प्राप्त नहीं हो रहा है।"
    },
    "English": {
        "welcome": "Hello! Ask your agriculture-related questions.",
        "placeholder": "Type your farming question here...",
        "loading": "Preparing your answer...",
        "error": "Sorry, an answer is currently unavailable."
    }
}

st.info(messages[language]["welcome"])

# Find matching FAQ
def find_faq(question):

    columns = {
        "Kannada": ("question_kn", "answer_kn"),
        "Hindi": ("question_hi", "answer_hi"),
        "English": ("question_en", "answer_en")
    }

    q_col, a_col = columns[language]

    question_words = set(re.findall(
        r"\w+", question.lower()
    ))

    best_score = 0
    best_answer = ""

    for _, row in data.iterrows():

        faq_words = set(re.findall(
            r"\w+", str(row[q_col]).lower()
        ))

        score = len(question_words & faq_words)

        if score > best_score:
            best_score = score
            best_answer = str(row[a_col])

    return best_answer if best_score > 0 else ""

# Generate AI answer
def get_answer(question):

    faq_answer = find_faq(question)

    if language == "Kannada":
        language_instruction = "Answer in simple Kannada."
    elif language == "Hindi":
        language_instruction = "Answer in simple Hindi."
    else:
        language_instruction = "Answer in simple English."

    if not client:
        return faq_answer or messages[language]["error"]

    prompt = f"""
You are Krishi Mitra, a helpful agricultural assistant.

Farmer question:
{question}

Relevant agricultural FAQ:
{faq_answer if faq_answer else "No matching FAQ found."}

Instructions:
- {language_instruction}
- Give simple, clear and practical advice.
- Do not invent pesticide doses or fertilizer quantities.
- If information is insufficient, ask for crop name,
  location and symptoms.
- Never claim an uncertain diagnosis is confirmed.
- Recommend consulting a local KVK or agriculture
  officer for serious crop problems.
- Do not invent government scheme details.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return response.text or messages[language]["error"]

    except Exception:
        return faq_answer or messages[language]["error"]


# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
question = st.chat_input(
    messages[language]["placeholder"]
)

if question:

    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):

        with st.spinner(messages[language]["loading"]):
            answer = get_answer(question)
            st.write(answer)

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })

# Sidebar
with st.sidebar:
    st.title("🌾 Krishi Mitra")
    st.write("Your multilingual agricultural assistant.")

    st.write("Supported languages:")
    st.write("ಕನ್ನಡ | हिन्दी | English")

    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()
