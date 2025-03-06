import streamlit as st
from typing import Dict
from datetime import datetime
import pandas as pd

def display_verification_results(extracted_info: Dict, verification_status: bool):
    """Display document verification results in a clear table format"""
    
    # Initialize session state if not exists
    if 'last_extracted_info' not in st.session_state:
        st.session_state.last_extracted_info = None
    
    # Update session state with new extracted info if available
    if extracted_info:
        st.session_state.last_extracted_info = extracted_info
    
    # Use stored info from session state if available, otherwise show message
    display_info = st.session_state.last_extracted_info or extracted_info
    
    if not display_info:
        st.error("No data extracted from document")
        return

    # Display the main results table first
    st.markdown("#### Document Information")
    df = pd.DataFrame([
        {
            "Field": k.replace('_', ' ').title(),
            "Value": str(v)
        }
        for k, v in display_info.items()
    ])
    
    st.dataframe(
        df,
        column_config={
            "Field": st.column_config.TextColumn("Field", width=200),
            "Value": st.column_config.TextColumn("Extracted Value", width=300)
        },
        hide_index=True,
        use_container_width=True
    )
    
    # Show verification status separately
    st.markdown("#### Verification Status")
    status_col1, status_col2 = st.columns([1, 3])
    with status_col1:
        if verification_status:
            st.markdown("# ✅")
        else:
            st.markdown("# ❌")
    with status_col2:
        if verification_status:
            st.markdown("### Verification Successful")
        else:
            st.markdown("### Verification Failed")
    
    # Display compact summary
    st.markdown("#### Verification Summary")
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    with summary_col1:
        st.metric("Fields Extracted", len(display_info))
    with summary_col2:
        st.metric("Verification Status", "Pass" if verification_status else "Fail")
    with summary_col3:
        st.metric("Timestamp", datetime.now().strftime('%H:%M:%S'))
