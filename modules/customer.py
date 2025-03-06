import streamlit as st
import pandas as pd
from datetime import datetime
from utils.helpers import validate_nik, add_audit_log, calculate_risk_score, get_risk_category
from utils.database import (
    add_customer, 
    update_customer, 
    delete_customer, 
    get_all_customers,
    archive_customer,
    get_archived_customers  # Add this import
)
from modules.hybrid_verifier import HybridDocumentVerifier
import os
import io
import base64
import json
from PIL import Image
import google.generativeai as genai
from modules.auth.session import login_required
from modules.auth.roles import Resource, Permission

@login_required(Resource.CUSTOMER, Permission.READ)
def customer_management():
    """Handle customer CRUD operations"""
    st.title("Customer Management")
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "View Customers", 
        "Add Customer", 
        "Edit Customer", 
        "Verify Customer",  # New tab
        "Delete Customer",
        "Archived Customers"  # New tab
    ])
    
    with tab1:
        _view_customers()
    
    with tab2:
        _add_customer()
    
    with tab3:
        _edit_customer()
    
    with tab4:
        st.subheader("Verify Customer")
        customer_id = st.selectbox(
            "Select Customer to Verify",
            list(st.session_state.customers.keys()),
            format_func=lambda x: f"{x} - {st.session_state.customers[x]['full_name']}"
        )
        
        if customer_id:
            customer = st.session_state.customers[customer_id]
            verify_customer_documents(customer_id, customer)
    
    with tab5:
        _delete_customer()

    with tab6:
        _view_archived_customers()

def _view_customers():
    """View and filter customer database"""
    st.subheader("Customer Database")
    
    # Search and filter options
    search_col, filter_col = st.columns([1, 1])
    with search_col:
        search_term = st.text_input("Search by Name or ID")
    with filter_col:
        risk_filter = st.multiselect(
            "Filter by Risk Category",
            ["Low", "Medium", "High"],
            default=["Low", "Medium", "High"]
        )
    
    # Convert customers dict to DataFrame for display
    df = pd.DataFrame(st.session_state.customers.values())
    
    # Apply filters
    if search_term:
        df = df[df['full_name'].str.contains(search_term, case=False) | 
               df['id'].str.contains(search_term, case=False)]
    
    if risk_filter:
        df = df[df['risk_category'].isin(risk_filter)]
    
    if not df.empty:
        # Display customers
        display_cols = ['id', 'full_name', 'risk_category', 'verification_status', 'occupation']
        st.dataframe(df[display_cols], use_container_width=True)
        
        # Customer details expansion
        _display_customer_details(df)
    else:
        st.warning("No customers found matching the criteria")

def _display_customer_details(df):
    """Display detailed customer information"""
    customer_id = st.selectbox("Select customer to view details", df['id'])
    if customer_id:
        customer = st.session_state.customers[customer_id]
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(f"Customer: {customer['full_name']}")
            st.text(f"ID: {customer['id']}")
            st.text(f"NIK: {customer['nik']}")
            st.text(f"Date of Birth: {customer['dob']}")
            st.text(f"Address: {customer['address']}")
            st.text(f"Occupation: {customer['occupation']}")
            st.text(f"Income Level: {customer['income_level']}")
        
        with col2:
            st.subheader("Risk Information")
            risk_color = "red" if customer['risk_category'] == "High" else "orange" if customer['risk_category'] == "Medium" else "green"
            st.markdown(f"Risk Score: **:{risk_color}[{customer['risk_score']}]**")
            st.markdown(f"Risk Category: **:{risk_color}[{customer['risk_category']}]**")
            st.text(f"PEP Status: {customer['pep_status']}")
            st.text(f"Verification Status: {customer['verification_status']}")
            st.text(f"Suspicious Activity: {customer['suspicious_activity']}")
        
        _display_additional_info(customer_id, customer)
        add_audit_log("View Customer Details", f"Viewed details of customer {customer_id}")

def _display_additional_info(customer_id, customer):
    """Display documents, notes, and related information"""
    st.subheader("Documents")
    st.write(", ".join(customer['documents']))
    
    st.subheader("Notes")
    st.write(customer['notes'])
    
    st.subheader("Transaction Profile")
    st.write(customer['transaction_profile'])
    
    # Related alerts
    _display_related_alerts(customer_id)
    
    # Customer transactions
    _display_customer_transactions(customer_id)

def _display_related_alerts(customer_id):
    """Display alerts related to the customer"""
    st.subheader("Related Alerts")
    customer_alerts = [a for a in st.session_state.alerts if a['customer_id'] == customer_id]
    if customer_alerts:
        alerts_df = pd.DataFrame(customer_alerts)
        st.dataframe(alerts_df[['date', 'type', 'description', 'status', 'severity']], use_container_width=True)
    else:
        st.info("No alerts for this customer")

def _display_customer_transactions(customer_id):
    """Display customer transactions"""
    st.subheader("Recent Transactions")
    customer_transactions = [t for t in st.session_state.transaction_logs if t['customer_id'] == customer_id]
    if customer_transactions:
        transactions_df = pd.DataFrame(customer_transactions)
        transactions_df['amount'] = transactions_df['amount'].apply(lambda x: f"Rp {x:,.0f}")
        st.dataframe(transactions_df[['date', 'type', 'amount', 'destination', 'notes', 'risk_flag']], use_container_width=True)
    else:
        st.info("No recent transactions")

@login_required(Resource.CUSTOMER, Permission.WRITE)
def _add_customer():
    """Add a new customer"""
    st.subheader("Add New Customer")
    
    with st.form("add_customer_form"):
        new_customer = _customer_form()
        
        if st.form_submit_button("Register Customer"):
            if _validate_customer_data(new_customer):
                _save_new_customer(new_customer)

def _edit_customer():
    """Edit existing customer"""
    st.subheader("Edit Customer")
    
    customer_id = st.selectbox("Select customer to edit", 
                             list(st.session_state.customers.keys()),
                             format_func=lambda x: f"{x} - {st.session_state.customers[x]['full_name']}")
    
    if customer_id:
        with st.form("edit_customer_form"):
            updated_data = _customer_form(st.session_state.customers[customer_id])
            
            if st.form_submit_button("Update Customer"):
                if _validate_customer_data(updated_data):
                    _update_customer(customer_id, updated_data)

@login_required(Resource.CUSTOMER, Permission.DELETE)
def _delete_customer():
    """Delete customer functionality"""
    st.subheader("Delete Customer")
    
    customer_id = st.selectbox("Select customer to delete", 
                             list(st.session_state.customers.keys()),
                             format_func=lambda x: f"{x} - {st.session_state.customers[x]['full_name']}",
                             key="delete_customer_select")
    
    if customer_id:
        _handle_customer_deletion(customer_id)

def _view_archived_customers():
    """View archived customer records"""
    st.subheader("📁 Archived Customers")
    
    archived = get_archived_customers()
    
    if not archived:
        st.info("No archived customers found")
        return
        
    # Convert to DataFrame for display
    df = pd.DataFrame([
        {
            "ID": k,
            "Name": v["full_name"],
            "Archive Date": v["archive_date"],
            "Reason": v["archive_reason"]
        } 
        for k, v in archived.items()
    ])
    
    st.dataframe(df, use_container_width=True)
    
    # View detailed archived customer info
    selected_id = st.selectbox(
        "Select customer to view details",
        list(archived.keys()),
        format_func=lambda x: f"{x} - {archived[x]['full_name']}"
    )
    
    if selected_id:
        customer = archived[selected_id]
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Customer Details")
            st.info(f"Archive Date: {customer['archive_date']}")
            st.info(f"Archive Reason: {customer['archive_reason']}")
            
        with col2:
            st.markdown("#### Status at Archive")
            data = customer['customer_data']
            st.info(f"Verification Status: {data['verification_status']}")
            st.info(f"Risk Category: {data['risk_category']}")
        
        # Show full archived data
        with st.expander("View Complete Customer Record"):
            st.json(customer['customer_data'])

# Helper functions for validation and data handling
def _validate_customer_data(data):
    """Validate customer data input"""
    if not data["full_name"] or not data["nik"] or not data["address"]:
        st.error("Please fill in all required fields")
        return False
    elif not validate_nik(data["nik"]):
        st.error("Invalid NIK format. NIK should be a 16-digit number.")
        return False
    return True

def _save_new_customer(data):
    """Save new customer to database"""
    new_id = f"CUS{len(st.session_state.customers) + 1:03d}"
    
    customer_data = {
        "id": new_id,
        **data,
        "registration_date": datetime.now().strftime("%Y-%m-%d"),
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "verification_status": "Under Review"
    }
    
    # Calculate risk score
    customer_data["risk_score"] = calculate_risk_score(customer_data)
    customer_data["risk_category"] = get_risk_category(customer_data["risk_score"])
    
    if add_customer(customer_data):
        # Update session state
        st.session_state.customers = get_all_customers()
        add_audit_log("Add Customer", f"Added new customer {new_id} - {data['full_name']}")
        st.success(f"Customer {data['full_name']} registered successfully with ID: {new_id}")
        st.balloons()
    else:
        st.error("Failed to add customer. NIK might already exist.")

@login_required(Resource.CUSTOMER, Permission.WRITE)
def _update_customer(customer_id, data):
    """Update customer in database"""
    try:
        # Ensure required fields
        data.update({
            "id": customer_id,
            "last_updated": datetime.now().strftime("%Y-%m-%d")
        })
        
        # Recalculate risk score
        data["risk_score"] = calculate_risk_score(data)
        data["risk_category"] = get_risk_category(data["risk_score"])
        
        # Update database
        if update_customer(customer_id, data):
            # Update session state only after successful database update
            st.session_state.customers[customer_id].update(data)
            add_audit_log("Edit Customer", f"Updated customer {customer_id} - {data['full_name']}")
            st.success(f"Customer {data['full_name']} updated successfully")
            st.rerun()
        else:
            st.error("Failed to update customer in database. Check logs for details.")
            
    except Exception as e:
        st.error(f"Error updating customer: {str(e)}")
        print(f"Update error details: {str(e)}")  # For debugging

def _handle_customer_deletion(customer_id):
    """Handle customer deletion process"""
    customer = st.session_state.customers[customer_id]
    
    has_relations = not _can_delete_customer(customer_id)
    
    if has_relations:
        st.warning("⚠️ This customer has related alerts or transactions")
        st.info("Instead of deletion, you can archive this customer")
        
        reason = st.text_area(
            "Archive Reason (required)", 
            placeholder="Explain why this customer is being archived...",
            key=f"archive_reason_{customer_id}"  # Add unique key
        )
        
        if st.button("Archive Customer", key=f"archive_btn_{customer_id}") and reason:
            if archive_customer(customer_id, reason):
                st.session_state.customers.pop(customer_id)
                add_audit_log(
                    "Archive Customer",
                    f"Archived customer {customer_id} - {customer['full_name']} - Reason: {reason}"
                )
                st.success(f"Customer {customer['full_name']} archived successfully")
                st.rerun()
            
    else:
        st.info("This action cannot be undone. All customer information will be permanently removed.")
        confirmation = st.text_input(
            "Type the customer ID to confirm deletion:", 
            key=f"delete_confirm_{customer_id}"  # Add unique key
        )
        
        if st.button("Delete Customer", key=f"delete_btn_{customer_id}") and confirmation == customer_id:
            if delete_customer(customer_id):
                st.session_state.customers.pop(customer_id)
                add_audit_log("Delete Customer", f"Deleted customer {customer_id}")
                st.success(f"Customer {customer['full_name']} deleted successfully")
                st.rerun()

def _can_delete_customer(customer_id):
    """Check if customer can be deleted"""
    customer_alerts = [a for a in st.session_state.alerts if a['customer_id'] == customer_id]
    customer_transactions = [t for t in st.session_state.transaction_logs if t['customer_id'] == customer_id]
    return not (customer_alerts or customer_transactions)

def _customer_form(existing_data=None):
    """Handle customer form fields"""
    # Personal information
    col1, col2 = st.columns(2)
    with col1:
        full_name = st.text_input("Nama", value=existing_data["full_name"] if existing_data else "")
        nik = st.text_input("NIK (16 digits)", value=existing_data["nik"] if existing_data else "")
        
        # Fix date handling
        default_date = (
            datetime.strptime(existing_data["dob"], "%Y-%m-%d").date() 
            if existing_data and existing_data.get("dob") 
            else datetime.today().date()
        )
        dob = st.date_input(
            "Date of Birth",
            value=default_date,
            min_value=datetime(1940, 1, 1).date(),
            max_value=datetime.today().date()
        )
    
    with col2:
        occupation = st.selectbox(
            "Occupation", 
            [
                "Business Owner", "Government Employee", "Private Sector Employee", 
                "Real Estate Developer", "Politician", "Doctor", "Lawyer", "Student", 
                "Retired", "Military/Police", "Teacher", "Other"
            ],
            index=[
                "Business Owner", "Government Employee", "Private Sector Employee", 
                "Real Estate Developer", "Politician", "Doctor", "Lawyer", "Student", 
                "Retired", "Military/Police", "Teacher", "Other"
            ].index(existing_data["occupation"]) if existing_data else 0
        )
        income_level = st.selectbox(
            "Income Level", 
            ["Low", "Medium", "High"],
            index=["Low", "Medium", "High"].index(existing_data["income_level"]) if existing_data else 0
        )
        pep_status = st.checkbox("Politically Exposed Person (PEP)", value=existing_data["pep_status"] if existing_data else False)
    
    address = st.text_area("Address", value=existing_data["address"] if existing_data else "")
    
    # Document information
    st.subheader("Documents")
    documents = existing_data["documents"] if existing_data else []
    doc_id_card = st.checkbox("ID Card", value="ID Card" in documents)
    doc_address = st.checkbox("Proof of Address", value="Proof of Address" in documents)
    doc_tax = st.checkbox("Tax ID", value="Tax ID" in documents)
    doc_business = st.checkbox("Business License", value="Business License" in documents)
    doc_other = st.text_input(
        "Other Documents",
        value=", ".join([d for d in documents if d not in ["ID Card", "Proof of Address", "Tax ID", "Business License"]]) if documents else ""
    )
    
    # Additional information
    transaction_profile = st.text_area(
        "Expected Transaction Profile",
        value=existing_data["transaction_profile"] if existing_data else "",
        placeholder="E.g., Monthly transfers between Rp 10-20 million"
    )
    notes = st.text_area(
        "Additional Notes",
        value=existing_data["notes"] if existing_data else ""
    )
    suspicious = st.checkbox(
        "Flag as Suspicious",
        value=existing_data["suspicious_activity"] if existing_data else False
    )

    # Compile documents list
    final_documents = []
    if doc_id_card:
        final_documents.append("ID Card")
    if doc_address:
        final_documents.append("Proof of Address")
    if doc_tax:
        final_documents.append("Tax ID")
    if doc_business:
        final_documents.append("Business License")
    if doc_other:
        final_documents.extend([d.strip() for d in doc_other.split(",")])

    return {
        "full_name": full_name,
        "nik": nik,
        "dob": dob.strftime("%Y-%m-%d") if dob else datetime.today().strftime("%Y-%m-%d"),
        "address": address,
        "occupation": occupation,
        "income_level": income_level,
        "documents": final_documents,
        "suspicious_activity": suspicious,
        "notes": notes,
        "transaction_profile": transaction_profile,
        "pep_status": pep_status
    }

def _evaluate_verification_results(results, customer):
    """Evaluate verification results and determine status"""
    try:
        # 1. Check match percentages
        match_score = sum(results['matches'].values()) / len(results['matches'])
        
        # 2. Calculate verification score
        verification_score = {
            "data_match": match_score,
            "authenticity": results['authenticity_score'],
            "field_completeness": len(results['extracted_info']) / 4  # 4 required fields
        }
        
        # 3. Define verification thresholds
        thresholds = {
            "Verified": {
                "data_match": 0.8,  # 80% data must match
                "authenticity": 0.7,  # 70% authenticity score
                "field_completeness": 0.75  # 75% fields must be present
            },
            "Manual Review": {
                "data_match": 0.6,
                "authenticity": 0.5,
                "field_completeness": 0.5
            }
        }
        
        # 4. Make verification decision
        if (verification_score["data_match"] >= thresholds["Verified"]["data_match"] and
            verification_score["authenticity"] >= thresholds["Verified"]["authenticity"] and
            verification_score["field_completeness"] >= thresholds["Verified"]["field_completeness"]):
            return "Verified", verification_score
            
        elif (verification_score["data_match"] >= thresholds["Manual Review"]["data_match"] and
              verification_score["authenticity"] >= thresholds["Manual Review"]["authenticity"] and
              verification_score["field_completeness"] >= thresholds["Manual Review"]["field_completeness"]):
            return "Manual Review", verification_score
            
        else:
            return "Failed", verification_score
            
    except Exception as e:
        st.error(f"Error evaluating verification: {str(e)}")
        return "Failed", {}

def verify_customer_documents(customer_id, customer):
    """Enhanced document verification using Gemini Flash"""
    st.subheader("🔍 Document Verification")
    
    # Display current documents
    st.write("📄 Current Documents:")
    for doc in customer["documents"]:
        st.info(f"✓ {doc}")
    
    # Document upload and verification
    doc_type = st.selectbox("Select Document Type", [
        "ID Card (KTP)",
        "Passport",
        "Proof of Address",
        "Tax ID (NPWP)",
        "Business License"
    ])
    
    uploaded_file = st.file_uploader("Upload Document", type=["jpg", "jpeg", "png"])
    
    if uploaded_file:
        try:
            image = Image.open(uploaded_file)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            st.image(image, caption=f"{doc_type} Preview", width=400)
            
            if st.button("Verify Document"):
                with st.spinner("Analyzing document..."):
                    results = analyze_document(image, doc_type, customer)
                    
                    if results:
                        display_verification_results(results, customer_id, customer, doc_type)
                    else:
                        st.error("Failed to analyze document")
                        
        except Exception as e:
            st.error(f"Verification Error: {str(e)}")

def analyze_document(image, doc_type, customer):
    """Analyze document using Gemini"""
    try:
        # Convert image for Gemini
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()
        
        prompt = f"""Analyze this {doc_type} and verify if it matches the following customer information:
Name: {customer['full_name']}
NIK: {customer['nik']}
DOB: {customer['dob']}
Address: {customer['address']}

Provide a response in the following exact JSON format:
{{
    "extracted_info": {{
        "name": "extracted name",
        "nik": "extracted nik",
        "dob": "extracted date of birth",
        "address": "extracted address"
    }},
    "matches": {{
        "name": true/false,
        "nik": true/false,
        "dob": true/false,
        "address": true/false
    }},
    "authenticity_score": 0.95,
    "verification_status": "Verified/Manual Review/Failed"
}}"""

        # Create content for Gemini
        content = {
            "parts": [
                {"text": prompt},
                {"inline_data": {
                    "mime_type": "image/jpeg",
                    "data": base64.b64encode(img_byte_arr).decode('utf-8')
                }}
            ]
        }
        
        # Generate Gemini response
        api_key = os.getenv("GEMINI_API_KEY") or st.secrets["GEMINI_API_KEY"]
        if not api_key:
            st.error("Gemini API key not found")
            return None
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        response = model.generate_content(content)
        response_text = response.text.strip()
        
        # Parse JSON response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            results = json.loads(response_text[json_start:json_end])
            return results
        else:
            raise ValueError("No valid JSON found in response")
            
    except Exception as e:
        st.error(f"Analysis error: {str(e)}")
        return None

def display_verification_results(results, customer_id, customer, doc_type):
    """Display verification results and update records"""
    try:
        # Display results
        st.success("✅ Document Analysis Complete")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Authenticity Score", f"{results['authenticity_score']:.0%}")
        with col2:
            match_score = len([v for v in results['matches'].values() if v])/len(results['matches'])
            st.metric("Data Match", f"{match_score:.0%}")
        
        # Show extracted information
        st.subheader("📋 Extracted Information")
        for field, value in results["extracted_info"].items():
            st.write(f"**{field.title()}:** {value}")
        
        # Comparison table
        st.subheader("Data Comparison")
        comparison_df = pd.DataFrame({
            'Field': results['matches'].keys(),
            'Extracted': [results['extracted_info'][k] for k in results['matches'].keys()],
            'Original': [customer.get(k, 'N/A') for k in results['matches'].keys()],
            'Match': ['✅' if v else '❌' for v in results['matches'].values()]
        })
        st.dataframe(comparison_df)
        
        # Update customer if verified
        if results["verification_status"] == "Verified":
            _update_customer_verification(customer_id, customer, results, doc_type)
        else:
            st.warning(f"⚠️ Document Status: {results['verification_status']}")
            
    except Exception as e:
        st.error(f"Error displaying results: {str(e)}")

def _update_customer_verification(customer_id, customer, results, doc_type):  # Add doc_type parameter
    """Update customer record after successful verification"""
    try:
        # Update customer data with verification results
        customer_data = st.session_state.customers[customer_id].copy()
        
        # Add new document without duplicates
        current_documents = set(customer_data.get("documents", []))
        current_documents.add(doc_type)
        
        customer_data.update({
            "verification_status": "Verified",
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "notes": f"{customer_data.get('notes', '')}\n[{datetime.now().strftime('%Y-%m-%d')}] {doc_type} verification completed successfully",
            "documents": list(current_documents)
        })
        
        # Update database first
        if update_customer(customer_id, customer_data):
            # Only update session state after successful database update
            st.session_state.customers[customer_id] = customer_data
            
            # Add audit log
            add_audit_log(
                "Document Verification",
                f"Successfully verified {doc_type} for customer {customer_id}"
            )
            
            st.success(f"✅ Customer record updated successfully with {doc_type}")
            st.rerun()  # Changed from experimental_rerun() to rerun()
        else:
            st.error("Database update failed. Please try again or contact support.")
            
    except Exception as e:
        st.error(f"Error updating customer verification: {str(e)}")

def _create_review_alert(customer_id, results):
    """Create alert for manual review"""
    alert_id = f"ALT{len(st.session_state.alerts) + 1:03d}"
    new_alert = {
        "id": alert_id,
        "customer_id": customer_id,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "type": "Document Review Required",
        "description": "Document verification requires manual review",
        "status": "Open",
        "severity": "Medium",
        "assigned_to": "KYC Team",
        "verification_data": results
    }
    st.session_state.alerts.append(new_alert)

def _create_verification_alert(customer_id, results):
    """Create alert for failed verification"""
    alert_id = f"ALT{len(st.session_state.alerts) + 1:03d}"
    new_alert = {
        "id": alert_id,
        "customer_id": customer_id,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "type": "Verification Failed",
        "description": "Document verification failed - possible fraud",
        "status": "Open",
        "severity": "High",
        "assigned_to": "Risk Team",
        "verification_data": results
    }
    st.session_state.alerts.append(new_alert)