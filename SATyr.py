import streamlit as st
import http.client
import json
from typing import Optional, Dict, List, Tuple
import time
from dotenv import load_dotenv
import os
import pyrebase

# Set page config
st.set_page_config(page_title="SATyr", page_icon="🧠", layout="wide")

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "chatbot" not in st.session_state:
    st.session_state.chatbot = None  # Initialize later to avoid import issues
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "selected_conversation_index" not in st.session_state:
    st.session_state.selected_conversation_index = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "user_token" not in st.session_state:
    st.session_state.user_token = None
if "refresh_token" not in st.session_state:
    st.session_state.refresh_token = None
if "visit_count" not in st.session_state:
    st.session_state.visit_count = 0

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

# AI Client (unchanged for brevity)
class SATyrAI:
    def __init__(self):
        self.api_key = "rzZknlckhFldf2YV2AcpHlxmknkcL7Bo"
        self.domain = "km-pfrdhsi"
        self.base_url = "api.personal.ai"
        self.session_id = None
        self.user_name = None
        self.context = None
        self.conn = None
        self._connect()

    def _connect(self):
        if self.conn:
            self.conn.close()
        self.conn = http.client.HTTPSConnection(self.base_url, timeout=30)

    def _create_payload(self, text: str, context: Optional[str] = None) -> Dict:
        payload = {
            "Text": text,
            "DomainName": self.domain,
            "UserName": self.user_name or "Guest"
        }
        if self.session_id:
            payload["SessionId"] = self.session_id
        if context and isinstance(context, str) and context.strip():
            payload["Context"] = context
        return payload

    def send_request(self, text: str, context: Optional[str] = None) -> str:
        if not text or not isinstance(text, str) or not text.strip():
            return "[Error] Invalid or empty input text"
        try:
            payload = json.dumps(self._create_payload(text, context))
            headers = {
                'Content-Type': 'application/json',
                'x-api-key': self.api_key
            }
            self._connect()
            self.conn.request("POST", "/v1/message", payload, headers)
            response = self.conn.getresponse()
            response_data = response.read().decode()
            if response.status == 200:
                try:
                    data = json.loads(response_data)
                    self.session_id = data.get("SessionId", self.session_id)
                    self.context = data.get("ai_message", "[Error] No AI message in response")
                    return self.context
                except json.JSONDecodeError:
                    return f"[Error] Invalid JSON response: {response_data}"
            return f"[Error] API request failed: {response.status} - {response.reason}"
        except Exception as e:
            return f"[Error] Network or API error: {str(e)}"
        finally:
            self._connect()

    def reset(self):
        self.session_id = None
        self.context = None
        self._connect()

# Initialize chatbot
if st.session_state.chatbot is None:
    st.session_state.chatbot = SATyrAI()

# Helper functions
def save_refresh_token(email: str, refresh_token: str, token: str):
    try:
        safe_email = email.replace(".", "_").replace("@", "_")
        db.child("users").child(safe_email).set({
            "email": email,
            "refresh_token": refresh_token
        }, token)
    except Exception as e:
        st.warning(f"Failed to save refresh token: {str(e)}.")

def load_refresh_token(email: str) -> Optional[str]:
    try:
        safe_email = email.replace(".", "_").replace("@", "_")
        data = db.child("users").child(safe_email).get().val()
        if data and "refresh_token" in data:
            return data["refresh_token"]
        return None
    except Exception as e:
        st.warning(f"Failed to load refresh token: {str(e)}.")
        return None

def load_user_email() -> Optional[str]:
    try:
        users = db.child("users").get().val()
        if users:
            for safe_email, data in users.items():
                if "email" in data:
                    return data["email"]
        return None
    except Exception as e:
        st.warning(f"Failed to load user email: {str(e)}.")
        return None

def load_chat_history(email: str, token: str) -> List[Tuple[str, str]]:
    if not st.session_state.logged_in or not email or not token:
        return []
    try:
        safe_email = email.replace(".", "_").replace("@", "_")
        chat_data = db.child("users").child(safe_email).child("chat_history").get(token=token).val()
        if isinstance(chat_data, list):
            return [(str(item[0]), str(item[1])) for item in chat_data if isinstance(item, list) and len(item) == 2]
        return []
    except Exception as e:
        st.warning(f"Failed to load chat history: {str(e)}.")
        return []

def save_chat_history(email: str, chat_history: List[Tuple[str, str]], token: str):
    if not st.session_state.logged_in or not email or not token:
        return
    try:
        safe_email = email.replace(".", "_").replace("@", "_")
        serialized_history = [[user_msg, ai_msg] for user_msg, ai_msg in chat_history]
        db.child("users").child(safe_email).child("chat_history").set(serialized_history, token)
    except Exception as e:
        st.warning(f"Failed to save chat history: {str(e)}.")

def try_auto_login():
    st.session_state.chat_history = []
    st.session_state.selected_conversation_index = None
    if not st.session_state.user_email:
        st.session_state.user_email = load_user_email()
    if st.session_state.user_email:
        st.session_state.refresh_token = load_refresh_token(st.session_state.user_email)
    if st.session_state.user_email and st.session_state.refresh_token:
        try:
            user = auth.refresh(st.session_state.refresh_token)
            st.session_state.user_token = user['idToken']
            st.session_state.logged_in = True
            st.session_state.user_name = st.session_state.user_email.split("@")[0]
            st.session_state.chat_history = load_chat_history(st.session_state.user_email, st.session_state.user_token)
            return True
        except Exception as e:
            st.warning(f"Auto-login failed: {str(e)}. Please log in manually.")
            st.session_state.logged_in = False
            st.session_state.refresh_token = None
            st.session_state.user_email = None
            st.session_state.user_token = None
            st.session_state.chat_history = []
    return False

# Login page
if not st.session_state.logged_in:
    st.title("🔐 SATyr Login")
    st.markdown("Welcome to SATyr. Please log in or sign up to continue.")
    email = st.text_input("📧 Email")
    password = st.text_input("🔒 Password", type="password")
    email_valid = "@" in email if email else False
    if email and not email_valid:
        st.error("Please enter a valid email address containing '@'.")
    password_valid = len(password) >= 6 if password else False
    if password and not password_valid:
        st.error("Password must be at least 6 characters long.")
    col1, col2 = st.columns(2)
    with col1:
        login = st.button("🔓 Login")
    with col2:
        signup = st.button("📝 Sign Up")
    if (login or signup) and email_valid and password_valid:
        try:
            st.session_state.chat_history = []
            st.session_state.selected_conversation_index = None
            if login:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.user_name = email.split("@")[0]
                st.session_state.user_token = user['idToken']
                st.session_state.refresh_token = user['refreshToken']
                save_refresh_token(email, user['refreshToken'], user['idToken'])
                st.session_state.chat_history = load_chat_history(email, user['idToken'])
                st.success(f"Logged in as {st.session_state.user_name}")
            elif signup:
                user = auth.create_user_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.user_name = email.split("@")[0]
                login_response = auth.sign_in_with_email_and_password(email, password)
                st.session_state.user_token = login_response['idToken']
                st.session_state.refresh_token = login_response['refreshToken']
                save_refresh_token(email, login_response['refreshToken'], login_response['idToken'])
                st.session_state.chat_history = []
                st.success(f"Account created for {st.session_state.user_name}")
            st.rerun()
        except Exception as e:
            error_msg = str(e)
            if "EMAIL_EXISTS" in error_msg:
                st.error("This email is already registered. Please log in or use a different email.")
            elif "INVALID_LOGIN_CREDENTIALS" in error_msg:
                st.error("Incorrect email or password.")
            else:
                st.error(f"Authentication failed: {error_msg}")

# Sidebar and main UI (simplified for brevity)
if st.session_state.logged_in:
    with st.sidebar:
        st.subheader("Conversations")
        if st.session_state.chat_history:
            for idx, (user_msg, _) in enumerate(st.session_state.chat_history):
                label = f"{user_msg[:20]}..." if len(user_msg) > 20 else user_msg
                if st.button(label, key=f"history_{idx}"):
                    st.session_state.selected_conversation_index = idx
                    st.rerun()
        if st.button("🚪 Logout"):
            try:
                if st.session_state.chat_history and st.session_state.user_email and st.session_state.user_token:
                    save_chat_history(st.session_state.user_email, st.session_state.chat_history, st.session_state.user_token)
                st.session_state.logged_in = False
                st.session_state.chatbot.reset()
                st.session_state.chat_history = []
                st.session_state.selected_conversation_index = None
                st.session_state.user_name = None
                st.session_state.user_email = None
                st.session_state.user_token = None
                st.session_state.refresh_token = None
                st.rerun()
            except Exception as e:
                st.error(f"Logout failed: {str(e)}")
