import streamlit as st
import http.client
import json
from typing import Optional, Dict

class PersonalAIChat:
    def __init__(self):
        self.api_key = "rzZknlckhFldf2YV2AcpHlxmknkcL7Bo"  # Replace with secure method if deploying publicly
        self.domain = "km-pfrdhsi"
        self.base_url = "api.personal.ai"
        self.session_id: Optional[str] = None
        self.user_name: Optional[str] = None
        self.context: Optional[str] = None
        self._connection = http.client.HTTPSConnection(self.base_url)

    def _create_payload(self, text: str) -> Dict:
        payload = {
            "Text": text,
            "DomainName": self.domain,
            "UserName": self.user_name or "Guest"
        }
        if self.session_id:
            payload["SessionId"] = self.session_id
        if self.context:
            payload["Context"] = self.context
        return payload

    def send_request(self, text: str) -> Optional[Dict]:
        try:
            payload = json.dumps(self._create_payload(text))
            headers = {
                'Content-Type': 'application/json',
                'x-api-key': self.api_key
            }

            self._connection.request("POST", "/v1/message", payload, headers)
            response = self._connection.getresponse()

            if response.status == 200:
                response_data = json.loads(response.read().decode())
                self.session_id = response_data.get("SessionId", self.session_id)
                self.context = response_data.get("ai_message")
                return response_data

            return {"ai_message": f"API Error: {response.status} {response.reason}"}

        except Exception as e:
            return {"ai_message": f"Network error: {str(e)}"}

    def reset(self):
        self.session_id = None
        self.user_name = None
        self.context = None

    def __del__(self):
        self._connection.close()


# Streamlit App
st.set_page_config(page_title="Personal AI Chat", page_icon="🤖")

if "chatbot" not in st.session_state:
    st.session_state.chatbot = PersonalAIChat()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "user_name" not in st.session_state:
    st.session_state.user_name = None

st.title("Bujji")

if not st.session_state.user_name:
    st.session_state.user_name = st.text_input("What’s your name?", value="", placeholder="Enter your name to start...")

if st.session_state.user_name:
    st.session_state.chatbot.user_name = st.session_state.user_name

    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("You:", placeholder="Type your message here...")
        submitted = st.form_submit_button("Send")

    if submitted and user_input:
        response = st.session_state.chatbot.send_request(user_input)
        st.session_state.chat_history.append((user_input, response.get("ai_message", "No response received")))

    # Chat history display
    for user_msg, ai_msg in reversed(st.session_state.chat_history):
        st.markdown(f"**You:** {user_msg}")
        st.markdown(f"**AI:** {ai_msg}")
        st.markdown("---")

    if st.button("🔄 Start New Session"):
        st.session_state.chatbot.reset()
        st.session_state.chat_history = []
        st.session_state.user_name = None
        st.experimental_rerun()

else:
    st.info("👆 Please enter your name to begin chatting.")

