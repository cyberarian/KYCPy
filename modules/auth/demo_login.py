import streamlit as st

def show_demo_credentials():
    """Display demo login credentials in a styled container"""
    with st.container():
        st.markdown("""
        <style>
        .demo-box {
            background-color: transparent;
            border-radius: 5px;
            padding: 20px;
            margin-bottom: 20px;
        }
        </style>
        <div class="demo-box">
            <h4>👋 Demo Access</h4>
            <p>Try the app with these credentials:</p>
            <code>Username: ade</code><br>
            <code>Password: ade123456</code>
        </div>
        """, unsafe_allow_html=True)
