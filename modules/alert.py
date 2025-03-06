import streamlit as st
from utils.helpers import add_audit_log
from datetime import datetime
from modules.auth.session import login_required
from modules.auth.roles import Resource, Permission

@login_required(Resource.ALERT, Permission.READ)
def alert_management():
    """Handle alert management functionality"""
    st.title("Alert Management")
    
    tab1, tab2 = st.tabs(["Active Alerts", "Create Alert"])
    
    with tab1:
        st.subheader("Active Alerts")
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.multiselect(
                "Filter by Status",
                ["Open", "In Progress", "Manual Review", "Pending", "Scheduled", "Completed", "Closed"],  # Added statuses
                default=["Open", "In Progress", "Manual Review", "Pending"]
            )
        
        with col2:
            severity_filter = st.multiselect(
                "Filter by Severity",
                ["Low", "Medium", "High"],
                default=["Medium", "High"]
            )
        
        with col3:
            alert_type_filter = st.multiselect(
                "Filter by Type",
                ["Unusual Transaction", "Document Expiry", "Risk Escalation", 
                 "Document Verification Failure", "Suspicious Activity"],
                default=["Unusual Transaction", "Risk Escalation", "Suspicious Activity"]
            )
        
        # Filter alerts based on selections
        filtered_alerts = [
            alert for alert in st.session_state.alerts
            if alert["status"] in status_filter
            and alert["severity"] in severity_filter
            and alert["type"] in alert_type_filter
        ]
        
        if filtered_alerts:
            for alert in filtered_alerts:
                customer = st.session_state.customers.get(alert["customer_id"], {"full_name": "Unknown Customer"})
                
                # Determine alert color based on severity
                alert_color = "red" if alert["severity"] == "High" else "orange" if alert["severity"] == "Medium" else "green"
                
                with st.expander(f"[{alert['severity']}] {alert['type']} - {customer['full_name']} ({alert['date']})"):
                    _display_alert_details(alert, customer, alert_color)
        else:
            st.info("No alerts match the selected filters")
    
    with tab2:
        _create_new_alert()

def _display_alert_details(alert, customer, alert_color):
    """Display alert details and action buttons"""
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"**Alert ID:** {alert['id']}")
        st.markdown(f"**Customer:** {customer['full_name']} ({alert['customer_id']})")
        st.markdown(f"**Description:** {alert['description']}")
        st.markdown(f"**Date Created:** {alert['date']}")
        st.markdown(f"**Assigned To:** {alert['assigned_to']}")
    
    with col2:
        # Add status update dropdown
        new_status = st.selectbox(
            "Status",
            ["Open", "In Progress", "Scheduled", "Pending", "Completed", "Closed"],
            index=["Open", "In Progress", "Scheduled", "Pending", "Completed", "Closed"].index(alert['status']),
            key=f"status_{alert['id']}"
        )
        st.markdown(f"**Severity:** :{alert_color}[{alert['severity']}]")
        
        if new_status != alert['status']:
            alert['status'] = new_status
            add_audit_log("Alert Update", f"Updated status of alert {alert['id']} to {new_status}")
            st.success(f"Status updated to {new_status}")
    
    _handle_alert_actions(alert)

@login_required(Resource.ALERT, Permission.WRITE)
def _handle_alert_actions(alert):
    """Handle alert response actions"""
    st.subheader("Alert Response")
    
    response_text = st.text_area("Response Notes", key=f"response_{alert['id']}")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if alert["status"] == "Open" and st.button("Start Investigation", key=f"start_{alert['id']}"):
            _start_investigation(alert)
            st.experimental_rerun()
    
    with col2:
        if alert["status"] != "Closed" and st.button("Close Alert", key=f"close_{alert['id']}"):
            if _close_alert(alert, response_text):
                st.experimental_rerun()
    
    with col3:
        if st.button("Escalate", key=f"escalate_{alert['id']}"):
            _escalate_alert(alert, response_text)
            st.experimental_rerun()

@login_required(Resource.ALERT, Permission.WRITE)
def _create_new_alert():
    """Create a new alert"""
    st.subheader("Create New Alert")
    
    with st.form("create_alert_form"):
        customer_id = st.selectbox("Select Customer", list(st.session_state.customers.keys()),
                                  format_func=lambda x: f"{x} - {st.session_state.customers[x]['full_name']}")
        
        alert_type = st.selectbox("Alert Type", [
            "Unusual Transaction", "Document Expiry", "Risk Escalation", 
            "Document Verification Failure", "Suspicious Activity", "Other"
        ])
        
        description = st.text_area("Alert Description")
        severity = st.select_slider("Severity", options=["Low", "Medium", "High"], value="Medium")
        assigned_to = st.selectbox("Assign To", ["KYC Team", "Risk Team", "Compliance Team", "Current User"])
        
        if st.form_submit_button("Create Alert"):
            if _save_new_alert(customer_id, alert_type, description, severity, assigned_to):
                st.success(f"Alert created successfully")

def _save_new_alert(customer_id, alert_type, description, severity, assigned_to):
    """Save a new alert to session state"""
    if not description:
        st.error("Please enter an alert description")
        return False
    
    alert_id = f"ALT{len(st.session_state.alerts) + 1:03d}"
    
    new_alert = {
        "id": alert_id,
        "customer_id": customer_id,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "type": alert_type,
        "description": description,
        "status": "Open",
        "severity": severity,
        "assigned_to": assigned_to
    }
    
    st.session_state.alerts.append(new_alert)
    st.session_state.customers[customer_id]["notes"] += f"\n[{datetime.now().strftime('%Y-%m-%d')}] Alert created: {description}"
    add_audit_log("Create Alert", f"Created new alert {alert_id} for customer {customer_id}")
    
    return True

def _start_investigation(alert):
    """Start investigation on an alert"""
    alert["status"] = "In Progress"
    alert["assigned_to"] = "Current User"
    add_audit_log("Alert Management", f"Started investigation on alert {alert['id']}")
    st.success("Status updated to In Progress")

def _close_alert(alert, response_text):
    """Close an alert"""
    if not response_text:
        st.error("Please enter response notes before closing the alert")
        return False
    
    alert["status"] = "Closed"
    if alert["customer_id"] in st.session_state.customers:
        st.session_state.customers[alert["customer_id"]]["notes"] += f"\n[{datetime.now().strftime('%Y-%m-%d')}] Alert response: {response_text}"
    add_audit_log("Alert Management", f"Closed alert {alert['id']}")
    st.success("Alert closed successfully")
    return True

@login_required(Resource.ALERT, Permission.APPROVE)
def _escalate_alert(alert, response_text):
    """Escalate an alert"""
    alert["severity"] = "High"
    alert["assigned_to"] = "Compliance Team"
    if response_text and alert["customer_id"] in st.session_state.customers:
        st.session_state.customers[alert["customer_id"]]["notes"] += f"\n[{datetime.now().strftime('%Y-%m-%d')}] Alert escalated: {response_text}"
    add_audit_log("Alert Management", f"Escalated alert {alert['id']}")
    st.warning("Alert escalated to Compliance Team")
