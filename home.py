import streamlit as st
from modules.auth.session import init_auth, display_login, logout
from modules.auth.roles import Resource, Permission, check_access
from modules.auth.users import init_user_db  # Add this import

# Must be first Streamlit command
st.set_page_config(
    page_title="Banking KYC Analysis System",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Rest of imports
from datetime import datetime
from config.config import initialize_session_state
from modules.dashboard import display_dashboard
from modules.customer import customer_management
from modules.risk import risk_assessment
from modules.alert import alert_management
from modules.transaction import transaction_monitoring
from modules.audit import audit_logs
from modules.user_management import user_management  # Add this import

def side_bar():
    """Render the sidebar navigation"""
    st.sidebar.image("assets/logo.png", use_container_width=True)
    
    # Show menu only if logged in
    if st.session_state.user:
        menu_options = []
        user_role = st.session_state.user.role
        
        # Add menu items based on permissions
        if check_access(user_role, Resource.CUSTOMER, Permission.READ):
            menu_options.append("Dashboard")
            menu_options.append("Customer Management")
            
        if check_access(user_role, Resource.RISK, Permission.READ):
            menu_options.append("Risk Assessment")
            
        if check_access(user_role, Resource.ALERT, Permission.READ):
            menu_options.append("Alert Management")
            
        if check_access(user_role, Resource.TRANSACTION, Permission.READ):
            menu_options.append("Transaction Monitoring")
            
        if check_access(user_role, Resource.AUDIT, Permission.READ):
            menu_options.append("Audit Logs")

        # Add User Management for admin users
        if check_access(user_role, Resource.SYSTEM, Permission.ADMIN):
            menu_options.append("User Management")
        
        # Add About option at the end of menu_options
        menu_options.append("About")
        
        selection = st.sidebar.radio("Navigate", menu_options)
        
        # User info section
        st.sidebar.divider()
        st.sidebar.caption("Logged in as:")
        st.sidebar.text(f"{st.session_state.user.full_name}")
        st.sidebar.text(f"Role: {st.session_state.user.role}")
        
        if st.sidebar.button("Logout"):
            logout()
        
        return selection
    return None

def display_about():
    """Display About section content"""
    st.markdown('<div class="about-container">', unsafe_allow_html=True)
    st.title("About KYCPy, Banking KYC Analysis System")
    st.markdown("---")
    st.markdown("""
    ## Overview
    The KYCPy platform represents a comprehensive solution for Know Your Customer (KYC) processes in banking institutions. By integrating advanced security protocols with intuitive document management, our system streamlines the complex workflows associated with customer verification and compliance. Our platform combines robust security measures with user-friendly interfaces to deliver a seamless experience for banking professionals.

    ## Core System Components

    ### Document Verification System
    Our AI-powered document verification system leverages Google's Gemini AI technology to provide advanced document processing capabilities. The system performs real-time authenticity verification while simultaneously extracting and validating information from submitted documents. Through multi-language OCR integration, we ensure accurate processing of documents regardless of their origin or language.

    The document processing workflow begins with our intelligent preprocessing engine, which optimizes uploaded images for maximum accuracy. Our system then employs advanced algorithms to extract relevant information, automatically populating required fields while maintaining data integrity through robust validation mechanisms.

    We support a comprehensive range of document types, including official government identification cards (KTP, passports, driver's licenses), proof of address documentation, bank statements, and utility bills. The system accepts multiple file formats including JPEG, JPG, and PNG, ensuring flexibility in document submission while maintaining security standards.

    ### Role-Based Access Management
    Our sophisticated role-based access control system ensures precise management of system capabilities across different user roles. The platform supports multiple specialized roles including Administrators, Risk Officers, Customer Service Representatives, Compliance Officers, and Transaction Analysts. Each role is carefully designed with specific permission sets that align with job responsibilities while maintaining security protocols.

    The authentication system implements advanced session management and monitors login attempts to prevent unauthorized access. This granular approach to access control ensures that users can only access information and perform actions appropriate to their role, maintaining data security and operational integrity.

    ### Customer Information Management
    The customer management module serves as a centralized hub for all customer-related activities. It provides comprehensive tools for creating and maintaining detailed customer profiles, with seamless integration of document management capabilities. The system features advanced search and filtering mechanisms, allowing staff to quickly locate and access customer information while maintaining a complete history of all profile changes and document submissions.

    ### Risk Assessment Framework
    Our risk assessment module implements a systematic approach to evaluating customer risk profiles. The system provides tools for detailed risk scoring and categorization, maintaining a comprehensive history of all assessments. Users can track changes in risk status over time and document their findings through an intuitive commenting system. This structured approach ensures consistent risk evaluation across the organization while maintaining detailed records for compliance purposes.

    ### Alert Management System
    The alert management system provides a sophisticated framework for handling time-sensitive notifications and issues. It implements a priority-based routing system that ensures critical alerts receive immediate attention. The system tracks alert assignments and resolution progress, maintaining detailed documentation of all actions taken. This comprehensive approach ensures that no critical notifications are missed and all issues are properly addressed and documented.

    ### Transaction Monitoring Capabilities
    Our transaction monitoring module provides powerful tools for overseeing financial activities. The system offers detailed transaction viewing capabilities with advanced filtering options for efficient analysis. Users can track transaction histories, monitor status changes, and generate comprehensive reports. The export functionality ensures that transaction data can be analyzed in external systems while maintaining data integrity and security.

    ### Comprehensive Audit System
    The audit system maintains detailed records of all system activities, creating a comprehensive audit trail for compliance and security purposes. Every user action, login attempt, and document access is logged with precise timestamps and user information. The system provides tools for analyzing activity patterns and generating detailed reports, ensuring complete transparency and accountability in all operations.

    ### User Administration
    The user management system provides administrators with powerful tools for managing system access and security. It includes comprehensive features for account creation, role assignment, and access control management. The system maintains detailed records of all user activities and account status changes, ensuring accountability and security in system access management.

    ## Security Infrastructure
    Our security framework implements multiple layers of protection, including robust password management, sophisticated session control, and comprehensive access logging. The system enforces strict security policies while maintaining user-friendly interfaces. Regular security audits and monitoring ensure the ongoing protection of sensitive information.

    ## Current System Scope
    While our system provides comprehensive KYC management capabilities, we maintain transparency about current limitations in automation and OCR functionality. Our development roadmap includes plans for enhanced automation features and advanced reporting capabilities, ensuring that the system continues to evolve with industry needs.
    """)
    
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    """Main application entry point"""
    # Initialize database and create tables first
    init_user_db()  # Add this line before init_auth()
    
    # Initialize authentication
    init_auth()
    
    # Check authentication
    if not st.session_state.user:
        display_login()
        return
        
    # Initialize session state for data persistence
    initialize_session_state()

    # Render sidebar and get selection
    selection = side_bar()

    # Route to appropriate module based on selection
    if selection:
        try:
            if selection == "Dashboard":
                display_dashboard()
            elif selection == "Customer Management":
                customer_management()
            elif selection == "Risk Assessment":
                risk_assessment()
            elif selection == "Alert Management":
                alert_management()
            elif selection == "Transaction Monitoring":
                transaction_monitoring()
            elif selection == "Audit Logs":
                audit_logs()
            elif selection == "User Management":  # Add this condition
                user_management()
            elif selection == "About":
                display_about()
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.error("Please try refreshing the page or contact support if the issue persists.")
# Footer
    st.markdown("---")
    st.markdown("Powered by KYCPy, Adnuri Mohamidi", help="cyberariani@gmail.com")
if __name__ == "__main__":
    main()
