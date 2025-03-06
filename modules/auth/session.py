import streamlit as st
from datetime import datetime, timedelta
from .users import authenticate_user, User
from .roles import check_access, Resource, Permission

def init_auth():
    """Initialize authentication state"""
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'auth_status' not in st.session_state:
        st.session_state.auth_status = None
    if 'login_attempts' not in st.session_state:
        st.session_state.login_attempts = 0

def login_required(resource: Resource, required_permission: Permission):
    """Decorator to protect pages/functions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not st.session_state.user:
                st.error("Please log in to access this feature")
                display_login()
                return
            
            if not check_access(st.session_state.user.role, resource, required_permission):
                st.error("You don't have permission to access this feature")
                return
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def display_login():
    """Display login form"""
    # Add styling for fonts
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Ledger:wght@300;400;500;700&family=Playfair+Display:wght@400;500;600;700&display=swap');
            
            .login-container {
                font-family: 'Ledger', serif;
            }
            .login-title {
                font-family: 'Playfair Display', serif;
                font-weight: 600;
                letter-spacing: -0.02em;
            }
            .stImage {
                background-color: transparent;
            }
            .stImage img {
                background-color: transparent;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # Center the logo
    col1, col2, col3 = st.columns([5,2,5])
    with col2:
        st.image("assets/logo.png", width=280)
    
    # Title under logo with updated styling
    st.markdown("""
        <div class='login-container' style='text-align: center; padding: 10px; color: grey'>
            <p class='login-title' style='font-size: 1.5rem; margin-bottom: 1rem;'>Know Your Customer (KYC) Management Platform</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Login form
    col1, col2, col3 = st.columns([3,2,3])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True)
            
            if submit:
                if st.session_state.login_attempts >= 3:
                    st.error("Too many failed attempts. Please try again later.")
                    return
                
                user = authenticate_user(username, password)
                if user:
                    st.session_state.user = user
                    st.session_state.auth_status = "logged_in"
                    st.session_state.login_attempts = 0
                    st.rerun()
                else:
                    st.session_state.login_attempts += 1
                    st.error("Invalid username or password")
    
    # Add some space before footer
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Simplified footer with just the text
    st.markdown("---")
    st.markdown(
        '<div style="text-align: center; color: grey">'
        '<p style="margin-bottom: 5px;">Powered by <a href="mailto:cyberariani@gmail.com">KCYPy</a> (2025)</p>'
        '</div>',
        unsafe_allow_html=True
    )

def logout():
    """Clear session state and log out user"""
    st.session_state.user = None
    st.session_state.auth_status = None
    st.rerun()
