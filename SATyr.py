import streamlit as st
import http.client
import json
from typing import Optional, Dict, List, Tuple
import time
from dotenv import load_dotenv
import os
import pyrebase
import requests
from colors import COLORS, LIGHT_MODE_COLORS

# Set page config
st.set_page_config(page_title="SATyr", page_icon="🧠", layout="wide")

# Initialize session state
if "splash_shown" not in st.session_state:
    st.session_state.splash_shown = False
if "show_settings" not in st.session_state:
    st.session_state.show_settings = False
if "light_mode" not in st.session_state:
    st.session_state.light_mode = False
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "chatbot" not in st.session_state:
    st.session_state.chatbot = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "selected_conversation_index" not in st.session_state:
    st.session_state.selected_conversation_index = None
if "show_double_click_message" not in st.session_state:
    st.session_state.show_double_click_message = False
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "user_token" not in st.session_state:
    st.session_state.user_token = None
if "visit_count" not in st.session_state:
    st.session_state.visit_count = 0
if "signup_clicked" not in st.session_state:
    st.session_state.signup_clicked = False
if "signup_email" not in st.session_state:
    st.session_state.signup_email = ""
if "signup_password" not in st.session_state:
    st.session_state.signup_password = ""
if "pending_verification" not in st.session_state:
    st.session_state.pending_verification = False
if "temp_user_id" not in st.session_state:
    st.session_state.temp_user_id = None
if "temp_username" not in st.session_state:
    st.session_state.temp_username = None

# Display splash screen
if not st.session_state.splash_shown:
    with st.container():
        st.markdown(
            f"""
            <style>
            #splash-screen {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                background-color: {COLORS['splash_screen']};
                z-index: 999999;
                animation: fadeOut 0.25s ease-out 0.75s forwards;
            }}
            @keyframes fadeOut {{
                from {{ opacity: 1; }}
                to {{ opacity: 0; visibility: hidden; }}
            }}
            </style>
            <div id="splash-screen"></div>
            """,
            unsafe_allow_html=True
        )
    time.sleep(1)
    st.session_state.splash_shown = True
    st.rerun()

# Load environment variables
load_dotenv()

# Firebase configuration
firebase_config = {
    "apiKey": os.getenv("API_KEY", ""),
    "authDomain": os.getenv("AUTH_DOMAIN", ""),
    "projectId": os.getenv("PROJECT_ID", ""),
    "storageBucket": os.getenv("STORAGE_BUCKET", ""),
    "messagingSenderId": os.getenv("MESSAGING_SENDER_ID", ""),
    "appId": os.getenv("APP_ID", ""),
    "measurementId": os.getenv("MEASUREMENT_ID", ""),
    "databaseURL": os.getenv("DATABASE_URL", "")
}

# Initialize Firebase
try:
    firebase = pyrebase.initialize_app(firebase_config)
    auth = firebase.auth()
    db = firebase.database()
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
        self.conn = http.client.HTTPSConnection(self.base_url, timeout=30)

    def __del__(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()

    def _create_payload(self, text: str, context: Optional[str] = None) -> Dict:
        payload = {
            "Text": text,
            "DomainName": self.domain,
            "UserName": self.user_name or "Guest"
        }
        if context:
            payload["Context"] = context
        if self.session_id:
            payload["SessionId"] = self.session_id
        return payload

    def _log_api_error(self, status: int, reason: str, response_body: str) -> str:
        error_details = (
            f"API Error: {status} {reason}\n"
            f"Response: {response_body[:1000]}\n"
            f"Domain: {self.domain}\n"
            f"API Key (first 4 chars): {self.api_key[:4]}...\n"
            "Troubleshooting:\n"
            "- Check if API key is valid and not expired.\n"
            "- Verify domain is correct for your Personal AI account.\n"
            "- Ensure network connectivity and no firewall is blocking api.personal.ai.\n"
            "- Check for rate limits (HTTP 429) or server issues (HTTP
