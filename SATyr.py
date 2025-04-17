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
        color: white;
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
        color: white;
    }}
    .stSidebar .stButton > button:not([id*="history"]):hover,
    div:not([data-testid="stHorizontalBlock"]):not([id*="form"]) .stButton > button:hover {{
        background-color: {COLORS['button_sidebar_hover'] if not st.session_state.light_mode else LIGHT_MODE_COLORS['light_button_sidebar_default']};
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
        background-color: {COLORS['button_form_default'] if not st.session_state.light_mode else LIGHT_MODE_COLORS['light_button_form_default']};
        color: white;
        padding: 10px 15px;
        border-radius: 15px 15px 0 15px;
        display: inline-block;
        max-width: 70%;
        margin: 5px 0;
    }}
    .ai-bubble {{
        background-color: {COLORS['button_sidebar_default'] if not st.session_state.light_mode else LIGHT_MODE_COLORS['light_button_sidebar_default']};
        color: white;
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
            for item in chat_data:
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
def save_chat_history(email: str, chat_history
