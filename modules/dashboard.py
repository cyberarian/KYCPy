import streamlit as st
import pandas as pd
from datetime import datetime
from modules.auth.session import login_required
from modules.auth.roles import Resource, Permission, check_access

@login_required(Resource.CUSTOMER, Permission.READ)
def display_dashboard():
    """Display the main KYC Analysis Dashboard"""
    st.title("KYCPy Analysis Dashboard")
    
    # Header metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Customers", len(st.session_state.customers), "+2 today")
    with col2:
        open_alerts = sum(1 for alert in st.session_state.alerts if alert["status"] == "Open")
        st.metric("Open Alerts", open_alerts, "-1 since yesterday")
    with col3:
        high_risk = sum(1 for c in st.session_state.customers.values() if c["risk_category"] == "High")
        st.metric("High Risk Customers", high_risk, "+1 this week")
    with col4:
        pending = sum(1 for c in st.session_state.customers.values() if c["verification_status"] == "Under Review")
        st.metric("Pending Verifications", pending, "")

    # Risk distribution chart
    _display_risk_distribution()
    
    # Latest alerts
    _display_latest_alerts()
    
    # Transaction summary
    _display_transaction_summary()
    
    # Verification status
    _display_verification_status()

def _display_metrics():
    """Display dashboard metrics"""
    if check_access(st.session_state.user.role, Resource.TRANSACTION, Permission.READ):
        _display_transaction_metrics()
    
    if check_access(st.session_state.user.role, Resource.ALERT, Permission.READ):
        _display_alert_metrics()
        
    if check_access(st.session_state.user.role, Resource.RISK, Permission.READ):
        _display_risk_metrics()

def _display_risk_distribution():
    """Display risk distribution chart"""
    st.subheader("Customer Risk Distribution")
    risk_counts = {"Low": 0, "Medium": 0, "High": 0}
    for customer in st.session_state.customers.values():
        risk_counts[customer["risk_category"]] += 1
    
    risk_df = pd.DataFrame({
        "Risk Category": risk_counts.keys(),
        "Count": risk_counts.values()
    })
    st.bar_chart(risk_df.set_index("Risk Category"))

def _display_latest_alerts():
    """Display latest alerts section"""
    st.subheader("Latest Alerts")
    sorted_alerts = sorted(st.session_state.alerts, key=lambda x: x["date"], reverse=True)[:3]
    for alert in sorted_alerts:
        customer_name = st.session_state.customers[alert["customer_id"]]["full_name"]
        severity_color = "red" if alert["severity"] == "High" else "orange" if alert["severity"] == "Medium" else "green"
        st.info(f"**{alert['type']}** for {customer_name} - {alert['description']} ({alert['date']})")

def _display_transaction_summary():
    """Display transaction summary section"""
    st.subheader("Recent Transactions")
    
    # Get last 5 transactions
    recent_transactions = sorted(
        st.session_state.transaction_logs,
        key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d"),
        reverse=True
    )[:5]
    
    if recent_transactions:
        transactions_df = pd.DataFrame(recent_transactions)
        transactions_df["customer_name"] = transactions_df["customer_id"].apply(
            lambda x: st.session_state.customers[x]["full_name"]
        )
        transactions_df["amount"] = transactions_df["amount"].apply(
            lambda x: f"Rp {x:,.0f}"
        )
        st.dataframe(
            transactions_df[["date", "customer_name", "type", "amount", "risk_flag"]],
            use_container_width=True
        )

def _display_verification_status():
    """Display verification status summary"""
    st.subheader("Verification Status")
    
    verification_counts = _get_status_metrics()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Verified", verification_counts["Verified"])
    with col2:
        st.metric("Under Review", verification_counts["Under Review"])
    with col3:
        # Changed from "Rejected" to "Failed"
        st.metric("Failed", verification_counts["Failed"])

def _get_status_metrics():
    """Get verification status metrics"""
    status_counts = {
        "Verified": 0,
        "Under Review": 0,
        "Manual Review": 0,
        "Documentation Pending": 0,
        "Under Investigation": 0,
        "Failed": 0  # Changed from "Rejected" to match our status types
    }
    
    for customer in st.session_state.customers.values():
        status = customer.get('verification_status', 'Under Review')
        if status in status_counts:
            status_counts[status] += 1
        else:
            status_counts['Under Review'] += 1  # Default for unknown status
    
    return status_counts

def _get_alert_metrics():
    """Get alert metrics"""
    alert_stats = {
        "Open": 0,
        "In Progress": 0,
        "Manual Review": 0,
        "Pending": 0,
        "Completed": 0,
        "Closed": 0
    }
    
    for alert in st.session_state.alerts:
        status = alert.get('status', 'Open')
        if status in alert_stats:
            alert_stats[status] += 1
        else:
            alert_stats['Open'] += 1
    
    return alert_stats

def _display_transaction_metrics():
    """Display transaction-related metrics"""
    transactions = st.session_state.transaction_logs
    total_transactions = len(transactions)
    high_risk_transactions = sum(1 for t in transactions if t["risk_flag"] == "High")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Transactions", total_transactions)
    with col2:
        st.metric("High Risk Transactions", high_risk_transactions)

def _display_alert_metrics():
    """Display alert-related metrics"""
    alert_stats = _get_alert_metrics()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Open Alerts", alert_stats["Open"])
    with col2:
        st.metric("In Progress", alert_stats["In Progress"])

def _display_risk_metrics():
    """Display risk-related metrics"""
    risk_counts = {"Low": 0, "Medium": 0, "High": 0}
    for customer in st.session_state.customers.values():
        risk_counts[customer["risk_category"]] += 1
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Low Risk", risk_counts["Low"])
    with col2:
        st.metric("Medium Risk", risk_counts["Medium"])
    with col3:
        st.metric("High Risk", risk_counts["High"])
