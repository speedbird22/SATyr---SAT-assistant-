import streamlit as st
import pyrebase
from streamlit_option_menu import option_menu

# Firebase configuration
firebaseConfig = {
    "apiKey": "AIzaSyBxRk5PqiCMaCgJ2r5yV27O9UUNNxyJ6cc",
    "authDomain": "satyr-login.firebaseapp.com",
    "projectId": "satyr-login",
    "storageBucket": "satyr-login.appspot.com",
    "messagingSenderId": "438720156646",
    "appId": "1:438720156646:web:46f570a0dbf3c8b6e6a003",
    "measurementId": "G-WE9PZNYRQQ",
    "databaseURL": ""
}

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

# Setup page
st.set_page_config(page_title="SATyr Login", page_icon="🔒", layout="centered")
st.markdown("## 🔒 Login to SATyr")

# If already logged in, skip login screen
if "user" in st.session_state and st.session_state.user:
    st.markdown(f"### 👋 Welcome, `{st.session_state.user.get('email', 'User')}`!")
    if st.button("Logout"):
        st.session_state.user = None
        st.success("You have been logged out.")
        st.experimental_rerun()
    else:
        # Put your actual app content here
        st.write("🎉 You are inside the app. Add your chatbot UI here.")
    st.stop()

# Toggle between login and signup
login_option = st.radio("Choose an option:", ["Login", "Sign Up"])

# Input fields
email = st.text_input("Email")
password = st.text_input("Password", type="password")

# Show buttons only when email/password filled
if email and password:
    if login_option == "Login":
        if st.button("Login"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.user = user
                st.success("✅ Logged in successfully!")
                st.experimental_rerun()
            except Exception as e:
                st.error("❌ Login failed. Please check your email and password.")
                st.session_state.user = None

    elif login_option == "Sign Up":
        if st.button("Sign Up"):
            try:
                user = auth.create_user_with_email_and_password(email, password)
                st.success("✅ Account created! Please log in.")
                st.session_state.user = None
                st.experimental_rerun()
            except Exception as e:
                st.error("❌ Sign up failed. This email might already be in use or the password is too weak.")
else:
    st.info("ℹ️ Enter email and password to proceed.")
