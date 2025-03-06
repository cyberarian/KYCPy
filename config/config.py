import streamlit as st
from datetime import datetime
import os
from dotenv import load_dotenv
from utils.database import init_db, get_all_customers, add_customer
from utils.helpers import calculate_risk_score, get_risk_category
from modules.auth.users import init_user_db

# Load environment variables
load_dotenv()

def _create_default_customer():
    """Create default customer data"""
    default_customer = {
        "id": "CUS001",
        "full_name": "Bambang Suryanto",
        "nik": "3201012505780001",
        "dob": "1978-05-25",
        "address": "Jl. Sudirman No. 123, Jakarta Pusat",
        "occupation": "Business Owner",
        "income_level": "High",
        "risk_score": 0.35,
        "risk_category": "Medium",
        "registration_date": datetime.now().strftime("%Y-%m-%d"),
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "verification_status": "Verified",
        "documents": ["ID Card", "Proof of Address", "Tax ID"],
        "suspicious_activity": False,
        "notes": "Regular international transfers to Singapore",
        "transaction_profile": "Monthly transfers between Rp 50-100 million",
        "pep_status": False
    }
    
    # Calculate risk score
    default_customer["risk_score"] = calculate_risk_score(default_customer)
    default_customer["risk_category"] = get_risk_category(default_customer["risk_score"])
    
    add_customer(default_customer)
    return default_customer

def _create_synthetic_customers():
    """Create synthetic customer data for MVP"""
    customers = [
        {
            "id": "CUS001",
            # Change first customer's data to avoid duplication
            "full_name": "Budi Santoso",
            "nik": "3201012505780011",  # Changed NIK
            "dob": "1978-05-25",
            "address": "Jl. Sudirman No. 123, Jakarta Pusat",
            "occupation": "Business Owner",
            "income_level": "High",
            "verification_status": "Verified",
            "documents": ["ID Card", "Proof of Address", "Tax ID"],
            "suspicious_activity": False,
            "notes": "Regular international transfers to Singapore",
            "transaction_profile": "Monthly transfers between Rp 50-100 million",
            "pep_status": False
        },
        {
            "id": "CUS002",
            "full_name": "Sarah Wijaya",
            "nik": "3173015708900002",
            "dob": "1990-08-17",
            "address": "Jl. Gatot Subroto No. 45, Jakarta Selatan",
            "occupation": "Government Employee",
            "income_level": "Medium",
            "verification_status": "Verified",
            "documents": ["ID Card", "Proof of Address"],
            "suspicious_activity": False,
            "notes": "Regular salary deposits",
            "transaction_profile": "Monthly transactions under Rp 20 million",
            "pep_status": True
        },
        {
            "id": "CUS003",
            "full_name": "Abdul Rahman",
            "nik": "3275014404850003",
            "dob": "1985-04-04",
            "address": "Jl. Merdeka No. 78, Bandung",
            "occupation": "Doctor",
            "income_level": "High",
            "verification_status": "Under Review",
            "documents": ["ID Card", "Tax ID", "Business License"],
            "suspicious_activity": True,
            "notes": "Multiple large cash deposits",
            "transaction_profile": "Irregular high-value transactions",
            "pep_status": False
        },
        {
            "id": "CUS004",
            "full_name": "Linda Kusuma",
            "nik": "3271046009950004",
            "dob": "1995-09-20",
            "address": "Jl. Asia Afrika No. 88, Bandung",
            "occupation": "Private Sector Employee",
            "income_level": "Medium",
            "verification_status": "Verified",
            "documents": ["ID Card", "Proof of Address"],
            "suspicious_activity": False,
            "notes": "New account holder",
            "transaction_profile": "Regular salary and expenses",
            "pep_status": False
        },
        {
            "id": "CUS005",
            "full_name": "Richard Tanoko",
            "nik": "3578010203870005",
            "dob": "1987-03-02",
            "address": "Jl. Mayjen Sungkono No. 89, Surabaya",
            "occupation": "Real Estate Developer",
            "income_level": "High",
            "verification_status": "Verified",
            "documents": ["ID Card", "Tax ID", "Business License"],
            "suspicious_activity": False,
            "notes": "Property development investments",
            "transaction_profile": "Large business transactions",
            "pep_status": False
        },
        {
            "id": "CUS006",
            "full_name": "Maya Sari",
            "nik": "3171015007920006",
            "dob": "1992-07-10",
            "address": "Jl. Thamrin No. 56, Jakarta Pusat",
            "occupation": "Lawyer",
            "income_level": "High",
            "verification_status": "Manual Review",
            "documents": ["ID Card", "Proof of Address"],
            "suspicious_activity": False,
            "notes": "Legal consulting fees",
            "transaction_profile": "Monthly professional service payments",
            "pep_status": False
        },
        {
            "id": "CUS007",
            "full_name": "Hendra Gunawan",
            "nik": "3276011002830007",
            "dob": "1983-02-10",
            "address": "Jl. Gajah Mada No. 190, Jakarta Barat",
            "occupation": "Politician",
            "income_level": "High",
            "verification_status": "Verified",
            "documents": ["ID Card", "Tax ID"],
            "suspicious_activity": True,
            "notes": "Political campaign funding",
            "transaction_profile": "Large irregular deposits",
            "pep_status": True
        },
        {
            "id": "CUS008",
            "full_name": "Diana Chen",
            "nik": "3174016504960008",
            "dob": "1996-04-25",
            "address": "Jl. Pluit Raya No. 32, Jakarta Utara",
            "occupation": "Business Owner",
            "income_level": "High",
            "verification_status": "Verified",
            "documents": ["ID Card", "Business License", "Tax ID"],
            "suspicious_activity": False,
            "notes": "Import-export business",
            "transaction_profile": "Regular international trades",
            "pep_status": False
        },
        {
            "id": "CUS009",
            "full_name": "Agus Santoso",
            "nik": "3271010808890009",
            "dob": "1989-08-08",
            "address": "Jl. Pasteur No. 11, Bandung",
            "occupation": "Teacher",
            "income_level": "Low",
            "verification_status": "Under Review",
            "documents": ["ID Card"],
            "suspicious_activity": False,
            "notes": "Part-time online business",
            "transaction_profile": "Small regular transactions",
            "pep_status": False
        },
        {
            "id": "CUS010",
            "full_name": "Kartika Dewi",
            "nik": "3171014509910010",
            "dob": "1991-09-05",
            "address": "Jl. Veteran No. 75, Jakarta Pusat",
            "occupation": "Military/Police",
            "income_level": "Medium",
            "verification_status": "Verified",
            "documents": ["ID Card", "Proof of Address"],
            "suspicious_activity": False,
            "notes": "Service member benefits",
            "transaction_profile": "Regular salary deposits",
            "pep_status": True
        }
    ]
    
    for customer in customers:
        # Calculate risk score and category
        customer["risk_score"] = calculate_risk_score(customer)
        customer["risk_category"] = get_risk_category(customer["risk_score"])
        customer["registration_date"] = datetime.now().strftime("%Y-%m-%d")
        customer["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        
        # Add to database
        add_customer(customer)
    
    return {c["id"]: c for c in customers}

def initialize_session_state():
    """Initialize all session state variables"""
    # Initialize user database
    init_user_db()
    
    # Initialize database
    init_db()
    
    # Get customers from database
    customers = get_all_customers()
    
    # Check if we only have default/test customers (less than 3)
    if len(customers) < 3:
        # Clear existing customers
        from utils.database import get_db
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM customers')
        conn.commit()
        conn.close()
        
        # Create synthetic customers
        customers = _create_synthetic_customers()
        
        # Add some initial alerts and transactions for demo
        _create_demo_alerts(customers)
        _create_demo_transactions(customers)
    
    st.session_state.customers = customers
    
    # Initialize alerts if not exist, but check for valid customer references
    if 'alerts' not in st.session_state:
        st.session_state.alerts = []
    else:
        # Clean up alerts for deleted customers
        st.session_state.alerts = [
            alert for alert in st.session_state.alerts 
            if alert["customer_id"] in st.session_state.customers
        ]
    
    # Initialize transaction logs if not exist, but check for valid customer references
    if 'transaction_logs' not in st.session_state:
        st.session_state.transaction_logs = []
    else:
        # Clean up transactions for deleted customers
        st.session_state.transaction_logs = [
            tx for tx in st.session_state.transaction_logs 
            if tx["customer_id"] in st.session_state.customers
        ]
    
    # Initialize audit logs if not exist
    if 'audit_logs' not in st.session_state:
        st.session_state.audit_logs = []

    # Clear and recreate alerts
    if True:  # Always recreate alerts for testing
        from utils.database import get_db
        conn = get_db()
        cursor = conn.cursor()
        
        # Clear existing alerts
        cursor.execute('DELETE FROM alerts')
        conn.commit()
        
        # Reset session alerts
        st.session_state.alerts = []
        
        # Create new alerts
        _create_demo_alerts(st.session_state.customers)
        
        conn.close()

def _create_demo_alerts(customers):
    """Create some demo alerts"""
    from utils.database import save_alert
    
    high_risk_customers = {
        k: v for k, v in customers.items() 
        if v['suspicious_activity'] or v['pep_status'] or v['risk_category'] == 'High'
    }
    
    for cust_id, customer in high_risk_customers.items():
        alerts_to_create = []
        
        # Create PEP alert
        if customer['pep_status']:
            alerts_to_create.append({
                "type": "Risk Escalation",
                "description": "PEP status requires enhanced monitoring",
                "severity": "High",
                "status": "Open"
            })
        
        # Create suspicious activity alert
        if customer['suspicious_activity']:
            alerts_to_create.append({
                "type": "Suspicious Activity",
                "description": "Unusual transaction patterns detected",
                "severity": "Medium",
                "status": "Open"
            })
        
        # Create high risk alert
        if customer['risk_category'] == 'High':
            alerts_to_create.append({
                "type": "Risk Assessment",
                "description": "Customer classified as High Risk",
                "severity": "High",
                "status": "Open"
            })
        
        # Save all alerts for this customer
        for idx, alert_data in enumerate(alerts_to_create):
            alert_id = f"ALT{len(st.session_state.alerts) + idx + 1:03d}"
            alert = {
                "id": alert_id,
                "customer_id": cust_id,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "type": alert_data["type"],
                "description": alert_data["description"],
                "status": alert_data["status"],
                "severity": alert_data["severity"],
                "assigned_to": "Compliance Team",
                "last_updated": datetime.now().strftime("%Y-%m-%d")
            }
            
            # Save to both session state and database
            print(f"Creating alert for {cust_id}: {alert['type']}")  # Debug print
            st.session_state.alerts.append(alert)
            save_result = save_alert(alert)
            print(f"Save result: {save_result}")  # Debug print

def _create_demo_transactions(customers):
    """Create some demo transactions"""
    if 'transaction_logs' not in st.session_state:
        st.session_state.transaction_logs = []
    
    # Add sample transactions for each customer
    for cust_id, customer in customers.items():
        # Add 2-3 transactions per customer
        for i in range(2):
            tx_id = f"TX{len(st.session_state.transaction_logs) + 1:04d}"
            amount = 50_000_000 if customer['income_level'] == "High" else 10_000_000
            
            transaction = {
                "id": tx_id,
                "customer_id": cust_id,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "type": "Transfer",
                "amount": amount,
                "destination": "External Account",
                "notes": f"Monthly {customer['transaction_profile']}",
                "risk_flag": customer['suspicious_activity']
            }
            st.session_state.transaction_logs.append(transaction)

def get_env_variable(key, default=None):
    """Get environment variable with priority order:
    1. Environment variable
    2. Streamlit secrets
    3. Default value
    """
    value = os.getenv(key)
    if not value and hasattr(st, 'secrets'):
        value = st.secrets.get(key)
    return value or default

def get_db_config():
    """Get database configuration from secrets"""
    return st.secrets["database"]

def get_api_keys():
    """Get API keys from secrets"""
    return st.secrets["api_keys"]
