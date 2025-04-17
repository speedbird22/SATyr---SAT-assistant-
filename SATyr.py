# Debug: Confirm code version
print("Running minimal SATyr app.py - Version with status fix (2025-04-17)")

import streamlit as st
import http.client
import json
from typing import Optional, Dict, List, Tuple

# Set page config
st.set_page_config(page_title="SATyr Chatbot", page_icon="🧠")

# AI Client
class SATyrAI:
    def __init__(self):
        self.api_key = "rzZknlckhFldf2YV2AcpHlxmknkcL7Bo"
        self.domain = "km-pfrdhsi"
        self.base_url = "api.personal.ai"
        self.session_id = None
        self.user_name = "Guest"  # Hardcoded for simplicity
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
            "UserName": self.user_name,
            "SourceName": "API",
            "Is_stack": False,
            "Is_draft": False
        }
        if self.session_id:
            payload["SessionId"] = self.session_id
        return payload

    def send_request(self, text: str, context: Optional[str] = None) -> str:
        print("Executing SATyrAI.send_request with response.status")
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

            # Debug: Log response details
            print(f"API Response Status: {response.status}, Reason: {response.reason}")
            print(f"API Response Data: {response_data}")

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

# Initialize session state for chatbot and chat history
if "chatbot" not in st.session_state:
    st.session_state.chatbot = SATyrAI()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Main Chat UI
st.title("SATyr Chatbot")

with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("Your message:", placeholder="Type your message here...")
    submitted = st.form_submit_button("Send")

    if submitted and user_input:
        ai_response = st.session_state.chatbot.send_request(user_input)
        if ai_response.startswith("[Error]"):
            st.error(f"Failed to get response: {ai_response}")
        else:
            st.session_state.chat_history.append((user_input, ai_response))
            st.rerun()

# Display chat history
for user_msg, ai_msg in st.session_state.chat_history:
    st.markdown(f"**You**: {user_msg}")
    st.markdown(f"**SATyr**: {ai_msg}")
    st.markdown("---")
