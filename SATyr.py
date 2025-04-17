import streamlit as st
import http.client
import json
import os
from typing import Optional, Dict
from uuid import uuid4

class PersonalAIChat:
    def __init__(self):
        self.api_key = os.getenv("PERSONAL_AI_KEY", "rzZknlckhFldf2YV2AcpHlxmknkcL7Bo")
        self.domain = os.getenv("AI_DOMAIN", "km-pfrdhsi")
        self.base_url = "api.personal.ai"
        self._connection = http.client.HTTPSConnection(self.base_url)

    def _create_payload(self, text: str, session_id: Optional[str], user_name: Optional[str], context: Optional[str]) -> Dict:
        """Construct API payload with current session state"""
        payload = {
            "Text": text,
            "DomainName": self.domain,
            "UserName": user_name or "Guest"
        }
        if session_id:
            payload["SessionId"] = session_id
        if context:
            payload["Context"] = context
        return payload

    def send_request(self, text: str, session_id: Optional[str], user_name: Optional[str], context: Optional[str]) -> Optional[Dict]:
        """Handle API communication with error logging"""
        try:
            payload = json.dumps(self._create_payload(text, session_id, user_name, context))
            headers = {
                'Content-Type': 'application/json',
                'x-api-key': self.api_key
            }

            self._connection.request("POST", "/v1/message", payload, headers)
            response = self._connection.getresponse()
            
            if response.status == 200:
                response_data = json.loads(response.read().decode())
                return response_data
            
            self._log_api_error(response)
            return None

        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON response: {str(e)}")
            return None
        except Exception as e:
            st.error(f"Network error: {str(e)}")
            return None

    def _log_api_error(self, response: http.client.HTTPResponse):
        """Detailed error diagnostics"""
        error_body = response.read().decode()
        st.error(f"API Error ({response.status} {response.reason})\n"
                 f"Domain: {self.domain}\n"
                 f"API Key: {self.api_key[:6]}...{self.api_key[-4:]}\n"
                 f"Response: {error_body[:200]}...\n"
                 "Troubleshooting Steps:\n"
                 "1. Verify domain at https://app.personal.ai/domains\n"
                 "2. Check API key permissions\n"
                 "3. Test connection with: curl -X POST \\\n"
                 f'   -H "x-api-key: {self.api_key[:6]}..." \\\n'
                 f'   -d \'{{"Text":"Test","DomainName":"{self.domain}"}}\' \\\n'
                 f'   https://{self.base_url}/v1/message')

    def __del__(self):
        """Cleanup resources"""
        self._connection.close()

def main():
    st.set_page_config(page_title="Personal AI Chat", layout="wide")
    st.title("Personal AI Chat")

    # Initialize session state
    if 'chat_initialized' not in st.session_state:
        st.session_state.chat_initialized = False
        st.session_state.user_name = None
        st.session_state.session_id = None
        st.session_state.context = None
        st.session_state.messages = []
        st.session_state.message_key = str(uuid4())

    # Create PersonalAIChat instance
    chat = PersonalAIChat()

    # Test connection
    if not st.session_state.chat_initialized:
        test_response = chat.send_request("Connection test", None, None, None)
        if test_response and test_response.get("ai_message"):
            st.session_state.chat_initialized = True
            st.success("System Ready - Connection Verified")
        else:
            st.error("Failed to initialize. Potential issues:\n"
                     "- Incorrect API key or domain configuration\n"
                     "- Network connectivity problems\n"
                     "- Service outage (check status.personal.ai)\n"
                     "Verify configuration and refresh the page.")
            return

    # User name input
    if not st.session_state.user_name:
        with st.form(key="name_form"):
            name = st.text_input("Welcome! How should I address you?")
            submit_name = st.form_submit_button("Submit")
            if submit_name and name.strip():
                st.session_state.user_name = name.strip()
                st.session_state.messages.append({"role": "system", "content": f"Welcome, {name.strip()}!"})
                st.rerun()

    # Main chat interface
    if st.session_state.user_name:
        # Display conversation history
        for msg in st.session_state.messages:
            if msg["role"] == "system":
                st.info(msg["content"])
            elif msg["role"] == "user":
                with st.chat_message("user"):
                    st.write(f"{st.session_state.user_name}: {msg['content']}")
            elif msg["role"] == "ai":
                with st.chat_message("assistant"):
                    st.write(f"AI: {msg['content']}")
                    if msg.get("session_id"):
                        st.caption(f"[Session: {msg['session_id'][:8]}]")

        # Input form for new messages
        with st.form(key="chat_form", clear_on_submit=True):
            user_input = st.text_input(f"{st.session_state.user_name}:", key=st.session_state.message_key)
            col1, col2 = st.columns([1, 1])
            with col1:
                send_button = st.form_submit_button("Send")
            with col2:
                new_session_button = st.form_submit_button("New Session")

            if new_session_button:
                st.session_state.session_id = None
                st.session_state.context = None
                st.session_state.messages = []
                st.session_state.message_key = str(uuid4())
                st.session_state.messages.append({"role": "system", "content": "New Chat Session Initialized"})
                st.rerun()

            if send_button and user_input.strip():
                if user_input.lower() in ('exit', 'quit'):
                    st.session_state.messages.append({"role": "system", "content": "Session ended"})
                    st.rerun()
                else:
                    st.session_state.messages.append({"role": "user", "content": user_input})
                    response = chat.send_request(
                        user_input,
                        st.session_state.session_id,
                        st.session_state.user_name,
                        st.session_state.context
                    )
                    if response:
                        st.session_state.session_id = response.get("SessionId", st.session_state.session_id)
                        st.session_state.context = response.get("ai_message")
                        st.session_state.messages.append({
                            "role": "ai",
                            "content": response.get("ai_message", "No response received"),
                            "session_id": st.session_state.session_id
                        })
                    else:
                        st.session_state.messages.append({
                            "role": "ai",
                            "content": "Service temporarily unavailable"
                        })
                    st.session_state.message_key = str(uuid4())
                    st.rerun()

if __name__ == "__main__":
    main()
