import streamlit as st
import http.client
import json
from typing import Optional, Dict
import time

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


# --- Page config ---
st.set_page_config(page_title="SATyr", page_icon="🧠", layout="wide")


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


# --- Custom dark background styling ---
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
    time.sleep(2)  # Keep the message for 2 seconds, then it disappears
    st.session_state.show_double_click_message = False  # Hide the message after a short period


# --- Login Page ---
if not st.session_state.logged_in:
    st.title("🔐 SATyr Login")
    st.markdown("Welcome to SATyr. Please log in or sign up to continue.")
     st.markdown("Please double click the buttons to maintain the proper functionality of the buttons ")


    email = st.text_input("📇 Email")
    password = st.text_input("🔐 Password", type="password")

    col1, col2 = st.columns(2)
    with col1:
        login = st.button("🔓 Login")
    with col2:
        signup = st.button("📝 Sign Up")

    if login or signup:
        st.session_state.show_double_click_message = True  # Show the "double-click" message
        time.sleep(0.5)  # Add delay before handling the next steps to simulate the double-click
        st.session_state.logged_in = True
        st.session_state.user_name = email.split("@")[0] if email else "Guest"
        st.stop()  # Stop the execution so the session state is set before moving on


# --- Sidebar ---
if st.session_state.logged_in:
    with st.sidebar:
        st.title("🧠 SATyr")
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
            try:
                st.experimental_rerun()
            except Exception:
                st.stop()

        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.chatbot.reset()
            st.session_state.chat_history = []
            st.session_state.reply_to_index = None
            st.session_state.user_name = None
            st.experimental_rerun()


# --- Main Chat UI ---
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
        st.session_state.reply_to_index = None

    # Display chat history
    for idx, (user_msg, ai_msg) in enumerate(reversed(st.session_state.chat_history)):
        display_idx = len(st.session_state.chat_history) - idx - 1
        st.markdown(f"**🧑 {st.session_state.user_name}:** {user_msg}")
        st.markdown(f"**🧠 SATyr:** {ai_msg}")
        if st.button("↩️ Reply", key=f"reply_{display_idx}"):
            st.session_state.reply_to_index = display_idx
        st.divider()
