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
    st.success("Firebase initialized successfully!")
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

# --- Custom styling including visit counter ---
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
    display: inline-block; /* Ensure it fits within sidebar */
    z-index: 1001; /* Ensure it stays above other elements */
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
</style>
""", unsafe_allow_html=True)

# --- Show the "Please double-click" message if needed ---
if st.session_state.show_double_click_message:
    st.markdown('<div id="floating-message">Please double-click the button.</div>', unsafe_allow_html=True)
    time.sleep(2)
    st.session_state.show_double_click_message = False

# --- Update visit counter ---
def update_visit_counter():
    try:
        current_count = db.child("visit_count").get().val() or 0
        new_count = current_count + 1
        db.child("visit_count").set(new_count)
        st.session_state.visit_count = new_count
    except Exception as e:
        st.error(f"Failed to update visit counter: {str(e)}")

# --- Load visit counter ---
def load_visit_counter():
    try:
        count = db.child("visit_count").get().val() or 0
        st.session_state.visit_count = count
    except Exception as e:
        st.error(f"Failed to load visit counter: {str(e)}")

# --- Load chat history on login ---
def load_chat_history(email: str, token: str) -> List[Tuple[str, str]]:
    if not st.session_state.logged_in:
        return []
    try:
        safe_email = email.replace(".", "_").replace("@", "_")
        chat_data = db.child("users").child(safe_email).child("chat_history").get(token=token).val()
        return chat_data if chat_data else []
    except Exception as e:
        st.warning(f"Failed to load chat history: {str(e)}. Starting with empty history.")
        return []

# --- Save chat history on logout or update ---
def save_chat_history(email: str, chat_history: List[Tuple[str, str]], token: str):
    if not st.session_state.logged_in:
        return
    try:
        safe_email = email.replace(".", "_").replace("@", "_")
        db.child("users").child(safe_email).child("chat_history").set(chat_history, token)
    except Exception as e:
        st.error(f"Failed to save chat history: {str(e)}")

# --- Initial load of visit counter ---
load_visit_counter()

# --- Login Page ---
if not st.session_state.logged_in:
    st.title("🔐 SATyr Login")
    st.markdown("Welcome to SATyr. Please log in or sign up to continue.")

    email = st.text_input("📧 Email")
    password = st.text_input("🔒 Password", type="password")

    # Email validation
    email_valid = "@" in email if email else False
    if email and not email_valid:
        st.error("Please enter a valid email address containing '@'.")

    # Password validation
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
            if login:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.user_name = email.split("@")[0]
                # Get authentication token
                user_info = auth.get_account_info(user['idToken'])
                st.session_state.user_token = user['idToken']
                # Load chat history after login
                st.session_state.chat_history = load_chat_history(email, st.session_state.user_token)
                # Update visit counter
                update_visit_counter()
                st.success(f"Logged in as {st.session_state.user_name}")
            elif signup:
                user = auth.create_user_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.user_name = email.split("@")[0]
                # Get authentication token after signup
                login_response = auth.sign_in_with_email_and_password(email, password)
                st.session_state.user_token = login_response['idToken']
                # Update visit counter
                update_visit_counter()
                st.success(f"Account created for {st.session_state.user_name}")
            st.session_state.show_double_click_message = True
            time.sleep(0.5)
            st.rerun()
        except Exception as e:
            if "EMAIL_EXISTS" in str(e):
                st.error("This email is already registered. Please log in or use a different email.")
            else:
                st.error(f"Authentication failed: {str(e)}")

# --- Sidebar (only visible after login) ---
if st.session_state.logged_in:
    with st.sidebar:
        st.title("🧠 SATyr")
        # Display visit counter below SATyr logo
        st.markdown(f'<div id="visit-counter">Visits: {st.session_state.visit_count}</div>', unsafe_allow_html=True)
        st.subheader("Conversations")

        if st.session_state.chat_history:
            for idx, (user_msg, ai_msg) in enumerate(st.session_state.chat_history):
                label = f"{user_msg[:20]}..."
                if st.button(label, key=f"history_{idx}"):
                    st.session_state.reply_to_index = idx
        else:
            st.info("No conversations yet.")

        if st.button("🔄 New Session"):
            st.session_state.chatbot.reset()
            st.session_state.chat_history = []
            st.session_state.reply_to_index = None
            st.rerun()

        if st.button("🚪 Logout"):
            save_chat_history(st.session_state.user_email, st.session_state.chat_history, st.session_state.user_token)  # Save history on logout
            st.session_state.logged_in = False
            st.session_state.chatbot.reset()
            st.session_state.chat_history = []
            st.session_state.reply_to_index = None
            st.session_state.user_name = None
            st.session_state.user_email = None
            st.session_state.user_token = None
            st.rerun()

# --- Main Chat UI ---
if st.session_state.logged_in:
    st.title("SATyr - Your AI Assistant")

    if st.session_state.user_name:
        st.session_state.chatbot.user_name = st.session_state.user_name

        with st.form("chat_form", clear_on_submit=True):
            default_prompt = "Type your message here..." if st.session_state.reply_to_index is None else f"Replying to: {st.session_state.chat_history[st.session_state.reply_to_index][1][:50]}..."
            user_input = st.text_input("💬 Your message:", placeholder=default_prompt)
            submitted = st.form_submit_button("Send")

        if submitted and user_input:
            reply_context = None
            if st.session_state.reply_to_index is not None:
                reply_context = st.session_state.chat_history[st.session_state.reply_to_index][1]
            ai_response = st.session_state.chatbot.send_request(user_input, reply_to=reply_context)
            st.session_state.chat_history.append((user_input, ai_response))
            # Save updated chat history
            save_chat_history(st.session_state.user_email, st.session_state.chat_history, st.session_state.user_token)
            st.session_state.reply_to_index = None

        # Display chat history
        for idx, (user_msg, ai_msg) in enumerate(reversed(st.session_state.chat_history)):
            display_idx = len(st.session_state.chat_history) - idx - 1
            st.markdown(f"**🧑 {st.session_state.user_name}:** {user_msg}")
            st.markdown(f"**🤖 SATyr:** {ai_msg}")
            if st.button("↩️ Reply", key=f"reply_{display_idx}"):
                st.session_state.reply_to_index = display_idx
            st.divider()
