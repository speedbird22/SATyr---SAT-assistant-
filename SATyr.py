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

# Initialize session state for splash screen
if "splash_shown" not in st.session_state:
    st.session_state.splash_shown = False

# Display splash screen only if not shown yet, using same logo.jpg as sidebar
if not st.session_state.splash_shown:
    with st.container():
        st.markdown(
            """
            <style>
            #splash-screen {
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                background-color: white;
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 9999;
            }
            .splash-logo {
                max-width: 200px; /* Larger for splash screen */
                height: auto;
                image-rendering: -webkit-optimize-contrast;
                image-rendering: -moz-crisp-edges;
                image-rendering: crisp-edges;
            }
            </style>
            <div id="splash-screen">
            """,
            unsafe_allow_html=True
        )
        # Verify logo.jpg exists and display it
        try:
            st.image("logo.jpg", width=200, output_format="auto", clamp=True, use_column_width=False)
        except FileNotFoundError:
            st.error("logo.jpg not found in project folder. Please ensure it’s in the same directory as this script.")
        st.markdown(
            """
            </div>
            <script>
                setTimeout(function() {
                    var splash = document.getElementById('splash-screen');
                    if (splash) {
                        splash.style.display = 'none';
                    }
                }, 3000);
            </script>
            """,
            unsafe_allow_html=True
        )
    # Mark splash as shown without rerun to avoid refresh issues
    st.session_state.splash_shown = True
    # Debug: Confirm splash code ran
    # st.write("(Debug: Splash screen code executed)")  # Uncomment to verify

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
st.markdown(
    """
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
    #heart-icon {
        position: fixed;
        bottom: 10px;
        left: 10px;
        font-size: 30px;
        color: #ff4d4d;
        opacity: 0.5;
        z-index: 1000;
        display: none;
    }
    [data-testid="stSidebar"]:not([style*="width: 0px"]) ~ #heart-icon {
        display: block;
    }
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
    .stButton > button {
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 14px;
        font-weight: 500;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        width: 100%;
    }
    div[data-testid="stHorizontalBlock"] .stButton > button,
    form .stButton > button {
        background-color: #4CAF50;
        color: white;
    }
    div[data-testid="stHorizontalBlock"] .stButton > button:hover,
    form .stButton > button:hover {
        background-color: #45a049;
        transform: scale(1.05);
    }
    div[data-testid="stHorizontalBlock"] .stButton > button:active,
    form .stButton > button:active {
        background-color: #3d8b40;
        transform: scale(0.98);
    }
    .stSidebar .stButton > button:not([id*="history"]),
    div:not([data-testid="stHorizontalBlock"]):not([id*="form"]) .stButton > button {
        background-color: #555555;
        color: white;
    }
    .stSidebar .stButton > button:not([id*="history"]):hover,
    div:not([data-testid="stHorizontalBlock"]):not([id*="form"]) .stButton > button:hover {
        background-color: #666666;
        transform: scale(1.05);
    }
    .stSidebar .stButton > button:not([id*="history"]):active,
    div:not([data-testid="stHorizontalBlock"]):not([id*="form"]) .stButton > button:active {
        background-color: #4a4a4a;
        transform: scale(0.98);
    }
    .stSidebar .stButton[id*="history"] > button {
        background-color: #2d2d30;
        color: #ececf1;
        font-size: 13px;
        padding: 6px 12px;
    }
    .stSidebar .stButton[id*="history"] > button:hover {
        background-color: #3a3a3d;
        transform: scale(1.02);
    }
    .stSidebar .stButton[id*="history"] > button:active {
        background-color: #262629;
        transform: scale(0.98);
    }
    .logo-container {
        display: flex;
        align-items: flex-start; /* Allow margin-top to adjust text position */
        margin-bottom: 10px;
    }
    .logo-image {
        max-width: 50px; /* Downscaled size for sidebar */
        height: auto;
        margin-right: 10px;
        image-rendering: -webkit-optimize-contrast;
        image-rendering: -moz-crisp-edges;
        image-rendering: crisp-edges;
    }
    </style>
    """,
    unsafe_allow_html=True
)

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
        # Display logo beside SATyr text using a flex container for alignment
        st.markdown('<div class="logo-container">', unsafe_allow_html=True)
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image("logo.jpg", clamp=True, output_format="auto")  # Same logo.jpg
        with col2:
            st.markdown('<h1 class="sidebar-title">SATyr</h1>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        # Apply CSS for alignment and updated title size
        st.markdown(
            """
            <style>
            [data-testid="stImage"] img {
                max-width: 50px; /* Downscaled for sidebar */
                height: auto;
                image-rendering: -webkit-optimize-contrast;
                image-rendering: -moz-crisp-edges;
                image-rendering: crisp-edges;
            }
            .logo-container {
                display: flex;
                align-items: flex-start; /* Allow margin-top to adjust text position */
                margin-bottom: 10px;
            }
            div[data-testid="stSidebar"] h1.sidebar-title {
                font-size: 45px !important; /* Current size */
                margin: 0;
                line-height: 1;
                vertical-align: middle; /* Align text vertically with logo */
                margin-top: -15px !important; /* Maintain upward adjustment */
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        # Display visit counter below logo and title
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

    # Add translucent heart emoji at the bottom left of the screen
    st.markdown('<div id="heart-icon">❤️</div>', unsafe_allow_html=True)

# --- Main Chat UI ---
if st.session_state.logged_in:
    st.title("SATyr - ur SAT saviour")  # Updated title

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
