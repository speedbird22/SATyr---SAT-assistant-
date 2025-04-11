import streamlit as st
from firebase_config import auth
from satyr_chat_ui import chat_ui
import pyrebase
import os

# Initialize session state variables
if "user" not in st.session_state:
    st.session_state.user = None

# Streamlit page setup
st.set_page_config(page_title="SATyr", layout="wide", page_icon="🧠")

# Custom CSS for dark background like ChatGPT
st.markdown("""
    <style>
    body {
        background-color: #1E1E1E;
        color: #EAEAEA;
    }
    .stApp {
        background-color: #1E1E1E;
        color: #EAEAEA;
    }
    </style>
""", unsafe_allow_html=True)

# Firebase login/signup page
def show_login_page():
    st.title("🔐 Login to SATyr")
    login_option = st.radio("Choose an option:", ["Login", "Sign Up"])
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if login_option == "Login":
        if st.button("Login"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.user = user
                st.success("Logged in successfully!")
                st.experimental_rerun()
            except Exception as e:
                st.error("Login failed. Please check your credentials.")
    else:
        if st.button("Sign Up"):
            try:
                user = auth.create_user_with_email_and_password(email, password)
                st.session_state.user = user
                st.success("Account created and signed in!")
                st.experimental_rerun()
            except Exception as e:
                st.error("Signup failed. Email may already be in use.")

# Main routing
if st.session_state.user is None:
    show_login_page()
else:
    # Sidebar with logout option
    with st.sidebar:
        st.markdown("## SATyr Chat")
        if st.button("🚪 Log out"):
            st.session_state.user = None
            st.experimental_rerun()
    
    # Show chat interface
    chat_ui()
