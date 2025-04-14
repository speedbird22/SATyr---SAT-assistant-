import streamlit as st
import http.client
import json
from typing import Optional, Dict, List, Tuple
import time
from dotenv import load_dotenv
import os
import requests
import urllib.parse
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
if "chatbot" not in st.session_state:
    st.session_state.chatbot = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "selected_conversation_index" not in st.session_state:
    st.session_state.selected_conversation_index = None
if "visit_count" not in st.session_state:
    st.session_state.visit_count = 0
if "asked_for_name" not in st.session_state:
    st.session_state.asked_for_name = False

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

# Load environment variables (if needed for other APIs)
load_dotenv()

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
            "Context": context if context else "",
            "DomainName": self.domain,
            "UserName": self.user_name or "Guest",
            "SourceName": "API",
            "Is_stack": False,
            "Is_draft": False
        }
        if self.session_id:
            payload["SessionId"] = self.session_id
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

# --- Custom styling ---
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

# --- Update visit counter (local) ---
def update_visit_counter():
    st.session_state.visit_count += 1

# --- Clear chat history (session state) ---
def clear_chat_history():
    st.session_state.chat_history = []
    st.success("Chat history cleared successfully!")

# --- Sidebar ---
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

    if st.button("⚙️ Settings"):
        st.session_state.show_settings = True
        st.rerun()

# --- Settings Panel ---
if st.session_state.show_settings:
    st.title("⚙️ Settings")
    st.subheader("Update Name")
    new_name = st.text_input("Enter your name:", value=st.session_state.user_name or "", key="new_name")
    if st.button("Save Name"):
        if new_name and new_name.strip():
            st.session_state.user_name = new_name.strip()
            st.success(f"Name updated to {st.session_state.user_name}")
            st.session_state.show_settings = False
            st.rerun()
        else:
            st.error("Please enter a valid name.")

    st.subheader("Clear Chat History")
    if st.button("Clear All Chat History"):
        clear_chat_history()
        st.session_state.selected_conversation_index = None
        st.rerun()

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

# --- Main Chat UI ---
else:
    st.title("SATyr - you're SAT saviour")
    update_visit_counter()

    if st.session_state.user_name:
        st.session_state.chatbot.user_name = st.session_state.user_name
    else:
        st.session_state.chatbot.user_name = "Guest"

    # Ask for name if not set
    if not st.session_state.user_name and not st.session_state.asked_for_name:
        st.session_state.chat_history.append(("", "Hey there! What's your name?"))
        st.session_state.asked_for_name = True
        st.session_state.selected_conversation_index = 0

    if st.session_state.selected_conversation_index is None:
        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_input("💬 Your message:", placeholder="Type your message here...")
            submitted = st.form_submit_button("Send")

            if submitted and user_input:
                if not st.session_state.user_name:
                    # First input is the name
                    st.session_state.user_name = user_input.strip()
                    st.session_state.chat_history.append((user_input, f"Nice to meet you, {st.session_state.user_name}! How can I help you today?"))
                    st.session_state.selected_conversation_index = len(st.session_state.chat_history) - 1
                else:
                    ai_response = st.session_state.chatbot.send_request(user_input)
                    if ai_response.startswith("[Error]"):
                        st.error(f"Failed to get response: {ai_response}")
                    else:
                        st.session_state.chat_history.append((user_input, ai_response))
                        st.session_state.selected_conversation_index = len(st.session_state.chat_history) - 1
                st.rerun()

    if st.session_state.selected_conversation_index is not None:
        idx = st.session_state.selected_conversation_index
        if 0 <= idx < len(st.session_state.chat_history):
            user_msg, ai_msg = st.session_state.chat_history[idx]
            if user_msg or ai_msg:
                st.markdown('<hr style="border: 1px solid #ccc; margin: 10px 0;">', unsafe_allow_html=True)
                if user_msg:
                    st.markdown(f'<div class="user-bubble">🧑 {st.session_state.user_name or "You"}: {user_msg}</div>', unsafe_allow_html=True)
                st.markdown('<hr style="border: 1px solid #ccc; margin: 10px 0;">', unsafe_allow_html=True)
                st.markdown(f'<div class="ai-bubble">🤖 SATyr: {ai_msg}</div>', unsafe_allow_html=True)

            for i in range(idx + 1, len(st.session_state.chat_history)):
                follow_up_user_msg, follow_up_ai_msg = st.session_state.chat_history[i]
                st.markdown('<hr style="border: 1px solid #ccc; margin: 10px 0;">', unsafe_allow_html=True)
                st.markdown(f'<div class="user-bubble">🧑 {st.session_state.user_name or "You"}: {follow_up_user_msg}</div>', unsafe_allow_html=True)
                st.markdown('<hr style="border: 1px solid #ccc; margin: 10px 0;">', unsafe_allow_html=True)
                st.markdown(f'<div class="ai-bubble">🤖 SATyr: {follow_up_ai_msg}</div>', unsafe_allow_html=True)

        with st.form(f"reply_form_{idx}", clear_on_submit=True):
            follow_up_input = st.text_input("💬 Your message:", placeholder="Type your message here...", key=f"follow_up_{idx}")
            reply_submitted = st.form_submit_button("Send")

            if reply_submitted and follow_up_input:
                if not st.session_state.user_name:
                    # First input is the name
                    st.session_state.user_name = follow_up_input.strip()
                    st.session_state.chat_history.append((follow_up_input, f"Nice to meet you, {st.session_state.user_name}! How can I help you today?"))
                else:
                    context = "\n".join([f"User: {msg[0]}\nSATyr: {msg[1]}" for msg in st.session_state.chat_history[:idx + 1]])
                    ai_response = st.session_state.chatbot.send_request(follow_up_input, context)
                    if ai_response.startswith("[Error]"):
                        st.error(f"Failed to get follow-up response: {ai_response}")
                    else:
                        st.session_state.chat_history.append((follow_up_input, ai_response))
                st.rerun()

        st.divider()
