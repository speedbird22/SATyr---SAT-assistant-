# --- Session State Init ---
# (Unchanged, as shown above)

# --- Helper Functions for Auto-Login ---
def save_refresh_token(email: str, refresh_token: str, token: str):
    try:
        safe_email = email.replace(".", "_").replace("@", "_")
        db.child("users").child(safe_email).set({
            "email": email,
            "refresh_token": refresh_token
        }, token)
    except Exception as e:
        st.warning(f"Failed to save refresh token: {str(e)}. Auto-login may not work.")

def load_refresh_token(email: str) -> Optional[str]:
    try:
        safe_email = email.replace(".", "_").replace("@", "_")
        data = db.child("users").child(safe_email).get().val()
        if data and "refresh_token" in data:
            return data["refresh_token"]
        return None
    except Exception as e:
        st.warning(f"Failed to load refresh token: {str(e)}. Auto-login may not work.")
        return None

def load_user_email() -> Optional[str]:
    try:
        users = db.child("users").get().val()
        if users:
            for safe_email, data in users.items():
                if "email" in data:
                    return data["email"]
        return None
    except Exception as e:
        st.warning(f"Failed to load user email: {str(e)}.")
        return None

def try_auto_login():
    st.session_state.chat_history = []
    st.session_state.selected_conversation_index = None
    
    if not st.session_state.user_email:
        st.session_state.user_email = load_user_email()

    if st.session_state.user_email:
        st.session_state.refresh_token = load_refresh_token(st.session_state.user_email)

    if st.session_state.user_email and st.session_state.refresh_token:
        try:
            user = auth.refresh(st.session_state.refresh_token)
            st.session_state.user_token = user['idToken']
            st.session_state.logged_in = True
            st.session_state.user_name = st.session_state.user_email.split("@")[0]
            st.session_state.chat_history = load_chat_history(st.session_state.user_email, st.session_state.user_token)
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

# --- Load and Save Chat History ---
def load_chat_history(email: str, token: str) -> List[Tuple[str, str]]:
    if not st.session_state.logged_in or not email or not token:
        return []
    try:
        safe_email = email.replace(".", "_").replace("@", "_")
        chat_data = db.child("users").child(safe_email).child("chat_history").get(token=token).val()
        if isinstance(chat_data, list):
            return [(str(item[0]), str(item[1])) for item in chat_data if isinstance(item, list) and len(item) == 2]
        return []
    except Exception as e:
        st.warning(f"Failed to load chat history: {str(e)}.")
        return []

def save_chat_history(email: str, chat_history: List[Tuple[str, str]], token: str):
    if not st.session_state.logged_in or not email or not token:
        return
    try:
        safe_email = email.replace(".", "_").replace("@", "_")
        serialized_history = [[user_msg, ai_msg] for user_msg, ai_msg in chat_history]
        db.child("users").child(safe_email).child("chat_history").set(serialized_history, token)
    except Exception as e:
        st.warning(f"Failed to save chat history: {str(e)}.")

# --- Login Page ---
if not st.session_state.logged_in:
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
            st.session_state.chat_history = []
            st.session_state.selected_conversation_index = None
            
            if login:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.user_name = email.split("@")[0]
                st.session_state.user_token = user['idToken']
                st.session_state.refresh_token = user['refreshToken']
                save_refresh_token(email, user['refreshToken'], user['idToken'])
                st.session_state.chat_history = load_chat_history(email, user['idToken'])
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
                st.session_state.chat_history = []
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

# --- Sidebar ---
if st.session_state.logged_in:
    with st.sidebar:
        st.markdown('<div class="logo-container">', unsafe_allow_html=True)
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image("logo.jpg", clamp=True, output_format="auto")
        with col2:
            st.markdown('<h1 class="sidebar-title">SATyr</h1>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown(f'<div id="visit-counter">Visits: {st.session_state.visit_count}</div>', unsafe_allow_html=True)
        st.subheader("Conversations")

        if st.session_state.chat_history:
            for idx, (user_msg, ai_msg) in enumerate(st.session_state.chat_history):
                label = f"{user_msg[:20]}..." if len(user_msg) > 20 else user_msg
                if st.button(label, key=f"history_{idx}"):
                    st.session_state.selected_conversation_index = idx
                    st.rerun()
        else:
            st.info("No conversations yet.")

        if st.button("🔄 New Session"):
            st.session_state.chatbot.reset()
            st.session_state.selected_conversation_index = None
            st.session_state.chat_history = []
            if st.session_state.user_email and st.session_state.user_token:
                save_chat_history(st.session_state.user_email, [], st.session_state.user_token)
            st.rerun()

        if st.button("🚪 Logout"):
            try:
                if st.session_state.chat_history and st.session_state.user_email and st.session_state.user_token:
                    save_chat_history(st.session_state.user_email, st.session_state.chat_history, st.session_state.user_token)
                st.session_state.logged_in = False
                st.session_state.chatbot.reset()
                st.session_state.chat_history = []
                st.session_state.selected_conversation_index = None
                st.session_state.user_name = None
                st.session_state.user_email = None
                st.session_state.user_token = None
                st.session_state.refresh_token = None
                st.rerun()
            except Exception as e:
                st.error(f"Logout failed: {str(e)}")
