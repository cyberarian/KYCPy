import streamlit as st
import os.path
from utils.path_helper import get_asset_path

# --- Test Constants ---
# First test, we hardcode the path
HARDCODED_LOGO_PATH = "assets/logo.png"  # Replace with your actual path if different
# Use get_asset_path function
DYNAMIC_LOGO_PATH = get_asset_path('logo.png')
LOGO_WIDTH = 200
LOGO_ALT = "KYCPy Test Logo"


def test_logo_display(logo_path: str, name:str) -> None:
    """
    Tests displaying the logo with error handling and detailed diagnostics.
    """
    st.header(f"Test {name}")
    st.write(f"Logo Path: {logo_path}")

    if not os.path.exists(logo_path):
        st.error(f"❌ File does not exist at: {logo_path}")
        return

    try:
        st.image(logo_path, width=LOGO_WIDTH, caption=LOGO_ALT)
        st.success(f"✅ Logo displayed successfully from: {logo_path}")
    except FileNotFoundError:
        st.error(f"❌ File not found (even though it seems to exist): {logo_path}")
    except Exception as e:
        st.error(f"❌ An error occurred displaying the logo: {str(e)}")

    st.write("---")  # Separator

# --- Main Test Execution ---
st.title("Logo Display Test")

st.subheader("Test get_asset_path")
st.write(f"get_asset_path function output: {DYNAMIC_LOGO_PATH}")
# we test the output of get_asset_path independently
if os.path.exists(DYNAMIC_LOGO_PATH):
    st.success("✅ get_asset_path correctly returns a valid path")
else:
    st.error("❌ get_asset_path returns an invalid path")

test_logo_display(DYNAMIC_LOGO_PATH,"Dynamic Path")

test_logo_display(HARDCODED_LOGO_PATH,"Hardcoded Path")

