import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from modules.auth.session import login_required
from modules.auth.roles import Resource, Permission

@login_required(Resource.AUDIT, Permission.READ)
def audit_logs():
    """Display and manage audit logs"""
    st.title("Audit Logs")
    
    # Filter options
    col1, col2 = st.columns(2)
    
    with col1:
        date_range = st.selectbox(
            "Date Range",
            ["Last 24 Hours", "Last 7 Days", "Last 30 Days", "All Time"],
            index=1
        )
    
    with col2:
        action_type = st.multiselect(
            "Filter by Action",
            ["View Customer Details", "Add Customer", "Edit Customer", "Delete Customer",
             "Risk Assessment", "Document Verification", "Create Alert", "Alert Management",
             "Add Transaction", "EDD Action"],
            default=["Add Customer", "Create Alert", "Risk Assessment"]
        )
    
    # Apply filters to audit logs
    if st.session_state.audit_logs:
        df = pd.DataFrame(st.session_state.audit_logs)
        
        # Apply date filter
        if date_range != "All Time":
            current_time = datetime.now()
            if date_range == "Last 24 Hours":
                cutoff = current_time - timedelta(days=1)
            elif date_range == "Last 7 Days":
                cutoff = current_time - timedelta(days=7)
            else:  # Last 30 Days
                cutoff = current_time - timedelta(days=30)
                
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df[df['timestamp'] >= cutoff]
        
        # Apply action type filter
        if action_type:
            df = df[df['action'].isin(action_type)]
        
        if not df.empty:
            # Display filtered audit logs
            st.dataframe(
                df.sort_values('timestamp', ascending=False),
                use_container_width=True
            )
            
            # Export functionality
            if st.button("Export Audit Log"):
                csv = df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    "audit_log.csv",
                    "text/csv",
                    key='download-csv'
                )
        else:
            st.info("No audit logs match the selected filters")
    else:
        st.info("No audit logs available")

@login_required(Resource.AUDIT, Permission.WRITE)
def _add_audit_note(log_id, note):
    """Add note to audit log"""
    pass

@login_required(Resource.AUDIT, Permission.ADMIN)
def _export_audit_logs():
    """Export audit logs"""
    pass
