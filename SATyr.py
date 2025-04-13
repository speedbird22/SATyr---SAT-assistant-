import streamlit as st
import http.client
import json
from typing import Optional, Dict, List, Tuple
import time
from dotenv import load_dotenv
import os
import pyrebase
from colors import COLORS  # Import colors

# Set page config
st.set_page_config(page_title="SATyr", page_icon="🧠", layout="wide")

# Initialize session state for splash screen
if "splash_shown" not in st.session_state:
    st.session_state.splash_shown = False

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

# --- Session State Init ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "chatbot" not in st.session_state:
    st.session_state.chatbot = SATyrAI()

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

if "refresh_token" not in st.session_state:
    st.session_state.refresh_token = None

if "visit_count" not in st.session_state:
    st.session_state.visit_count = 0

# --- Helper Functions ---
def save_refresh_token(email: str, refresh_token: str, token: str):
    try:
        safe_email = email.replace(".", "_").replace("@", "_")
        db.child("users").child(safe_email).set({
            "email": email,
            "refresh_token": refresh_token,
            "chat_history": st.session_state.chat_history
        }, token)
    except Exception as e:
        st.warning(f"Failed to save refresh token: {str(e)}. Auto-login may not work.")

def load_user_data(email: str, token: str) -> tuple:
    try:
        safe_email = email.replace(".", "_").replace("@", "_")
        data = db.child("users").child(safe_email).get(token=token).val()
        if data:
            return data.get("refresh_token"), data.get("chat_history", [])
        return None, []
    except Exception as e:
        st.warning(f"Failed to load user data: {str(e)}.")
        return None, []

def try_auto_login():
    if not st.session_state.user_email:
        return False

    refresh_token, chat_history = load_user_data(st.session_state.user_email, None)
    st.session_state.refresh_token = refresh_token

    if st.session_state.user_email and st.session_state.refresh_token:
        try:
            user = auth.refresh(st.session_state.refresh_token)
            st.session_state.user_token = user['idToken']
            st.session_state.logged_in = True
            st.session_state.user_name = st.session_state.user_email.split("@")[0]
            st.session_state.chat_history = chat_history
            update_visit_counter()
            return True
        except Exception as e:
            st.warning(f"Auto-login failed: {str(e)}. Please log in manually.")
            st.session_state.logged_in = False
            st.session_state.refresh_token = None
            st.session_state.user_email = None
            st.session_state.user_token = None
            st.session_state.chat_history = []
    return False

def update_visit_counter():
    try:
        current_count = db.child("visit_count").get().val() or 0
        new_count = current_count + 1
        db.child("visit_count").set(new_count)
        st.session_state.visit_count = new_count
    except Exception as e:
        st.warning(f"Failed to update visit counter: {str(e)}.")

def load_visit_counter():
    try:
        count = db.child("visit_count").get().val() or 0
        st.session_state.visit_count = count
    except Exception as e:
        st.warning(f"Failed to load visit counter: {str(e)}.")

def save_chat_history(email: str, chat_history: List[Tuple[str, str]], token: str):
    try:
        safe_email = email.replace(".", "_").replace("@", "_")
        db.child("users").child(safe_email).update({"chat_history": chat_history}, token)
        st.session_state.chat_history = chat_history  # Sync session state
    except Exception as e:
        st.error(f"Failed to save chat history: {str(e)}.")

# --- Initial load of visit counter ---
load_visit_counter()

# --- Try auto-login ---
if not st.session_state.logged_in:
    try_auto_login()

# --- Custom styling ---
st.markdown(
    f"""
    <style>
    body {{
        background-color: {COLORS['app_background']};
        color: {COLORS['text_color']};
    }}
    .sidebar .sidebar-content {{
        background-color: {COLORS['sidebar_background']};
    }}
    .block-container {{
        padding: 2rem 2rem 2rem;
    }}
    input, textarea {{
        background-color: {COLORS['input_background']} !important;
        color: white !important;
    }}
    #visit-counter {{
        position: relative;
        background-color: {COLORS['visit_counter_background']};
        color: {COLORS['visit_counter_text']};
        padding: 5px 10px;
        border-radius: 5px;
        font-size: 14px;
        margin-top: 5px;
        display: inline-block;
        z-index: 1001;
    }}
    #floating-message {{
        position: fixed;
        bottom: 10px;
        left: 50%;
        transform: translateX(-50%);
        background-color: {COLORS['floating_message_background']};
        color: white;
        padding: 10px;
        border-radius: 5px;
        display: none;
        z-index: 1000;
    }}
    .stButton > button {{
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 14px;
        font-weight: 500;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        width: 100%;
    }}
    div[data-testid="stHorizontalBlock"] .stButton > button,
    form .stButton > button {{
        background-color: {COLORS['button_form_default']};
        color: white;
    }}
    div[data-testid="stHorizontalBlock"] .stButton > button:hover,
    form .stButton > button:hover {{
        background-color: {COLORS['button_form_hover']};
        transform: scale(1.05);
    }}
    div[data-testid="stHorizontalBlock"] .stButton > button:active,
    form .stButton > button:active {{
        background-color: {COLORS['button_form_active']};
        transform: scale(0.98);
    }}
    .stSidebar .stButton > button:not([id*="history"]),
    div:not([data-testid="stHorizontalBlock"]):not([id*="form"]) .stButton > button {{
        background-color: {COLORS['button_sidebar_default']};
        color: white;
    }}
    .stSidebar .stButton > button:not([id*="history"]):hover,
    div:not([data-testid="stHorizontalBlock"]):not([id*="form"]) .stButton > button:hover {{
        background-color: {COLORS['button_sidebar_hover']};
        transform: scale(1.05);
    }}
    .stSidebar .stButton > button:not([id*="history"]):active,
    div:not([data-testid="stHorizontalBlock"]):not([id*="form"]) .stButton > button:active {{
        background-color: {COLORS['button_sidebar_active']};
        transform: scale(0.98);
    }}
    .stSidebar .stButton[id*="history"] > button {{
        background-color: {COLORS['button_history_default']};
        color: {COLORS['text_color']};
        font-size: 13px;
        padding: 6px 12px;
    }}
    .stSidebar .stButton[id*="history"] > button:hover {{
        background-color: {COLORS['button_history_hover']};
        transform: scale(1.02);
    }}
    .stSidebar .stButton[id*="history"] > button:active {{
        background-color: {COLORS['button_history_active']};
        transform: scale(0.98);
    }}
    .logo-container {{
        display: flex;
        align-items: flex-start;
        margin-bottom: 10px;
    }}
    .logo-image {{
        max-width: 50px;
        height: auto;
        margin-right: 10px;
        image-rendering: -webkit-optimize-contrast;
        image-rendering: -moz-crisp-edges;
        image-rendering: crisp-edges;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# --- Show double-click message ---
if st.session_state.show_double_click_message:
    st.markdown('<div id="floating-message">Please double-click the button.</div>', unsafe_allow_html=True)
    time.sleep(2)
    st.session_state.show_double_click_message = False

# --- Main App Logic ---
if not st.session_state.logged_in:
    # Login Page
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

    with st.expander("Forgot Password?"):
        reset_email = st.text_input("📧 Enter your email to reset password", key="reset_email")
        reset_button = st.button("🔄 Send Reset Email")
        if reset_button and reset_email:
            if "@" not in reset_email:
                st.error("Please enter a valid email address containing '@'.")
            else:
                try:
                    auth.send_password_reset_email(reset_email)
                    st.success("Password reset email sent! Check your inbox.")
                except Exception as e:
                    error_msg = str(e)
                    if "EMAIL_NOT_FOUND" in error_msg:
                        st.error("No account found with this email.")
                    elif "INVALID_EMAIL" in error_msg:
                        st.error("Invalid email address.")
                    else:
                        st.error(f"Failed to send reset email: {error_msg}")

    if (login or signup) and email_valid and password_valid:
        try:
            if login:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.user_name = email.split("@")[0]
                st.session_state.user_token = user['idToken']
                st.session_state.refresh_token = user['refreshToken']
                save_refresh_token(email, user['refreshToken'], user['idToken'])
                _, chat_history = load_user_data(email, user['idToken'])
                st.session_state.chat_history = chat_history
                update_visit_counter()
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
                update_visit_counter()
                st.success(f"Account created for {st.session_state.user_name}")
            st.session_state.show_double_click_message = True
            time.sleep(0.5)
            st.rerun()
        except Exception as e:
            error_msg = str(e)
            if "EMAIL_EXISTS" in error_msg:
                st.error("This email is already registered. Please log in or use a different email.")
            elif "INVALID_LOGIN_CREDENTIALS" in error_msg:
                st.error("Incorrect email or password.")
            else:
                st.error(f"Authentication failed: {error_msg}")
else:
    # Sidebar
    with st.sidebar:
        st.markdown('<div class="logo-container">', unsafe_allow_html=True)
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image("logo.jpg", clamp=True, output_format="auto")
        with col2:
            st.markdown('<h1 class="sidebar-title">SATyr</h1>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown(
            """
            <style>
            [data-testid="stImage"] img {
                max-width: 50px;
                height: auto;
                image-rendering: -webkit-optimize-contrast;
                image-rendering: -moz-crisp-edges;
                image-rendering: crisp-edges;
            }
            .logo-container {
                display: flex;
                align-items: flex-start;
                margin-bottom: 10px;
            }
            div[data-testid="stSidebar"] h1.sidebar-title {
                font-size: 45px !important;
                margin: 0;
                line-height: 1;
                vertical-align: middle;
                margin-top: -15px !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        st.markdown(f'<div id="visit-counter">Visits: {st.session_state.visit_count}</div>', unsafe_allow_html=True)
        st.subheader("Conversations")

        if st.session_state.chat_history:
            for idx, (user_msg, ai_msg) in enumerate(st.session_state.chat_history):
                label = f"{user_msg[:20]}..."
                if st.button(label, key=f"history_{idx}"):
                    st.session_state.selected_conversation_index = idx
                    st.rerun()
        else:
            st.info("No conversations yet.")

        if st.button("🔄 New Session"):
            st.session_state.chatbot.reset()
            st.session_state.selected_conversation_index = None
            st.rerun()

        if st.button("🚪 Logout"):
            if st.session_state.user_email and st.session_state.user_token:
                try:
                    save_chat_history(st.session_state.user_email, st.session_state.chat_history, st.session_state.user_token)
                    # Verify save by reloading
                    _, reloaded_chat_history = load_user_data(st.session_state.user_email, st.session_state.user_token)
                    if reloaded_chat_history != st.session_state.chat_history:
                        st.error("Chat history save verification failed. Reloading from Firebase.")
                        st.session_state.chat_history = reloaded_chat_history
                except Exception as e:
                    st.error(f"Failed to save chat history during logout: {str(e)}. Reloading from Firebase.")
                    _, reloaded_chat_history = load_user_data(st.session_state.user_email, st.session_state.user_token)
                    st.session_state.chat_history = reloaded_chat_history
            st.session_state.clear()
            st.session_state.logged_in = False
            st.success("Logged out successfully!")
            time.sleep(0.5)
            st.rerun()

    # Main Chat UI
    st.title("SATyr - you're SAT saviour")

    if st.session_state.user_name:
        st.session_state.chatbot.user_name = st.session_state.user_name

        if st.session_state.selected_conversation_index is None:
            with st.form("chat_form", clear_on_submit=True):
                user_input = st.text_input("💬 Your message:", placeholder="Type your message here...")
                submitted = st.form_submit_button("Send")

                if submitted and user_input:
                    ai_response = st.session_state.chatbot.send_request(user_input)
                    if ai_response.startswith("[Error]"):
                        st.error(f"Failed to get response: {ai_response}")
                    else:
                        st.session_state.chat_history.append((user_input, ai_response))
                        save_chat_history(st.session_state.user_email, st.session_state.chat_history, st.session_state.user_token)
                        st.session_state.selected_conversation_index = len(st.session_state.chat_history) - 1
                        st.rerun()

        if st.session_state.selected_conversation_index is not None:
            idx = st.session_state.selected_conversation_index
            user_msg, ai_msg = st.session_state.chat_history[idx]
            st.markdown(f"**🧑 {st.session_state.user_name}:** {user_msg}")
            st.markdown(f"**🤖 SATyr:** {ai_msg}")

            with st.form(f"reply_form_{idx}", clear_on_submit=True):
                follow_up_input = st.text_input("💬 Follow-up question:", placeholder="Type your follow-up question here...", key=f"follow_up_{idx}")
                reply_submitted = st.form_submit_button("Reply")

                if reply_submitted and follow_up_input:
                    ai_response = st.session_state.chatbot.send_request(follow_up_input)
                    if ai_response.startswith("[Error]"):
                        st.error(f"Failed to get follow-up response: {ai_response}")
                    else:
                        current_conversation = st.session_state.chat_history[idx]
                        updated_conversation = (
                            f"{current_conversation[0]}\nFollow-up: {follow_up_input}",
                            f"{current_conversation[1]}\nFollow-up response: {ai_response}"
                        )
                        st.session_state.chat_history[idx] = updated_conversation
                        save_chat_history(st.session_state.user_email, st.session_state.chat_history, st.session_state.user_token)
                        st.rerun()

            st.divider()
