import streamlit as st
import http.client
import json
from typing import Optional, Dict, List, Tuple
import time
from dotenv import load_dotenv
import os
import pyrebase

# Set page config as the first Streamlit command
st.set_page_config(page_title="SATyr", page_icon="🧠", layout="wide")

# Load environment variables from .env file
load_dotenv()

# Firebase configuration with fallback for missing databaseURL
firebase_config = {
    "apiKey": os.getenv("API_KEY", ""),
    "authDomain": os.getenv("AUTH_DOMAIN", ""),
    "projectId": os.getenv("PROJECT_ID", ""),
    "storageBucket": os.getenv("STORAGE_BUCKET", ""),
    "messagingSenderId": os.getenv("MESSAGING_SENDER_ID", ""),
    "appId": os.getenv("APP_ID", ""),
    "measurementId": os.getenv("MEASUREMENT_ID", ""),
    "databaseURL": os.getenv("DATABASE_URL", "")  # Should be https://satyr-fe4f3-default-rtdb.firebaseio.com
}

# Initialize Firebase with error handling
try:
    firebase = pyrebase.initialize_app(firebase_config)
    auth = firebase.auth()
    db = firebase.database()  # Initialize the database
except Exception as e:
    st.error(f"Failed to initialize Firebase: {str(e)}")
    st.stop()

# AI Client
class SATyrAI:
    def __init__(self):
        self.api_key = "rzZknlckhFldf2YV2AcpHlxmknkcL7Bo"
        self.domain = "km-pfrdhsi"
        self.base_url = "api.personal.ai"
        self.session_id = None
        self.user_name = None
        self.context = None
        self.conn = http.client.HTTPSConnection(self.base_url)

    def _create_payload(self, text: str, context: Optional[str] = None) -> Dict:
        payload = {
            "Text": text,
            "DomainName": self.domain,
            "UserName": self.user_name or "Guest"
        }
        if self.session_id:
            payload["SessionId"] = self.session_id
        if context:
            payload["Context"] = context
        return payload

    def send_request(self, text: str, reply_to: Optional[str] = None) -> str:
        try:
            payload = json.dumps(self._create_payload(text, context=reply_to))
            headers = {
                'Content-Type': 'application/json',
                'x-api-key': self.api_key
            }

            self.conn.request("POST", "/v1/message", payload, headers)
            response = self.conn.getresponse()

            if response.status == 200:
                data = json.loads(response.read().decode())
                self.session_id = data.get("SessionId", self.session_id)
                self.context = data.get("ai_message")
                return self.context
            return f"[Error] {response.status} - {response.reason}"

        except Exception as e:
            return f"[Network Error] {str(e)}"

    def reset(self):
        self.session_id = None
        self.context = None

# --- Session State Init ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "chatbot" not in st.session_state:
    st.session_state.chatbot = SATyrAI()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "user_name" not in st.session_state:
    st.session_state.user_name = None

if "reply_to_index" not in st.session_state:
    st.session_state.reply_to_index = None

if "show_double_click_message" not in st.session_state:
    st.session_state.show_double_click_message = False

if "user_email" not in st.session_state:
    st.session_state.user_email = None

if "user_token" not in st.session_state:
    st.session_state.user_token = None

if "visit_count" not in st.session_state:
    st.session_state.visit_count = 0

# --- Custom styling including visit counter, heart icon, buttons, and logo ---
st.markdown("""
<style>
body {
    background-color: #202123;
    color: #ececf1;
}
.sidebar .sidebar-content {
    background-color: #171717;
}
.block-container {
    padding: 2rem 2rem 2rem;
}
input, textarea {
    background-color: #2d2d30 !important;
    color: white !important;
}

/* Visit counter below SATyr logo in sidebar */
#visit-counter {
    position: relative;
    background-color: #4CAF50;
    color: white;
    padding: 5px 10px;
    border-radius: 5px;
    font-size: 14px;
    margin-top: 5px;
    display: inline-block;
    z-index: 1001;
}

/* Heart icon at the bottom left of the screen */
#heart-icon {
    position: fixed;
    bottom: 10px;
    left: 10px;
    font-size: 30px;
    color: #ff4d4d; /* Red color for heart */
    opacity: 0.5; /* 50% visibility */
    z-index: 1000;
    display: none; /* Hidden by default */
}

/* Show heart icon only when sidebar is visible (not collapsed) */
[data-testid="stSidebar"]:not([style*="width: 0px"]) ~ #heart-icon {
    display: block;
}

/* Floating message at the bottom */
#floating-message {
    position: fixed;
    bottom: 10px;
    left: 50%;
    transform: translateX(-50%);
    background-color: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 10px;
    border-radius: 5px;
    display: none;
    z-index: 1000;
}

/* General button styling */
.stButton > button {
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.2s ease;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    width: 100%; /* Ensure buttons take full container width */
}

/* Primary buttons (Login, Sign Up, Send) */
div[data-testid="stHorizontalBlock"] .stButton > button,
form .stButton > button {
    background-color: #4CAF50; /* Green to match visit counter */
    color: white;
}
div[data-testid="stHorizontalBlock"] .stButton > button:hover,
form .stButton > button:hover {
    background-color: #45a049; /* Slightly darker green */
    transform: scale(1.05);
}
div[data-testid="stHorizontalBlock"] .stButton > button:active,
form .stButton > button:active {
    background-color: #3d8b40; /* Darker on click */
    transform: scale(0.98);
}

/* Secondary buttons (New Session, Logout, Reply) */
.stSidebar .stButton > button:not([id*="history"]),
div:not([data-testid="stHorizontalBlock"]):not([id*="form"]) .stButton > button {
    background-color: #555555; /* Neutral gray */
    color: white;
}
.stSidebar .stButton > button:not([id*="history"]):hover,
div:not([data-testid="stHorizontalBlock"]):not([id*="form"]) .stButton > button:hover {
    background-color: #666666; /* Lighter gray */
    transform: scale(1.05);
}
.stSidebar .stButton > button:not([id*="history"]):active,
div:not([data-testid="stHorizontalBlock"]):not([id*="form"]) .stButton > button:active {
    background-color: #4a4a4a; /* Darker gray */
    transform: scale(0.98);
}

/* Conversation history buttons in sidebar */
.stSidebar .stButton[id*="history"] > button {
    background-color: #2d2d30; /* Matches input fields */
    color: #ece
