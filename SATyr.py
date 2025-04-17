import http.client
import json
import os
from typing import Optional, Dict

class PersonalAIChat:
    def _init_(self):
        self.api_key = os.getenv("PERSONAL_AI_KEY", "rzZknlckhFldf2YV2AcpHlxmknkcL7Bo")
        self.domain = os.getenv("AI_DOMAIN", "km-pfrdhsi")
        self.base_url = "api.personal.ai"
        self.session_id: Optional[str] = None
        self.user_name: Optional[str] = None
        self.context: Optional[str] = None  # New context tracking
        self._connection = http.client.HTTPSConnection(self.base_url)

    def _create_payload(self, text: str) -> Dict:
        """Construct API payload with current session state"""
        payload = {
            "Text": text,
            "DomainName": self.domain,
            "UserName": self.user_name or "Guest"
        }
        if self.session_id:
            payload["SessionId"] = self.session_id
        if self.context:  # Add context to payload if available
            payload["Context"] = self.context
        return payload

    def send_request(self, text: str) -> Optional[Dict]:
        """Handle API communication with error logging"""
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
                self.context = response_data.get("ai_message")  # Store response as new context
                return response_data
            
            self._log_api_error(response)
            return None

        except json.JSONDecodeError as e:
            print(f"Invalid JSON response: {str(e)}")
            return None
        except Exception as e:
            print(f"Network error: {str(e)}")
            return None

    def _log_api_error(self, response: http.client.HTTPResponse):
        """Detailed error diagnostics"""
        error_body = response.read().decode()
        print(f"\n=== API Error ({response.status} {response.reason}) ===")
        print(f"Domain: {self.domain}")
        print(f"API Key: {self.api_key[:6]}...{self.api_key[-4:]}")
        print(f"Response: {error_body[:200]}...")
        print("Troubleshooting Steps:")
        print("1. Verify domain at https://app.personal.ai/domains")
        print("2. Check API key permissions")
        print("3. Test connection with: curl -X POST \\")
        print(f'   -H "x-api-key: {self.api_key[:6]}..." \\')
        print(f'   -d \'{{"Text":"Test","DomainName":"{self.domain}"}}\' \\')
        print(f'   https://{self.base_url}/v1/message')

    def start_new_session(self):
        """Reset conversation history"""
        self.session_id = None
        self.user_name = None
        self.context = None  # Clear context on new session
        print("\n" + "="*40)
        print(" New Chat Session Initialized ")
        print("="*40 + "\n")

    def chat_interface(self):
        """Main interactive chat loop"""
        self.start_new_session()
        
        # Get user identity
        while not self.user_name:
            try:
                name = input("AI: Welcome! How should I address you? ").strip()
                if name.lower() in ('exit', 'quit'):
                    return
                self.user_name = name or "Anonymous"
            except KeyboardInterrupt:
                print("\nSession cancelled")
                return

        # Conversation loop
        while True:
            try:
                user_input = input(f"{self.user_name}: ").strip()
                
                if not user_input:
                    continue
                if user_input.lower() == 'new':
                    self.start_new_session()
                    continue
                if user_input.lower() in ('exit', 'quit'):
                    break

                response = self.send_request(user_input)
                
                if response:
                    print(f"\nAI: {response.get('ai_message', 'No response received')}")
                    print(f"[Session: {self.session_id[:8]}]" if self.session_id else "")
                else:
                    print("\nAI: Service temporarily unavailable")

            except KeyboardInterrupt:
                print("\nSession ended by user")
                break

    def _del_(self):
        """Cleanup resources"""
        self._connection.close()

if _name_ == "_main_":
    # Configuration validation
    chat = PersonalAIChat()
    
    print("Initializing AI Chat...")
    test_response = chat.send_request("Connection test")
    
    if test_response and test_response.get("ai_message"):
        print("System Ready - Connection Verified\n")
        chat.chat_interface()
    else:
        print("\nFailed to initialize. Potential issues:")
        print("- Incorrect API key or domain configuration")
        print("- Network connectivity problems")
        print("- Service outage (check status.personal.ai)")
        print("\nVerify configuration and try again.")
