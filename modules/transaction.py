import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.helpers import add_audit_log, format_currency
from modules.auth.session import login_required
from modules.auth.roles import Resource, Permission

@login_required(Resource.TRANSACTION, Permission.READ)
def transaction_monitoring():
    """Handle transaction monitoring functionality"""
    st.title("Transaction Monitoring")
    
    tab1, tab2, tab3 = st.tabs(["Transaction Log", "Add Transaction", "Analytics"])
    
    with tab1:
        _display_transaction_log()
    
    with tab2:
        _add_transaction()
    
    with tab3:
        _display_analytics()

def _display_transaction_log():
    """Display and filter transaction logs"""
    st.subheader("Transaction Monitoring")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        customer_filter = st.selectbox(
            "Filter by Customer",
            ["All Customers"] + list(st.session_state.customers.keys()),
            format_func=lambda x: x if x == "All Customers" else f"{x} - {st.session_state.customers[x]['full_name']}"
        )
    
    with col2:
        type_filter = st.multiselect(
            "Filter by Type",
            ["Transfer", "Cash Deposit", "Cash Withdrawal", "Salary", "Other"],
            default=["Transfer", "Cash Deposit", "Cash Withdrawal", "Salary", "Other"]
        )
    
    with col3:
        risk_filter = st.radio(
            "Risk Flag Filter",
            ["All Transactions", "Flagged Only", "Unflagged Only"]
        )
    
    filtered_transactions = _apply_transaction_filters(customer_filter, type_filter, risk_filter)
    _display_filtered_transactions(filtered_transactions)

def _add_transaction():
    """Add new transaction functionality"""
    st.subheader("Add New Transaction")
    
    with st.form("add_transaction_form"):
        customer_id = st.selectbox(
            "Select Customer",
            list(st.session_state.customers.keys()),
            format_func=lambda x: f"{x} - {st.session_state.customers[x]['full_name']}",
            key="transaction_customer_select"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            transaction_type = st.selectbox(
                "Transaction Type",
                ["Transfer", "Cash Deposit", "Cash Withdrawal", "Salary", "Other"]
            )
            date = st.date_input("Transaction Date", value=datetime.today())
        
        with col2:
            amount = st.number_input("Amount (IDR)", min_value=0.0, value=0.0, step=1000000.0)
            destination = st.text_input(
                "Destination",
                placeholder="e.g., Account number, recipient name, or 'Self Account'"
            )
        
        notes = st.text_area("Transaction Notes")
        risk_flag = st.checkbox("Flag as Suspicious")
        
        if st.form_submit_button("Add Transaction"):
            if _validate_transaction(amount, destination):
                _save_transaction(customer_id, transaction_type, date, amount, destination, notes, risk_flag)

def _apply_transaction_filters(customer_filter, type_filter, risk_filter):
    """Apply filters to transactions"""
    filtered_transactions = st.session_state.transaction_logs
    
    if customer_filter != "All Customers":
        filtered_transactions = [t for t in filtered_transactions if t["customer_id"] == customer_filter]
    
    if type_filter:
        filtered_transactions = [t for t in filtered_transactions if t["type"] in type_filter]
    
    if risk_filter == "Flagged Only":
        filtered_transactions = [t for t in filtered_transactions if t["risk_flag"]]
    elif risk_filter == "Unflagged Only":
        filtered_transactions = [t for t in filtered_transactions if not t["risk_flag"]]
    
    return filtered_transactions

def _display_filtered_transactions(filtered_transactions):
    """Display filtered transactions and transaction details"""
    if filtered_transactions:
        df = pd.DataFrame(filtered_transactions)
        df["customer_name"] = df["customer_id"].apply(lambda x: st.session_state.customers[x]["full_name"])
        df["formatted_amount"] = df["amount"].apply(lambda x: f"Rp {x:,.0f}")
        
        display_columns = ["id", "customer_name", "date", "type", "formatted_amount", "destination", "notes", "risk_flag"]
        st.dataframe(
            df[display_columns].rename(columns={"formatted_amount": "amount", "customer_name": "customer"}),
            use_container_width=True
        )
        
        _handle_transaction_details(filtered_transactions)
    else:
        st.info("No transactions match the selected filters")

def _handle_transaction_details(transactions):
    """Handle individual transaction details and updates"""
    selected_transaction = st.selectbox(
        "Select transaction for details",
        [t["id"] for t in transactions],
        format_func=lambda x: f"{x} - {next((t['type'] for t in transactions if t['id'] == x), '')} - Rp {next((t['amount'] for t in transactions if t['id'] == x), 0):,.0f}"
    )
    
    if selected_transaction:
        transaction = next((t for t in transactions if t["id"] == selected_transaction), None)
        if transaction:
            _display_transaction_details(transaction)

def _display_transaction_details(transaction):
    """Display detailed transaction information and risk review options"""
    with st.expander("Transaction Details", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            _display_basic_details(transaction)
        
        with col2:
            _display_additional_details(transaction)
        
        _handle_risk_review(transaction)

def _validate_transaction(amount, destination):
    """Validate transaction input"""
    if amount <= 0:
        st.error("Amount must be greater than zero")
        return False
    elif not destination:
        st.error("Please enter a destination")
        return False
    return True

def _save_transaction(customer_id, transaction_type, date, amount, destination, notes, risk_flag):
    """Save new transaction and handle related actions"""
    transaction_id = f"TRX{len(st.session_state.transaction_logs) + 1:03d}"
    
    new_transaction = {
        "id": transaction_id,
        "customer_id": customer_id,
        "date": date.strftime("%Y-%m-%d"),
        "type": transaction_type,
        "amount": amount,
        "destination": destination,
        "notes": notes,
        "risk_flag": risk_flag
    }
    
    st.session_state.transaction_logs.append(new_transaction)
    add_audit_log("Add Transaction", f"Added new transaction {transaction_id} for customer {customer_id}")
    
    _check_suspicious_patterns(customer_id, transaction_type)
    st.success(f"Transaction {transaction_id} added successfully")

def _check_suspicious_patterns(customer_id, transaction_type):
    """Check for suspicious transaction patterns"""
    customer_transactions = [t for t in st.session_state.transaction_logs if t["customer_id"] == customer_id]
    
    recent_cash_deposits = [
        t for t in customer_transactions 
        if t["type"] == "Cash Deposit" 
        and (datetime.strptime(t["date"], "%Y-%m-%d") > datetime.now() - timedelta(days=7))
    ]
    
    if transaction_type == "Cash Deposit" and len(recent_cash_deposits) >= 3:
        _create_structuring_alert(customer_id)

def _create_structuring_alert(customer_id):
    """Create alert for potential structuring"""
    alert_id = f"ALT{len(st.session_state.alerts) + 1:03d}"
    new_alert = {
        "id": alert_id,
        "customer_id": customer_id,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "type": "Suspicious Pattern",
        "description": "Multiple cash deposits detected within short period. Possible structuring.",
        "status": "Open",
        "severity": "High",
        "assigned_to": "Risk Team"
    }
    st.session_state.alerts.append(new_alert)
    st.warning("Alert created for suspicious transaction pattern")

def _display_basic_details(transaction):
    """Display basic transaction details"""
    st.markdown(f"**Transaction ID:** {transaction['id']}")
    st.markdown(f"**Customer:** {st.session_state.customers[transaction['customer_id']]['full_name']}")
    st.markdown(f"**Type:** {transaction['type']}")
    st.markdown(f"**Amount:** Rp {transaction['amount']:,.0f}")

def _display_additional_details(transaction):
    """Display additional transaction details"""
    st.markdown(f"**Date:** {transaction['date']}")
    st.markdown(f"**Destination:** {transaction['destination']}")
    st.markdown(f"**Risk Flag:** {'🚩 Yes' if transaction['risk_flag'] else '✓ No'}")
    st.markdown(f"**Notes:** {transaction['notes']}")

def _handle_risk_review(transaction):
    """Handle transaction risk review updates"""
    st.subheader("Risk Review")
    
    col1, col2 = st.columns(2)
    with col1:
        risk_flag = st.checkbox("Flag as Suspicious", value=transaction["risk_flag"])
    
    with col2:
        notes = st.text_input("Additional Notes", value=transaction["notes"])
    
    if st.button("Update Transaction"):
        _update_transaction_risk(transaction, risk_flag, notes)

@login_required(Resource.TRANSACTION, Permission.WRITE)
def _flag_transaction(transaction_id, reason):
    """Flag suspicious transaction"""
    # ... existing code ...

def _update_transaction_risk(transaction, risk_flag, notes):
    """Update transaction risk status and handle related actions"""
    for t in st.session_state.transaction_logs:
        if t["id"] == transaction["id"]:
            t["risk_flag"] = risk_flag
            t["notes"] = notes
    
    if risk_flag and not transaction["risk_flag"]:
        _create_suspicious_transaction_alert(transaction)
        st.session_state.customers[transaction["customer_id"]]["suspicious_activity"] = True
        add_audit_log("Transaction Monitoring", f"Flagged transaction {transaction['id']} as suspicious")
        st.warning("Alert created for suspicious transaction")
    else:
        add_audit_log("Transaction Monitoring", f"Updated transaction {transaction['id']}")
        st.success("Transaction updated")
    
    st.experimental_rerun()

def _create_suspicious_transaction_alert(transaction):
    """Create alert for suspicious transaction"""
    alert_id = f"ALT{len(st.session_state.alerts) + 1:03d}"
    new_alert = {
        "id": alert_id,
        "customer_id": transaction["customer_id"],
        "date": datetime.now().strftime("%Y-%m-%d"),
        "type": "Suspicious Transaction",
        "description": f"Suspicious transaction flagged: {transaction['type']} of Rp {transaction['amount']:,.0f}",
        "status": "Open",
        "severity": "High",
        "assigned_to": "Risk Team"
    }
    st.session_state.alerts.append(new_alert)

def _display_analytics():
    """Display transaction analytics and insights"""
    st.subheader("Transaction Analytics")
    
    if st.session_state.transaction_logs:
        df = pd.DataFrame(st.session_state.transaction_logs)
        
        # Time period selector
        period = st.selectbox(
            "Analysis Period",
            ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"]
        )
        
        # Filter data based on selected period
        current_date = datetime.now()
        if period != "All Time":
            days = int(period.split()[1])
            cutoff_date = current_date - timedelta(days=days)
            df['date'] = pd.to_datetime(df['date'])
            df = df[df['date'] >= cutoff_date]
        
        # Display key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_volume = df['amount'].sum()
            st.metric("Total Volume", format_currency(total_volume))
        
        with col2:
            avg_transaction = df['amount'].mean()
            st.metric("Average Transaction", format_currency(avg_transaction))
        
        with col3:
            total_transactions = len(df)
            st.metric("Total Transactions", total_transactions)
        
        with col4:
            flagged_count = df['risk_flag'].sum()
            st.metric("Flagged Transactions", flagged_count)
        
        # Transaction type distribution
        st.subheader("Transaction Type Distribution")
        type_dist = df['type'].value_counts()
        st.bar_chart(type_dist)
        
        # Risk flagged transactions trend
        st.subheader("Risk Flagged Transactions")
        risk_df = df[df['risk_flag']].copy()
        if not risk_df.empty:
            risk_df['date'] = pd.to_datetime(risk_df['date'])
            risk_trend = risk_df.groupby('date').size()
            st.line_chart(risk_trend)
        else:
            st.info("No risk-flagged transactions in selected period")
        
        # Largest transactions
        st.subheader("Top 5 Largest Transactions")
        largest_df = df.nlargest(5, 'amount')[['date', 'customer_id', 'type', 'amount', 'risk_flag']]
        largest_df['customer_name'] = largest_df['customer_id'].apply(
            lambda x: st.session_state.customers[x]['full_name']
        )
        largest_df['amount'] = largest_df['amount'].apply(format_currency)
        st.dataframe(
            largest_df[['date', 'customer_name', 'type', 'amount', 'risk_flag']],
            use_container_width=True
        )
    else:
        st.info("No transaction data available for analysis")

@login_required(Resource.TRANSACTION, Permission.APPROVE)
def _approve_large_transaction(transaction_id):
    """Approve large transaction"""
    # ... existing code ...
