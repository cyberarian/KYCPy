import streamlit as st
from utils.helpers import add_audit_log
from datetime import datetime, timedelta
from utils.database import update_customer, save_alert, get_customer_alerts
from modules.auth.session import login_required
from modules.auth.roles import Resource, Permission
from modules.risk.scoring import (  # Add new imports
    calculate_risk_score,
    get_risk_category,
    get_risk_factors,
    explain_risk_score,
    OCCUPATION_RISK
)

@login_required(Resource.RISK, Permission.READ)
def risk_assessment():
    """Handle risk assessment functionality"""
    st.title("Risk Assessment")
    
    tab1, tab2 = st.tabs(["Risk Scoring", "High Risk Customers"])
    
    with tab1:
        _handle_risk_scoring()
    
    with tab2:
        _handle_high_risk_customers()

def _handle_risk_scoring():
    """Handle individual customer risk scoring"""
    st.subheader("Customer Risk Calculation")
    
    customer_id = st.selectbox("Select customer to assess", list(st.session_state.customers.keys()),
                             format_func=lambda x: f"{x} - {st.session_state.customers[x]['full_name']}",
                             key="risk_assess_select")
    
    if customer_id:
        customer = st.session_state.customers[customer_id]
        _display_current_risk_factors(customer)
        _update_risk_factors(customer_id, customer)

def _display_current_risk_factors(customer):
    """Display current risk factors for customer"""
    with st.expander("Current Risk Factors", expanded=True):
        # Get detailed risk breakdown
        risk_factors = get_risk_factors(customer)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Customer:** {customer['full_name']}")
            st.markdown(f"**Occupation:** {customer['occupation']}")
            st.markdown(f"**Income Level:** {customer['income_level']}")
            st.markdown(f"**PEP Status:** {customer['pep_status']}")
        
        with col2:
            st.markdown(f"**Current Risk Score:** {customer['risk_score']}")
            
            risk_color = "red" if customer['risk_category'] == "High" else "orange" if customer['risk_category'] == "Medium" else "green"
            st.markdown(f"**Risk Category:** :{risk_color}[{customer['risk_category']}]")
            
            # Add risk factor breakdown
            st.markdown("### Risk Factor Breakdown")
            for factor, score in risk_factors.items():
                factor_color = "red" if score >= 0.7 else "orange" if score >= 0.3 else "green"
                st.markdown(f"- {factor.title()}: :{factor_color}[{score:.2f}]")
        
        # Add risk explanation
        st.markdown("### Risk Factors Explanation")
        for explanation in explain_risk_score(customer):
            st.warning(explanation)

def _update_risk_factors(customer_id, customer):
    """Update risk factors for customer"""
    with st.form("risk_update_form"):
        st.subheader("Update Risk Factors")
        
        # Add occupation risk indicator
        occupation = st.selectbox(
            "Occupation", 
            list(OCCUPATION_RISK.keys()),
            index=list(OCCUPATION_RISK.keys()).index(customer["occupation"]) if customer["occupation"] in OCCUPATION_RISK else 0,
            help=f"Occupation risk score: {OCCUPATION_RISK.get(customer['occupation'], 0.3)}"
        )
        
        suspicious = st.checkbox("Flag for Suspicious Activity", value=customer["suspicious_activity"])
        pep_status = st.checkbox("Politically Exposed Person", value=customer["pep_status"])
        
        income_level = st.selectbox(
            "Income Level",
            ["Low", "Medium", "High"],
            index=["Low", "Medium", "High"].index(customer["income_level"])
        )
        
        transaction_profile = st.text_area("Transaction Profile", value=customer["transaction_profile"])
        notes = st.text_area("Risk Notes", value=customer["notes"])
        
        # Manual risk override option
        st.subheader("Risk Override (Optional)")
        override = st.checkbox("Override calculated risk score")
        
        if override:
            manual_score = st.slider("Manual Risk Score", 0.0, 1.0, customer["risk_score"], 0.05)
        else:
            manual_score = None
        
        if st.form_submit_button("Update Risk Assessment"):
            updated_data = customer.copy()
            updated_data.update({
                "occupation": occupation,
                "suspicious_activity": suspicious,
                "pep_status": pep_status,
                "income_level": income_level,
                "transaction_profile": transaction_profile,
                "notes": notes
            })
            _save_risk_assessment(customer_id, updated_data, manual_score)

def _handle_high_risk_customers():
    """Handle high risk customers section"""
    st.subheader("High Risk Customers")
    
    high_risk_customers = {k: v for k, v in st.session_state.customers.items() 
                          if v["risk_category"] == "High"}
    
    if high_risk_customers:
        st.info(f"Found {len(high_risk_customers)} high risk customers requiring enhanced due diligence")
        
        for customer_id, customer in high_risk_customers.items():
            _display_high_risk_customer(customer_id, customer)
    else:
        st.success("No high risk customers found")

def _display_high_risk_customer(customer_id, customer):
    """Display high risk customer details"""
    with st.expander(f"{customer['full_name']} (ID: {customer_id})"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Risk Score:** {customer['risk_score']}")
            st.markdown(f"**Occupation:** {customer['occupation']}")
            st.markdown(f"**Income Level:** {customer['income_level']}")
            st.markdown(f"**PEP Status:** {customer['pep_status']}")
            st.markdown(f"**Transaction Profile:** {customer['transaction_profile']}")
        
        with col2:
            st.subheader("Risk Factors")
            _display_risk_warnings(customer)
            st.markdown(f"**Notes:** {customer['notes']}")
        
        # Add EDD Status Tracking
        st.subheader("EDD Status")
        _display_edd_status(customer_id)
        
        _display_customer_alerts(customer_id)
        _provide_edd_actions(customer_id)

def _display_risk_warnings(customer):
    """Display risk warning indicators"""
    if customer["pep_status"]:
        st.warning("⚠️ Politically Exposed Person")
    if customer["suspicious_activity"]:
        st.warning("⚠️ Suspicious Activity Flagged")
    if "high-value" in customer["transaction_profile"].lower():
        st.warning("⚠️ High-Value Transaction Pattern")
    if "cash" in customer["transaction_profile"].lower():
        st.warning("⚠️ Cash-Intensive Business")

def _display_customer_alerts(customer_id):
    """Display alerts for customer"""
    customer_alerts = [a for a in st.session_state.alerts if a['customer_id'] == customer_id]
    if customer_alerts:
        st.subheader("Related Alerts")
        for alert in customer_alerts:
            st.error(f"{alert['date']} - {alert['type']}: {alert['description']}")

def _provide_edd_actions(customer_id):
    """Provide Enhanced Due Diligence actions"""
    st.subheader("Enhanced Due Diligence Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Schedule EDD Interview", key=f"edd_{customer_id}"):
            _handle_edd_scheduling(customer_id, st.session_state.customers[customer_id])
    
    with col2:
        if st.button("Request Additional Documents", key=f"docs_{customer_id}"):
            _handle_document_request(customer_id, st.session_state.customers[customer_id])
    
    with col3:
        if st.button("Refer to Compliance", key=f"compliance_{customer_id}"):
            _handle_compliance_referral(customer_id, st.session_state.customers[customer_id])

@login_required(Resource.RISK, Permission.WRITE)
def _save_risk_assessment(customer_id, updated_data, manual_score):
    """Save risk assessment updates"""
    # Update customer data
    st.session_state.customers[customer_id].update(updated_data)
    
    # Calculate new risk score
    if manual_score is not None:
        new_score = manual_score
        add_audit_log("Risk Override", f"Manual risk override for customer {customer_id} to {manual_score}")
    else:
        new_score = calculate_risk_score(st.session_state.customers[customer_id])
    
    st.session_state.customers[customer_id]["risk_score"] = new_score
    st.session_state.customers[customer_id]["risk_category"] = get_risk_category(new_score)
    st.session_state.customers[customer_id]["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    
    add_audit_log("Risk Assessment", f"Updated risk assessment for customer {customer_id}")
    
    st.success(f"Risk assessment updated successfully")
    _check_high_risk_alert(customer_id, new_score)

def _check_high_risk_alert(customer_id, new_score):
    """Create alert if customer becomes high risk"""
    if get_risk_category(new_score) == "High" and st.session_state.customers[customer_id]["risk_category"] != "High":
        alert_id = f"ALT{len(st.session_state.alerts) + 1:03d}"
        new_alert = {
            "id": alert_id,
            "customer_id": customer_id,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "type": "Risk Escalation",
            "description": "Customer escalated to High Risk category",
            "status": "Open",
            "severity": "High",
            "assigned_to": "Risk Team"
        }
        st.session_state.alerts.append(new_alert)
        st.warning("Alert created due to High Risk classification")

@login_required(Resource.RISK, Permission.APPROVE)
def _handle_edd_scheduling(customer_id, customer):
    """Handle Enhanced Due Diligence interview scheduling"""
    st.subheader("📅 Schedule EDD Interview")
    
    with st.form("edd_scheduling_form"):
        col1, col2 = st.columns(2)
        with col1:
            interview_date = st.date_input(
                "Select Interview Date",
                min_value=datetime.now().date(),
                max_value=datetime.now().date() + timedelta(days=30)
            )
            interview_time = st.selectbox(
                "Select Time",
                ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
            )
        
        with col2:
            interview_type = st.radio(
                "Interview Type",
                ["Virtual", "In-Person"]
            )
            interviewer = st.selectbox(
                "Assigned Interviewer",
                ["Compliance Officer", "KYC Manager", "Risk Officer"]
            )
        
        reason = st.text_area(
            "Reason for EDD",
            placeholder="Explain why Enhanced Due Diligence is required..."
        )
        
        if st.form_submit_button("Schedule Interview"):
            if reason:
                try:
                    # Create new EDD alert
                    alert_id = f"EDD{datetime.now().strftime('%Y%m%d%H%M%S')}"  # More unique ID
                    edd_alert = {
                        "id": alert_id,
                        "customer_id": customer_id,
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "type": "EDD Interview",
                        "description": f"EDD Interview scheduled for {interview_date} {interview_time} ({interview_type})\nReason: {reason}",
                        "status": "Scheduled",
                        "severity": "High",
                        "assigned_to": interviewer,
                        "last_updated": datetime.now().strftime("%Y-%m-%d")
                    }
                    
                    # Save to database first
                    if save_alert(edd_alert):
                        # Update customer data
                        customer_data = customer.copy()
                        customer_data["notes"] = f"{customer_data.get('notes', '')}\n[{datetime.now().strftime('%Y-%m-%d')}] EDD Interview scheduled: {reason}"
                        customer_data["last_updated"] = datetime.now().strftime("%Y-%m-%d")
                        customer_data["verification_status"] = "Under Review"
                        
                        if update_customer(customer_id, customer_data):
                            st.session_state.customers[customer_id] = customer_data
                            add_audit_log("Schedule EDD", f"EDD Interview scheduled for customer {customer_id}")
                            st.success("✅ EDD Interview scheduled successfully")
                            st.experimental_rerun()
                        else:
                            st.error("Failed to update customer record")
                    else:
                        st.error("Failed to save alert")
                except Exception as e:
                    st.error(f"Error scheduling interview: {str(e)}")
                    print(f"Interview scheduling error details: {str(e)}")
            else:
                st.error("Please provide a reason for the EDD interview")

def _handle_document_request(customer_id, customer):
    """Handle additional document requests"""
    st.subheader("📄 Request Additional Documents")
    
    with st.form("document_request_form"):
        required_docs = st.multiselect(
            "Select Required Documents",
            [
                "Bank Statements (6 months)",
                "Tax Returns (2 years)",
                "Business License",
                "Source of Wealth Declaration",
                "Corporate Structure",
                "Partnership Agreements",
                "Proof of Address (Recent)",
                "Employment Contract",
                "Financial Statements",
                "Other"
            ]
        )
        
        if "Other" in required_docs:
            other_docs = st.text_input("Specify other documents required")
        
        urgency = st.select_slider(
            "Request Urgency",
            options=["Low", "Medium", "High"],
            value="Medium"
        )
        
        notes = st.text_area(
            "Additional Notes",
            placeholder="Provide context for the document request..."
        )
        
        if st.form_submit_button("Send Request"):
            if required_docs and notes:
                try:
                    # Create or update document request alert
                    existing_alert = next(
                        (a for a in st.session_state.alerts 
                         if a['customer_id'] == customer_id and a['type'] == "Document Request"),
                        None
                    )
                    
                    if existing_alert:
                        # Update existing alert
                        existing_alert['status'] = "Pending"
                        existing_alert['description'] += f"\n[{datetime.now().strftime('%Y-%m-%d')}] New request: {', '.join(required_docs)}"
                        doc_alert = existing_alert
                    else:
                        # Create new alert
                        doc_alert = {
                            "id": f"DOC{len(st.session_state.alerts) + 1:03d}",
                            "customer_id": customer_id,
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "type": "Document Request",
                            "description": f"Additional documents requested: {', '.join(required_docs)}\nUrgency: {urgency}\nNotes: {notes}",
                            "status": "Pending",
                            "severity": "High" if urgency == "High" else "Medium",
                            "assigned_to": "KYC Team"
                        }
                        st.session_state.alerts.append(doc_alert)
                    
                    # Update customer data
                    customer_data = customer.copy()
                    customer_data["notes"] = f"{customer_data.get('notes', '')}\n[{datetime.now().strftime('%Y-%m-%d')}] Document request: {', '.join(required_docs)}"
                    customer_data["last_updated"] = datetime.now().strftime("%Y-%m-%d")
                    customer_data["verification_status"] = "Documentation Pending"
                    
                    if update_customer(customer_id, customer_data):
                        st.session_state.customers[customer_id] = customer_data
                        add_audit_log("Document Request", f"Requested documents for {customer_id}")
                        st.success("✅ Document request sent successfully")
                        st.rerun()
                    else:
                        st.error("Failed to update customer record")
                except Exception as e:
                    st.error(f"Error requesting documents: {str(e)}")
            else:
                st.error("Please select documents and provide notes")

def _handle_compliance_referral(customer_id, customer):
    """Handle compliance team referrals"""
    st.subheader("⚠️ Refer to Compliance")
    
    with st.form("compliance_referral_form"):
        referral_type = st.selectbox(
            "Referral Type",
            [
                "Suspicious Activity",
                "High Risk Customer",
                "PEP Verification",
                "Complex Structure",
                "Unusual Transactions",
                "Other"
            ]
        )
        
        priority = st.select_slider(
            "Priority Level",
            options=["Low", "Medium", "High", "Critical"],
            value="High"
        )
        
        details = st.text_area(
            "Referral Details",
            placeholder="Provide detailed explanation for compliance review..."
        )
        
        if st.form_submit_button("Submit Referral"):
            if details:
                try:
                    # Create compliance referral alert
                    ref_alert = {
                        "id": f"REF{len(st.session_state.alerts) + 1:03d}",
                        "customer_id": customer_id,
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "type": "Compliance Referral",
                        "description": f"Type: {referral_type}\nPriority: {priority}\nDetails: {details}",
                        "status": "New",
                        "severity": "Critical" if priority in ["Critical", "High"] else "High",
                        "assigned_to": "Compliance Team"
                    }
                    
                    # Update customer data
                    customer_data = customer.copy()
                    customer_data["notes"] = f"{customer_data.get('notes', '')}\n[{datetime.now().strftime('%Y-%m-%d')}] Referred to compliance: {referral_type}"
                    customer_data["last_updated"] = datetime.now().strftime("%Y-%m-%d")
                    customer_data["risk_category"] = "High"
                    customer_data["verification_status"] = "Under Investigation"
                    
                    # Update database
                    if update_customer(customer_id, customer_data):
                        # Update session state
                        st.session_state.customers[customer_id] = customer_data
                        st.session_state.alerts.append(ref_alert)
                        
                        add_audit_log(
                            "Compliance Referral",
                            f"Customer {customer_id} referred to compliance for {referral_type}"
                        )
                        
                        st.success("✅ Compliance referral submitted successfully")
                        st.rerun()
                    else:
                        st.error("Failed to update customer record")
                except Exception as e:
                    st.error(f"Error submitting referral: {str(e)}")
            else:
                st.error("Please provide referral details")

def _schedule_edd_interview(customer_id):
    """Schedule Enhanced Due Diligence interview"""
    st.session_state.customers[customer_id]["notes"] += f"\n[{datetime.now().strftime('%Y-%m-%d')}] EDD Interview scheduled."
    add_audit_log("EDD Action", f"Scheduled EDD Interview for {customer_id}")
    st.success("Interview scheduled")

def _request_additional_documents(customer_id):
    """Request additional documents for EDD"""
    st.session_state.customers[customer_id]["notes"] += f"\n[{datetime.now().strftime('%Y-%m-%d')}] Additional documents requested."
    add_audit_log("EDD Action", f"Requested additional documents for {customer_id}")
    st.success("Document request sent")

def _refer_to_compliance(customer_id):
    """Refer customer to compliance team"""
    st.session_state.customers[customer_id]["notes"] += f"\n[{datetime.now().strftime('%Y-%m-%d')}] Referred to Compliance team."
    add_audit_log("EDD Action", f"Referred {customer_id} to Compliance")
    st.success("Referred to Compliance team")

def _display_edd_status(customer_id):
    """Display EDD action statuses"""
    try:
        # Get fresh data from database
        edd_alerts = get_customer_alerts(customer_id)
        
        if not edd_alerts:
            st.info("No EDD actions initiated yet")
            return
            
        st.write("---")
        st.subheader("📊 EDD Status Overview")
        
        # Group by alert type and get latest
        alert_types = {
            "EDD Interview": ("📅", "No interview scheduled"),
            "Document Request": ("📄", "No pending requests"),
            "Compliance Referral": ("⚠️", "Not referred")
        }
        
        cols = st.columns(len(alert_types))
        
        for (i, (alert_type, (icon, default_msg))) in enumerate(alert_types.items()):
            with cols[i]:
                latest_alert = next(
                    (alert for alert in sorted(edd_alerts, key=lambda x: x['date'], reverse=True)
                     if alert['type'] == alert_type),
                    None
                )
                _show_edd_status(alert_type, latest_alert, icon, default_msg)
        
        # Display history
        if edd_alerts:
            st.write("---")
            st.subheader("📝 EDD History")
            for alert in sorted(edd_alerts, key=lambda x: x['date'], reverse=True):
                with st.expander(f"{alert['type']} - {alert['date']}"):
                    _display_edd_details(alert)
                    
    except Exception as e:
        st.error(f"Error displaying EDD status: {str(e)}")
        print(f"EDD status error details: {str(e)}")

def _show_edd_status(title, alert, icon, default_msg):
    """Display EDD status with update capability"""
    st.markdown(f"### {icon} {title}")
    
    if alert:
        status_colors = {
            "New": "🟡",
            "Scheduled": "🟡",
            "In Progress": "🟠",
            "Pending": "🟡",
            "Completed": "🟢",
            "Under Review": "🟠",
            "Documentation Pending": "🟡",
            "Under Investigation": "🟠",
            "Closed": "⚫"
        }
        
        current_status = alert['status']
        st.markdown(f"**Current Status:** {status_colors.get(current_status, '⚪')} {current_status}")
        st.markdown(f"**Last Updated:** {alert.get('last_updated', alert['date'])}")
        st.markdown(f"**Assigned To:** {alert['assigned_to']}")
        
        with st.expander("Update Status"):
            with st.form(key=f"status_update_{alert['id']}"):
                new_status = st.selectbox(
                    "Status",
                    ["New", "Scheduled", "In Progress", "Pending", "Completed", "Closed"],
                    index=["New", "Scheduled", "In Progress", "Pending", "Completed", "Closed"].index(current_status)
                )
                
                note = st.text_area("Add Note (optional)")
                
                if st.form_submit_button("Update"):
                    try:
                        # Update alert data
                        alert['status'] = new_status
                        alert['last_updated'] = datetime.now().strftime("%Y-%m-%d")
                        if note:
                            alert['description'] += f"\n[{datetime.now().strftime('%Y-%m-%d')}] {note}"
                        
                        # Save to database
                        if save_alert(alert):
                            add_audit_log("EDD Update", f"Updated {title} status to {new_status}")
                            st.success("✅ Status updated")
                            st.experimental_rerun()
                        else:
                            st.error("Failed to update status in database")
                    except Exception as e:
                        st.error(f"Error updating status: {str(e)}")
                        print(f"Status update error details: {str(e)}")
    else:
        st.info(f"💡 {default_msg}")

def _display_edd_details(alert):
    """Display detailed EDD information"""
    st.markdown(f"**Status:** {alert['status']}")
    st.markdown(f"**Assigned:** {alert['assigned_to']}")
    st.markdown(f"**Description:**")
    
    # Split description into main description and notes
    description_parts = alert['description'].split('\n')
    st.write(description_parts[0])  # Main description
    
    if len(description_parts) > 1:
        st.markdown("#### Notes:")
        for note in description_parts[1:]:
            st.write(note)