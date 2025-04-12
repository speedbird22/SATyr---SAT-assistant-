import streamlit as st
import re

# Email validation
def is_valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email)

# Password validation
def is_valid_password(password):
    return len(password) >= 6

# Initialize session state variables if not set
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_name" not in st.session_state:
    st.session_state.user_name = ""

# --- Login Page ---
if not st.session_state.logged_in:
    st.title("🔐 SATyr Login")
    st.markdown("Welcome to SATyr. Please log in or sign up to continue.")

    email = st.text_input("📧 Email")
    password = st.text_input("🔒 Password", type="password")

    col1, col2 = st.columns(2)
    with col1:
        login = st.button("🔓 Login")
    with col2:
        signup = st.button("📝 Sign Up")

    # SIGNUP FLOW
    if signup:
        if not is_valid_email(email):
            st.warning("Please enter a valid email address.")
        elif not is_valid_password(password):
            st.warning("Password must be at least 6 characters long.")
        else:
            st.success("Signup successful!")
            st.session_state.user_name = email.split("@")[0]
            st.session_state.logged_in = True
            st.experimental_rerun()

    # LOGIN FLOW (temporary placeholder)
    elif login:
        st.session_state.show_double_click_message = True  # Temporary logic if login not built yet
        st.warning("Login functionality coming soon.")
else:
    st.success(f"Welcome back, {st.session_state.user_name}!")
