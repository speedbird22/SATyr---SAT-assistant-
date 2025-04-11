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

st.set_page_config(page_title="SATyr Login", page_icon="🔒", layout="centered")
st.markdown("## 🔒 Login to SATyr")

# Toggle between login and signup
login_option = st.radio("Choose an option:", ["Login", "Sign Up"])

# Input fields
email = st.text_input("Email")
password = st.text_input("Password", type="password")

# Only show buttons if email and password are provided
if email and password:
    if login_option == "Login":
        if st.button("Login"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.user = user
                st.success("Logged in successfully!")
                st.experimental_rerun()
            except:
                st.session_state.user = None
                st.error("Login failed. Please check your credentials.")

    elif login_option == "Sign Up":
        if st.button("Sign Up"):
            try:
                user = auth.create_user_with_email_and_password(email, password)
                st.session_state.user = user
                st.success("Account created successfully! You can now log in.")
                st.experimental_rerun()
            except:
                st.session_state.user = None
                st.error("Sign up failed. Please try again.")
else:
    st.info("Please enter your email and password to continue.")

# Main app logic (placeholder)
if "user" in st.session_state and st.session_state.user:
    st.markdown("---")
    st.markdown(f"### 👋 Welcome, {st.session_state.user.get('displayName', 'User')}!")
    st.write("You are now inside the app.")
    # Add chatbot or other features here
