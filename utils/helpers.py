import re
import streamlit as st
from datetime import datetime

def validate_nik(nik):
    """Validate Indonesian NIK (Identity Number)"""
    if not nik or not re.match(r'^\d{16}$', nik):
        return False
    return True

def calculate_risk_score(customer_data):
    """Calculate risk score based on various factors"""
    base_score = 0.2
    
    # Occupation risk
    high_risk_occupations = ["Business Owner", "Real Estate Developer", "Politician"]
    if customer_data["occupation"] in high_risk_occupations:
        base_score += 0.2
    
    # Income level risk
    if customer_data["income_level"] == "High":
        base_score += 0.1
    
    # PEP status risk
    if customer_data["pep_status"]:
        base_score += 0.3
    
    # Suspicious activity
    if customer_data["suspicious_activity"]:
        base_score += 0.2
        
    # Transaction profile risk
    if "high-value" in customer_data["transaction_profile"].lower():
        base_score += 0.1
    
    return min(round(base_score, 2), 1.0)

def get_risk_category(score):
    """Convert score to risk category"""
    if score < 0.3:
        return "Low"
    elif score < 0.7:
        return "Medium"
    else:
        return "High"

def add_audit_log(action, details):
    """Add entry to audit log"""
    st.session_state.audit_logs.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "details": details,
        "user": "Current User"
    })

def format_currency(amount):
    """Format amount to Indonesian Rupiah"""
    return f"Rp {amount:,.0f}"
