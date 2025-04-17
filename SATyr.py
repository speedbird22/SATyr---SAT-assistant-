import streamlit as st
import http.client
import json
from typing import Optional, Dict, List, Tuple
import time
from dotenv import load_dotenv
import os
import pyrebase
import requests

# Define color schemes inline
COLORS = {
    'splash_screen': '#D8AA2A',  # Warm gold
    'app_background': '#000099',  # Navy blue
    'sidebar_background': '#1C2526',  # Slightly brighter shade of navy blue
    'input_background': '#B2984A',  # Dark shade of gold
    'text_color': '#FFFFFF',
    'visit_counter_background': '#D8AA2A80',  # Translucent gold (with 50% opacity)
    'visit_counter_text': '#FFFFFF',  # White
    'floating_message_background': '#B2984A',  # Dark shade of gold
    'button_form_default': '#34C759',  # Exact green from SMS bubble in image
    'button_form_hover': '#2EB74E',  # Slightly darker green
    'button_form_active': '#28A745',  # Even darker green
    'button_sidebar_default': '#007AFF',  # Exact blue from iMessage bubble in image
    'button_sidebar_hover': '#0066CC',  # Slightly darker blue
    'button_sidebar_active': '#0055B3',  # Even darker blue
    'button_history_default': '#2A2A2A',
    'button_history_hover': '#3A3A3A',
    'button_history_active': '#1A1A1A',
    'user_message': '#007AFF',  # Exact blue from iMessage bubble
    'ai_message': '#34C759'  # Exact green from SMS bubble
}

LIGHT_MODE_COLORS = {
    'light_app_background': '#FFFFFF',  # White background
    'light_sidebar_background': '#F5F5F5',  # Soft light gray
    'light_input_background': '#E0E0E0',  # Light gray
    'light_text_color': '#333333',  # Dark gray for contrast
    'light_visit_counter_background': '#E0E0E0',  # Light gray
    'light_visit_counter_text': '#333333',  # Dark gray
    'light_floating_message_background': '#E0E0E0',  # Light gray
    'light_button_form_default': '#FFC107',  # Soft amber, comforting
    'light_button_form_hover': '#FFA000',
    'light_button_form_active': '#FF8F00',
    'light_button_sidebar_default': '#E57373',  # Soft red, comforting
    'light_button_sidebar_hover': '#EF5350',
    'light_button_sidebar_active': '#F44336',
    'light_button_history_default': '#E0E0E0',  # Neutral gray
    'light_button_history_hover': '#D0D0D0',
    'light_button_history_active': '#C0C0C0',
    'light_user_message': '#E57373',  # Soft red, matching light_button_sidebar_default
    'light_ai_message': '#FFC107'  # Soft amber, matching light_button_form_default
}

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
            "- Check for rate limits (HTTP 429) or server issues (HTTP 500)."
        )
        return error_details

    def send_request(self, text: str, context: Optional[str] = None) -> str:
        if not text or not isinstance(text, str) or not text.strip():
            return "[Error] Invalid or empty input text"

        try:
            payload = json.dumps(self._create_payload(text, context))
            headers = {
                'Content-Type': 'application/json',
                'x-api-key': self.api_key
            }

            self.conn.request("POST", "/v1/message", payload, headers)
            response = self.conn.getresponse()
            response_data = response.read().decode()

            if response.status == 200:
                try:
                    data = json.loads(response_data)
                    self.session_id = data.get("SessionId", self.session_id)
                    self.context = data.get("ai_message", "[Error] No AI message in response")
                    return self.context
                except json.JSONDecodeError as e:
                    st.error(f"Invalid JSON response: {response_data[:100]}")
                    return f"[Error] Invalid JSON response: {str(e)}"
            else:
                error_details = self._log_api_error(response.status, response.reason, response_data)
                st.error(error_details)
                return f"[Error] API request failed: {response.status} - {response.reason}"

        except http.client.HTTPException as e:
            st.error(f"HTTP error occurred: {str(e)}")
            return f"[Error] HTTP error: {str(e)}"
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            return f"[Error] Network or API error: {str(e)}"

    def reset(self):
        self.session_id = None
        self.context = None

# Initialize chatbot
if st.session_state.chatbot is None:
    st.session_state.chatbot = SATyrAI()

# Custom styling
st.markdown(
    f"""
    <style>
    body {{
        background-color: {COLORS['app_background'] if not st.session_state.light_mode else LIGHT_MODE_COLORS['light_app_background']};
        color: {COLORS['text_color'] if not st.session_state.light_mode else LIGHT_MODE_COLORS['light_text_color']};
    }}
    .sidebar .sidebar-content {{
        background-color: {COLORS['sidebar_background'] if not st.session_state.light_mode else LIGHT_MODE_COLORS['light_sidebar_background']};
    }}
    .block-container {{
        padding: 2rem 2rem 2rem;
    }}
    input, textarea {{
        background-color: {COLORS['input_background'] if not st.session_state.light_mode else LIGHT_MODE_COLORS['light_input_background']} !important;
        color: {COLORS['text_color'] if not st.session_state.light_mode else LIGHT_MODE_COLORS['light_text_color']} !important;
    }}
    #visit-counter {{
        position: relative;
        background-color: {COLORS['visit_counter_background'] if not st.session_state.light_mode else LIGHT_MODE_COLORS['light_visit_counter_background']};
        color: {COLORS['visit_counter_text'] if not st.session_state.light_mode else LIGHT_MODE_COLORS['light_visit_counter_text']};
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
        background-color: {COLORS['floating_message_background'] if not st.session_state.light_mode else LIGHT_MODE_COLORS['light_floating_message_background']};
        color: {COLORS['text_color'] if not st.session_state.light_mode else LIGHT_MODE_COLORS['light_text_color']};
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
        background-color: {COLORS['button_form_default'] if not st.session_state.light_mode else LIGHT_MODE_COLORS['light_button_form_default']};
        color: {COLORS['text_color'] if not st.session_state.light_mode else LIGHT_MODE_COLORS['light_text_color']};
    }}
    div[data-testid="stHorizontalBlock"] .stButton > button:hover,
    form .stButton > button:hover {{
        background-color: {COLORS['button_form_hover'] if not st.session_state.light_mode else LIGHT_MODE_COLORS['light_button_form_hover']};
        transform: scale(1.05);
    }}
    div[data-testid="stHorizontalBlock"] .stButton > button:active,
    form .stButton > button:active {{
        background-color: {COLORS['button_form_active'] if not st.session_state.light_mode else LIGHT_MODE_COLORS['light_button_form_active']};
        transform: scale(0.98);
    }}
    .stSidebar .stButton > button:not([id*="history"]),
    div:not([data-testid="stHorizontalBlock"]):not([id*="form"]) .stButton > button {{
        background-color: {COLORS['button_sidebar_default'] if not st.session_state.light_mode else LIGHT_MODE_COLORS['light_button_sidebar_default']};
        color: {COLORS['text_color'] if not st.session_state.light_mode else LIGHT_MODE_COLORS['light_text_color']};
    }}
    .stSidebar .stButton > button:not([id*="history"]):hover,
    div:not([data-testid="stHorizontalBlock"]):not([id*="form"]) .stButton > button:hover {{
        background-color: {COLORS['button_sidebar_hover'] if not st.session_state.light_mode else LIGHT_MODE_COLORS['light_button_sidebar_hover']};
        transform: scale(1.05);
    }}
    .stSidebar .stButton > button:not([id*="history"]):active,
    div:not([data-testid="stHorizontalBlock"]):not([id*="form"]) .stButton > button:active {{
        background-color: {COLORS['button_sidebar_active'] if not st.session_state.light_mode else LIGHT_MODE_COLORS['light_button_sidebar_active']};
        transform: scale(0.98);
    }}
    .stSidebar .stButton[id*="history"] > button {{
        background-color: {COLORS['button_history_default'] if not st.session_state.light_mode else LIGHT_MODE_COLORS['light_button_history_default']};
        color: {COLORS['text_color'] if not st.session_state.light_mode else LIGHT_MODE_COLORS['light_text_color']};
        font-size: 13px;
        padding: 6px 12px;
    }}
    .stSidebar .stButton[id*="history"] > button:hover {{
        background-color: {COLORS['button_history_hover'] if not st.session_state.light_mode else LIGHT_MODE_COLORS['light_button_history_hover']};
        transform: scale(1.02);
    }}
    .stSidebar .stButton[id*="history"] > button:active {{
        background-color: {COLORS['button_history_active'] if not st.session_state.light_mode else LIGHT_MODE_COLORS['light_button_history_active']};
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
    .user-bubble {{
        background-color: {COLORS['user_message'] if not st.session_state.light_mode else LIGHT_MODE_COLORS['light_user_message']};
        color: {COLORS['text_color'] if not st.session_state.light_mode else LIGHT_MODE_COLORS['light_text_color']};
        padding: 10px 15px;
        border-radius: 15px 15px 0 15px;
        display: inline-block;
        max-width: 70%;
        margin: 5px 0;
    }}
    .ai-bubble {{
        background-color: {COLORS['ai_message'] if not st.session_state.light_mode else LIGHT_MODE_COLORS['light_ai_message']};
        color: {COLORS['text_color'] if not st.session_state.light_mode else LIGHT_MODE_COLORS['light_text_color']};
        padding: 10px 15px;
        border-radius: 15px 15px 15px 0;
        display: inline-block;
        max-width: 70%;
        margin: 5px 0;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# Show double-click message
if st.session_state.show_double_click_message:
    st.markdown('<div id="floating-message">Please double-click the button.</div>', unsafe_allow_html=True)
    time.sleep(2)
    st.session_state.show_double_click_message = False

# Update visit counter
def update_visit_counter():
    try:
        current_count = db.child("visit_count").get().val() or 0
        new_count = current_count + 1
        db.child("visit_count").set(new_count)
        st.session_state.visit_count = new_count
    except Exception as e:
        st.warning(f"Failed to update visit counter: {str(e)}")

# Load visit counter
def load_visit_counter():
    try:
        count = db.child("visit_count").get().val() or 0
        st.session_state.visit_count = count
    except Exception as e:
        st.warning(f"Failed to load visit counter: {str(e)}")

# Fetch username
def fetch_username(email: str, token: str) -> str:
    try:
        safe_email = email.replace(".", "_").replace("@", "_")
        username = db.child("users").child(safe_email).child("username").get(token=token).val()
        return username if username else None
    except Exception as e:
        st.warning(f"Failed to fetch username: {str(e)}")
        return None

# Load chat history
def load_chat_history(email: str, token: str) -> List[Dict]:
    if not st.session_state.logged_in:
        return []
    try:
        safe_email = email.replace(".", "_").replace("@", "_")
        chat_data = db.child("users").child(safe_email).child("chat_history").get(token=token).val()
        if not chat_data:
            return []
        valid_threads = []
        if isinstance(chat_data, list):
            for idx, item in enumerate(chat_data):
                if isinstance(item, dict) and "initial" in item:
                    initial = item.get("initial")
                    if isinstance(initial, (list, tuple)) and len(initial) == 2 and all(isinstance(s, str) for s in initial):
                        valid_threads.append({
                            "initial": tuple(initial),
                            "follow_ups": [
                                tuple(f) for f in item.get("follow_ups", [])
                                if isinstance(f, (list, tuple)) and len(f) == 2 and all(isinstance(s, str) for s in f)
                            ]
                        })
        return valid_threads
    except Exception as e:
        st.error(f"Failed to load chat history: {str(e)}")
        return []

# Save chat history
def save_chat_history(email: str, chat_history: List[Dict], token: str):
    if not st.session_state.logged_in:
        return
    try:
        safe_email = email.replace(".", "_").replace("@", "_")
        db.child("users").child(safe_email).child("chat_history").set(chat_history, token)
    except Exception as e:
        st.error(f"Failed to save chat history: {str(e)}")

# Clear chat history
def clear_chat_history(email: str, token: str):
    if not st.session_state.logged_in:
        return
    try:
        safe_email = email.replace(".", "_").replace("@", "_")
        db.child("users").child(safe_email).child("chat_history").remove(token)
        st.session_state.chat_history = []
        st.success("Chat history cleared successfully!")
    except Exception as e:
        st.error(f"Failed to clear chat history: {str(e)}")

# Initial load of visit counter
load_visit_counter()

# Login Page
if not st.session_state.logged_in:
    st.title("🔐 SATyr Login")
    st.markdown("Welcome to SATyr. Please log in or sign up to continue.")

    if not st.session_state.pending_verification:
        email = st.text_input("📧 Email", key="email_input")
        password = st.text_input("🔒 Password", type="password", key="password_input")

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

        if login and email_valid and password_valid:
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.user_token = user['idToken']
                username = fetch_username(email, user['idToken'])
                st.session_state.user_name = username if username else email.split("@")[0]
                st.session_state.chat_history = load_chat_history(email, user['idToken'])
                update_visit_counter()
                st.success(f"Logged in as {st.session_state.user_name}")
                st.session_state.show_double_click_message = True
                time.sleep(0.5)
                st.rerun()
            except Exception as e:
                error_msg = str(e)
                if "INVALID_LOGIN_CREDENTIALS" in error_msg:
                    st.error("Incorrect email or password.")
                else:
                    st.error(f"Authentication failed: {error_msg}")

        if signup and email_valid and password_valid:
            st.session_state.signup_clicked = True
            st.session_state.signup_email = email
            st.session_state.signup_password = password

        if st.session_state.signup_clicked:
            custom_username = st.text_input("Choose a username:", key="custom_username")
            if st.button("Confirm Sign-Up", key="confirm_signup"):
                if not custom_username or not custom_username.strip():
                    st.error("Please enter a valid username.")
                else:
                    try:
                        user = auth.create_user_with_email_and_password(
                            st.session_state.signup_email,
                            st.session_state.signup_password
                        )
                        st.session_state.temp_user_id = user['localId']
                        st.session_state.user_token = user['idToken']
                        st.session_state.temp_username = custom_username
                        safe_email = st.session_state.signup_email.replace(".", "_").replace("@", "_")
                        db.child("pending_users").child(safe_email).set(
                            {
                                "username": custom_username,
                                "email": st.session_state.signup_email,
                                "password": st.session_state.signup_password,
                                "temp_user_id": st.session_state.temp_user_id,
                                "created_at": time.time()
                            },
                            token=st.session_state.user_token
                        )
                        verification_response = requests.post(
                            'https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key=' + os.getenv("API_KEY"),
                            json={
                                'requestType': 'VERIFY_EMAIL',
                                'idToken': st.session_state.user_token,
                                'email': st.session_state.signup_email
                            }
                        )
                        if verification_response.status_code == 200:
                            st.info(f"Verification email sent! Click the link in your inbox, then return here to complete sign-up.")
                            st.session_state.pending_verification = True
                        else:
                            st.error(f"Failed to send verification email: {verification_response.text}")
                    except Exception as e:
                        error_msg = str(e)
                        if "EMAIL_EXISTS" in error_msg:
                            st.error("This email is already registered. Please log in or use a different email.")
                        elif "INVALID_EMAIL" in error_msg:
                            st.error("Invalid email format.")
                        elif "WEAK_PASSWORD" in error_msg:
                            st.error("Password is too weak.")
                        else:
                            st.error(f"Failed to initiate sign-up: {str(e)}")

    else:
        try:
            user = auth.sign_in_with_email_and_password(
                st.session_state.signup_email,
                st.session_state.signup_password
            )
            st.session_state.user_token = user['idToken']
            user_info = requests.post(
                'https://identitytoolkit.googleapis.com/v1/accounts:lookup?key=' + os.getenv("API_KEY"),
                json={'idToken': st.session_state.user_token}
            )
            if user_info.status_code == 200:
                user_data = user_info.json()
                if user_data.get('users', [{}])[0].get('emailVerified', False):
                    temp_user_info = user_data.get('users', [{}])[0]
                    temp_local_id = temp_user_info.get('localId')
                    if temp_local_id:
                        delete_response = requests.post(
                            'https://identitytoolkit.googleapis.com/v1/accounts:delete?key=' + os.getenv("API_KEY"),
                            json={'idToken': st.session_state.user_token, 'localId': temp_local_id}
                        )
                        if delete_response.status_code != 200:
                            st.error(f"Failed to delete temporary user: {delete_response.text}")
                            st.stop()
                    final_user = auth.create_user_with_email_and_password(
                        st.session_state.signup_email,
                        st.session_state.signup_password
                    )
                    st.session_state.user_token = final_user['idToken']
                    safe_email = st.session_state.signup_email.replace(".", "_").replace("@", "_")
                    db.child("users").child(safe_email).set(
                        {"username": st.session_state.temp_username},
                        token=st.session_state.user_token
                    )
                    db.child("pending_users").child(safe_email).remove()
                    st.success("Account creation successful! Enjoy mate :) ")
                    st.session_state.signup_clicked = False
                    st.session_state.signup_email = ""
                    st.session_state.signup_password = ""
                    st.session_state.pending_verification = False
                    st.session_state.temp_user_id = None
                    st.session_state.temp_username = None
                    time.sleep(2)
                    st.rerun()
                else:
                    st.info("Please click the verification link in your email and return here to complete sign-up.")
            else:
                st.error(f"Failed to check verification status: {user_info.text}")
        except Exception as e:
            st.error(f"Error checking verification: {str(e)}")

        col1, col2 = st.columns(2)
        with col2:
            if st.button("Cancel Sign-Up", key="cancel_signup"):
                try:
                    safe_email = st.session_state.signup_email.replace(".", "_").replace("@", "_")
                    pending_data = db.child("pending_users").child(safe_email).get().val()
                    if pending_data and pending_data.get("temp_user_id"):
                        requests.post(
                            'https://identitytoolkit.googleapis.com/v1/accounts:delete?key=' + os.getenv("API_KEY"),
                            json={'idToken': st.session_state.user_token, 'localId': pending_data["temp_user_id"]}
                        )
                    db.child("pending_users").child(safe_email).remove()
                    st.info("Sign-up cancelled. Pending data and temporary user removed.")
                    st.session_state.signup_clicked = False
                    st.session_state.signup_email = ""
                    st.session_state.signup_password = ""
                    st.session_state.pending_verification = False
                    st.session_state.temp_user_id = None
                    st.session_state.temp_username = None
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error cancelling sign-up: {str(e)}")

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

# Sidebar
if st.session_state.logged_in:
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
            displayed_threads = 0
            for idx, thread in enumerate(st.session_state.chat_history):
                if not isinstance(thread, dict) or "initial" not in thread:
                    continue
                initial = thread.get("initial")
                if not isinstance(initial, (list, tuple)) or len(initial) < 1 or not isinstance(initial[0], str):
                    continue
                user_msg = initial[0]
                label = f"{user_msg[:20]}{'...' if len(user_msg) > 20 else ''}"
                if st.button(label, key=f"history_{idx}"):
                    st.session_state.selected_conversation_index = idx
                    st.rerun()
                displayed_threads += 1
            if displayed_threads == 0:
                st.warning("No valid conversation threads found. Try starting a new chat or check Firebase data.")
        else:
            st.info("No conversations yet. Start a new chat to see it here.")

        if st.button("🔄 New Session"):
            st.session_state.chatbot.reset()
            st.session_state.selected_conversation_index = None
            st.rerun()

        if st.button("⚙️ Settings"):
            st.session_state.show_settings = True
            st.rerun()

        if st.button("🚪 Logout", key="logout_button"):
            try:
                save_chat_history(st.session_state.user_email, st.session_state.chat_history, st.session_state.user_token)
            except Exception as e:
                print(f"Logout: Failed to save chat history: {str(e)}")
            st.session_state.logged_in = False
            st.session_state.user_token = None
            st.session_state.user_email = None
            st.session_state.user_name = None
            st.session_state.chat_history = []
            st.session_state.selected_conversation_index = None
            st.session_state.show_settings = False
            st.session_state.signup_clicked = False
            st.session_state.pending_verification = False
            st.session_state.temp_user_id = None
            st.session_state.temp_username = None
            st.rerun()

# Settings Panel
if st.session_state.logged_in and st.session_state.show_settings:
    st.title("⚙️ Settings")
    st.subheader("Update Nickname")
    new_nickname = st.text_input("Enter new nickname:", value=st.session_state.user_name or "", key="new_nickname")
    if st.button("Save Nickname"):
        if new_nickname and new_nickname.strip():
            st.session_state.user_name = new_nickname
            try:
                safe_email = st.session_state.user_email.replace(".", "_").replace("@", "_")
                db.child("users").child(safe_email).update(
                    {"username": new_nickname},
                    token=st.session_state.user_token
                )
                st.success(f"Nickname updated to {st.session_state.user_name}")
            except Exception as e:
                st.error(f"Failed to update nickname in Firebase: {str(e)}")
            st.session_state.show_settings = False
            st.rerun()
        else:
            st.error("Please enter a valid nickname.")

    st.subheader("Clear Chat History")
    if st.button("Clear All Chat History"):
        clear_chat_history(st.session_state.user_email, st.session_state.user_token)
        st.session_state.selected_conversation_index = None
        st.rerun()

    st.subheader("Delete Account")
    st.warning("This action will permanently delete your account and all associated data. This cannot be undone.")
    if st.button("Delete My Account"):
        try:
            safe_email = st.session_state.user_email.replace(".", "_").replace("@", "_")
            db.child("users").child(safe_email).remove(token=st.session_state.user_token)
            response = requests.post(
                'https://identitytoolkit.googleapis.com/v1/accounts:delete?key=' + os.getenv("API_KEY"),
                json={'idToken': st.session_state.user_token}
            )
            if response.status_code == 200:
                st.session_state.logged_in = False
                st.session_state.user_token = None
                st.session_state.user_email = None
                st.session_state.user_name = None
                st.session_state.chat_history = []
                st.session_state.selected_conversation_index = None
                st.session_state.show_settings = False
                st.session_state.signup_clicked = False
                st.session_state.pending_verification = False
                st.session_state.temp_user_id = None
                st.session_state.temp_username = None
                st.rerun()
                st.success("Account deleted successfully. You can now sign up as a new user.")
            else:
                st.error(f"Failed to delete account: {response.text}")
        except Exception as e:
            st.error(f"Error deleting account: {str(e)}")

    st.subheader("Theme")
    light_mode = st.checkbox("Enable Light Mode", value=st.session_state.light_mode)
    if st.button("Apply Theme"):
        st.session_state.light_mode = light_mode
        st.success("Theme applied! Returning to chat...")
        st.session_state.show_settings = False
        st.rerun()

    if st.button("Back to Chat"):
        st.session_state.show_settings = False
        st.rerun()

# Main Chat UI
if st.session_state.logged_in and not st.session_state.show_settings:
    st.title("SATyr - your SAT saviour")

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
                        new_thread = {"initial": (user_input, ai_response), "follow_ups": []}
                        st.session_state.chat_history.append(new_thread)
                        save_chat_history(st.session_state.user_email, st.session_state.chat_history, st.session_state.user_token)
                        st.session_state.selected_conversation_index = len(st.session_state.chat_history) - 1
                        st.rerun()

        if st.session_state.selected_conversation_index is not None:
            idx = st.session_state.selected_conversation_index
            if 0 <= idx < len(st.session_state.chat_history):
                thread = st.session_state.chat_history[idx]
                user_msg, ai_msg = thread["initial"]
                st.markdown(f'<div class="user-bubble">🧑 {st.session_state.user_name}: {user_msg}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="ai-bubble">🤖 SATyr: {ai_msg}</div>', unsafe_allow_html=True)

                for follow_up_user_msg, follow_up_ai_msg in thread.get("follow_ups", []):
                    st.markdown(f'<div class="user-bubble">🧑 {st.session_state.user_name}: {follow_up_user_msg}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="ai-bubble">🤖 SATyr: {follow_up_ai_msg}</div>', unsafe_allow_html=True)

            with st.form(f"reply_form_{idx}", clear_on_submit=True):
                follow_up_input = st.text_input("💬 Follow-up question:", placeholder="Type your follow-up question here...", key=f"follow_up_{idx}")
                reply_submitted = st.form_submit_button("Reply")

                if reply_submitted and follow_up_input:
                    thread = st.session_state.chat_history[idx]
                    context_parts = [f"User: {thread['initial'][0]}\nSATyr: {thread['initial'][1]}"]
                    context_parts.extend([f"User: {u}\nSATyr: {a}" for u, a in thread.get("follow_ups", [])])
                    context = "\n".join(context_parts)
                    ai_response = st.session_state.chatbot.send_request(follow_up_input, context)
                    if ai_response.startswith("[Error]"):
                        st.error(f"Failed to get follow-up response: {ai_response}")
                    else:
                        if "follow_ups" not in st.session_state.chat_history[idx]:
                            st.session_state.chat_history[idx]["follow_ups"] = []
                        st.session_state.chat_history[idx]["follow_ups"].append((follow_up_input, ai_response))
                        save_chat_history(st.session_state.user_email, st.session_state.chat_history, st.session_state.user_token)
                        st.rerun()

            st.divider()
