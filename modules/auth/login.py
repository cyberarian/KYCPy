import streamlit as st
from typing import NoReturn
import os.path
from modules.auth.session import login_user
from utils.path_helper import get_asset_path

# Constants
LOGO_PATH = get_asset_path('logo.png')
LOGO_WIDTH = 200
LOGO_ALT = "KYCPy Logo"

def display_logo() -> NoReturn:
    """Display the KYCPy logo in the center of the page with error handling."""
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            try:
                if os.path.exists(LOGO_PATH):
                    st.image(LOGO_PATH, 
                            width=LOGO_WIDTH,
                            use_column_width=True,
                            caption=LOGO_ALT)
                else:
                    st.warning(f"Logo not found at: {LOGO_PATH}")
                st.markdown(
                    "<h1 style='text-align: center; margin-top: -10px;'>KYCPy</h1>", 
                    unsafe_allow_html=True
                )
            except Exception as e:
                st.error(f"Error displaying logo: {str(e)}")

def display_login() -> NoReturn:
    """
    Display the login page with username and password inputs.
    Handles user authentication and provides feedback.
    """
    if 'login_attempts' not in st.session_state:
        st.session_state.login_attempts = 0

    display_logo()
    
    st.markdown("### Login")
    username = st.text_input("Username").strip()
    password = st.text_input("Password", type="password").strip()
    
    if st.button("Login"):
        if not username or not password:
            st.error("Please enter both username and password")
            return
            
        if st.session_state.login_attempts >= 3:
            st.error("Too many login attempts. Please try again later.")
            return
            
        if login_user(username, password):
            st.session_state.login_attempts = 0
            st.success("Login successful!")
            st.experimental_rerun()
        else:
            st.session_state.login_attempts += 1
            st.error("Invalid username or password")
