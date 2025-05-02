import streamlit as st
import http.client
import json
from typing import Optional, Dict, List, Tuple
from dotenv import load_dotenv
import os
import pyrebase
import requests
import uuid
import time
import streamlit.components.v1 as components

# Set page config to wide layout to maximize screen usage
st.set_page_config(layout="wide", page_title="SATyr AI", initial_sidebar_state="collapsed")

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

# SATyr AI Client
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
                    return f"[Error] Invalid JSON response: {str(e)}"
            else:
                error_details = self._log_api_error(response.status, response.reason, response_data)
                return f"[Error] API request failed: {response.status} - {response.reason}"

        except http.client.HTTPException as e:
            return f"[Error] HTTP error: {str(e)}"
        except Exception as e:
            return f"[Error] Network or API error: {str(e)}"

    def reset(self):
        self.session_id = None
        self.context = None

# Initialize SATyr AI
satyr_ai = SATyrAI()

# Helper Functions
def refresh_user_token(refresh_token: str) -> Optional[Tuple[str, str]]:
    try:
        response = requests.post(
            'https://securetoken.googleapis.com/v1/token?key=' + os.getenv("API_KEY"),
            data={
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token
            }
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('id_token'), data.get('refresh_token')
        return None, None
    except Exception as e:
        st.error(f"Error refreshing token: {str(e)}")
        return None, None

def fetch_username(email: str, token: str) -> str:
    try:
        safe_email = email.replace(".", "_").replace("@", "_")
        username = db.child("users").child(safe_email).child("username").get(token=token).val()
        return username if username else None
    except Exception as e:
        st.error(f"Failed to fetch username: {str(e)}")
        return None

def load_chat_history(email: str, token: str) -> List[Dict]:
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

def save_chat_history(email: str, chat_history: List[Dict], token: str):
    try:
        safe_email = email.replace(".", "_").replace("@", "_")
        db.child("users").child(safe_email).child("chat_history").set(chat_history, token)
    except Exception as e:
        st.error(f"Failed to save chat history: {str(e)}")

def update_visit_counter():
    try:
        current_count = db.child("visit_count").get().val() or 0
        new_count = current_count + 1
        db.child("visit_count").set(new_count)
        return new_count
    except Exception as e:
        st.error(f"Failed to update visit counter: {str(e)}")
        return 0

# Streamlit App
def main():
    # Initialize session state
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'home'
    if 'chat_message' not in st.session_state:
        st.session_state.chat_message = ""

    # Read and embed HTML with a fixed height for the iframe
    with open("index.html", "r") as f:
        html_content = f.read()
    components.html(
        html_content,
        height=900,  # Set explicit height to match a typical laptop screen
        scrolling=True,
        width=None
    )

    # Handle JavaScript-to-Python communication
    if st.session_state.get('js_message'):
        js_data = st.session_state.js_message
        action = js_data.get('action')
        data = js_data.get('data', {})

        if action == 'login':
            email = data.get('email')
            password = data.get('password')
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                username = fetch_username(email, user['idToken'])
                st.session_state.user = {
                    'user_token': user['idToken'],
                    'refresh_token': user['refreshToken'],
                    'email': email,
                    'username': username or email.split("@")[0]
                }
                st.session_state.chat_history = load_chat_history(email, user['idToken'])
                update_visit_counter()
                st.session_state.js_response = {'status': 'success', 'message': 'Login successful'}
            except Exception as e:
                st.session_state.js_response = {'status': 'error', 'message': str(e)}

        elif action == 'signup':
            email = data.get('email')
            password = data.get('password')
            username = data.get('username')
            try:
                user = auth.create_user_with_email_and_password(email, password)
                safe_email = email.replace(".", "_").replace("@", "_")
                db.child("users").child(safe_email).set({"username": username}, user['idToken'])
                verification_response = requests.post(
                    'https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key=' + os.getenv("API_KEY"),
                    json={
                        'requestType': 'VERIFY_EMAIL',
                        'idToken': user['idToken'],
                        'email': email
                    }
                )
                if verification_response.status_code == 200:
                    st.session_state.user = {
                        'user_token': user['idToken'],
                        'refresh_token': user['refreshToken'],
                        'email': email,
                        'username': username
                    }
                    st.session_state.js_response = {'status': 'success', 'message': 'Signup successful, verification email sent'}
                else:
                    st.session_state.js_response = {'status': 'error', 'message': 'Failed to send verification email'}
            except Exception as e:
                st.session_state.js_response = {'status': 'error', 'message': str(e)}

        elif action == 'chat':
            if st.session_state.user:
                message = data.get('message')
                context = data.get('context')
                response = satyr_ai.send_request(message, context)
                if not response.startswith("[Error]"):
                    chat_history = st.session_state.chat_history
                    new_thread = {"initial": [message, response], "follow_ups": []}
                    chat_history.append(new_thread)
                    save_chat_history(st.session_state.user['email'], chat_history, st.session_state.user['user_token'])
                    st.session_state.chat_history = chat_history
                    st.session_state.js_response = {'status': 'success', 'response': response, 'chat_history': chat_history}
                else:
                    st.session_state.js_response = {'status': 'error', 'message': response}
            else:
                st.session_state.js_response = {'status': 'error', 'message': 'User not logged in'}

        elif action == 'get_chat_history':
            if st.session_state.user:
                st.session_state.chat_history = load_chat_history(st.session_state.user['email'], st.session_state.user['user_token'])
                st.session_state.js_response = {'status': 'success', 'chat_history': st.session_state.chat_history}
            else:
                st.session_state.js_response = {'status': 'error', 'message': 'User not logged in'}

        elif action == 'clear_history':
            if st.session_state.user:
                safe_email = st.session_state.user['email'].replace(".", "_").replace("@", "_")
                db.child("users").child(safe_email).child("chat_history").remove(token=st.session_state.user['user_token'])
                st.session_state.chat_history = []
                st.session_state.js_response = {'status': 'success', 'message': 'Chat history cleared'}
            else:
                st.session_state.js_response = {'status': 'error', 'message': 'User not logged in'}

        elif action == 'logout':
            st.session_state.user = None
            st.session_state.chat_history = []
            st.session_state.js_response = {'status': 'success', 'message': 'Logged out successfully'}

if __name__ == "__main__":
    main()
