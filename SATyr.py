
import streamlit as st
from firebase_config import auth

st.set_page_config(page_title="SATyr", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'email' not in st.session_state:
    st.session_state.email = ""

def login():
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            st.session_state.logged_in = True
            st.session_state.email = email
            st.success("Logged in successfully!")
        except Exception as e:
            st.error("Login failed. Check your credentials.")

def logout():
    st.session_state.logged_in = False
    st.session_state.email = ""
    st.success("Logged out successfully.")

st.title("👨‍💻 SATyr - Your GPT-Powered Assistant")

if st.session_state.logged_in:
    st.sidebar.markdown(f"👤 Logged in as: {st.session_state.email}")
    if st.sidebar.button("Logout"):
        logout()
    st.write("Chatbot UI coming here...")
else:
    st.subheader("🔐 Please log in to continue")
    login()
