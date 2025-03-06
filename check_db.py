from utils.db_check import check_database
from config.config import initialize_session_state
import streamlit as st

print("\n=== Checking Database State ===")
check_database()

print("\n=== Initializing Session State ===")
if 'customers' not in st.session_state:
    initialize_session_state()

print("\n=== Checking Session State ===")
print("Customers in session:", len(st.session_state.customers) if 'customers' in st.session_state else 0)
print("Alerts in session:", len(st.session_state.alerts) if 'alerts' in st.session_state else 0)

if 'alerts' in st.session_state:
    cus007_alerts = [a for a in st.session_state.alerts if a['customer_id'] == 'CUS007']
    print("\nCUS007 alerts in session state:", len(cus007_alerts))
    for alert in cus007_alerts:
        print(f"- {alert['type']}: {alert['status']}")
