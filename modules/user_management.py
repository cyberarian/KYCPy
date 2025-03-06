import streamlit as st
from datetime import datetime
import bcrypt
from modules.auth.session import login_required
from modules.auth.roles import Resource, Permission, ROLES
from utils.database import get_db

@login_required(Resource.SYSTEM, Permission.ADMIN)
def user_management():
    """User management interface"""
    st.title("👥 User Management")
    
    tab1, tab2, tab3 = st.tabs(["View Users", "Add User", "Role Management"])
    
    with tab1:
        _display_users()
    
    with tab2:
        _add_user()
    
    with tab3:
        _manage_roles()

def _display_users():
    """Display and manage existing users"""
    st.subheader("System Users")
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
        users = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
        
        for user in users:
            with st.expander(f"{user['full_name']} ({user['username']})"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Email:** {user['email']}")
                    st.markdown(f"**Role:** {user['role']}")
                    st.markdown(f"**Last Login:** {user['last_login'] or 'Never'}")
                    st.markdown(f"**Created:** {user['created_at']}")
                
                with col2:
                    active = st.toggle("Active", value=user['is_active'], key=f"active_{user['id']}")
                    if active != user['is_active']:
                        _update_user_status(user['id'], active)
                    
                    role = st.selectbox(
                        "Change Role",
                        list(ROLES.keys()),
                        index=list(ROLES.keys()).index(user['role']),
                        key=f"role_{user['id']}"
                    )
                    if role != user['role']:
                        _update_user_role(user['id'], role)
                    
                    if st.button("Reset Password", key=f"reset_{user['id']}"):
                        _reset_user_password(user['id'])
    
    finally:
        conn.close()

def _add_user():
    """Add new user interface"""
    st.subheader("Add New User")
    
    with st.form("add_user_form"):
        username = st.text_input("Username")
        full_name = st.text_input("Full Name")
        email = st.text_input("Email")
        role = st.selectbox("Role", list(ROLES.keys()))
        password = st.text_input("Initial Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        if st.form_submit_button("Create User"):
            if _validate_new_user(username, email, password, confirm_password):
                if _create_user(username, full_name, email, role, password):
                    st.success("✅ User created successfully")
                    st.rerun()

def _manage_roles():
    """Display role permissions and capabilities"""
    st.subheader("Role Permissions")
    
    for role_id, role in ROLES.items():
        with st.expander(f"{role.name} - {role.description}"):
            for resource, permissions in role.permissions.items():
                st.markdown(f"**{resource.value}**")
                for permission in Permission:
                    st.checkbox(
                        permission.value,
                        value=permission in permissions,
                        disabled=True,
                        key=f"{role_id}_{resource.value}_{permission.value}"
                    )

def _validate_new_user(username, email, password, confirm_password):
    """Validate new user input"""
    if not all([username, email, password, confirm_password]):
        st.error("All fields are required")
        return False
    
    if password != confirm_password:
        st.error("Passwords do not match")
        return False
    
    if len(password) < 8:
        st.error("Password must be at least 8 characters")
        return False
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Check username uniqueness
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            st.error("Username already exists")
            return False
        
        # Check email uniqueness
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            st.error("Email already exists")
            return False
            
        return True
        
    finally:
        conn.close()

def _create_user(username, full_name, email, role, password):
    """Create new user in database"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Hash password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        # Generate user ID
        cursor.execute('SELECT COUNT(*) FROM users')
        count = cursor.fetchone()[0]
        user_id = f"USR{count + 1:03d}"
        
        # Insert new user
        cursor.execute('''
            INSERT INTO users (id, username, password, full_name, email, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            username,
            hashed.decode('utf-8'),
            full_name,
            email,
            role,
            datetime.now().strftime('%Y-%m-%d')
        ))
        
        conn.commit()
        return True
        
    except Exception as e:
        st.error(f"Error creating user: {str(e)}")
        return False
        
    finally:
        conn.close()

def _update_user_status(user_id, is_active):
    """Update user active status"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE users SET is_active = ? WHERE id = ?', (is_active, user_id))
        conn.commit()
        
        st.success("User status updated")
        
    except Exception as e:
        st.error(f"Error updating user status: {str(e)}")
        
    finally:
        conn.close()

def _update_user_role(user_id, new_role):
    """Update user role"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE users SET role = ? WHERE id = ?', (new_role, user_id))
        conn.commit()
        
        st.success("User role updated")
        
    except Exception as e:
        st.error(f"Error updating user role: {str(e)}")
        
    finally:
        conn.close()

def _reset_user_password(user_id):
    """Reset user password to default"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Hash default password
        default_password = "Welcome123!"
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(default_password.encode('utf-8'), salt)
        
        cursor.execute('UPDATE users SET password = ? WHERE id = ?', (hashed.decode('utf-8'), user_id))
        conn.commit()
        
        st.success(f"Password reset to: {default_password}")
        
    except Exception as e:
        st.error(f"Error resetting password: {str(e)}")
        
    finally:
        conn.close()
