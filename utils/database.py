import sqlite3
import json
import streamlit as st  # Add this import
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "kyc.db"

def init_db():
    """Initialize database and create tables"""
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create customers table
    c.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            nik TEXT UNIQUE NOT NULL,
            dob DATE NOT NULL,
            address TEXT NOT NULL,
            occupation TEXT NOT NULL,
            income_level TEXT NOT NULL,
            risk_score REAL NOT NULL,
            risk_category TEXT NOT NULL,
            registration_date DATE NOT NULL,
            last_updated DATE NOT NULL,
            verification_status TEXT NOT NULL,
            documents TEXT NOT NULL,
            suspicious_activity BOOLEAN NOT NULL,
            notes TEXT,
            transaction_profile TEXT,
            pep_status BOOLEAN NOT NULL
        )
    ''')
    
    # Add archived_customers table
    c.execute('''
        CREATE TABLE IF NOT EXISTS archived_customers (
            id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            nik TEXT UNIQUE NOT NULL,
            archive_date DATE NOT NULL,
            archive_reason TEXT NOT NULL,
            customer_data TEXT NOT NULL  -- JSON of all customer data
        )
    ''')
    
    # Add alerts table
    c.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            date DATE NOT NULL,
            type TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL,
            severity TEXT NOT NULL,
            assigned_to TEXT NOT NULL,
            last_updated DATE NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db():
    """Get database connection"""
    return sqlite3.connect(DB_PATH)

def dict_to_db(d):
    """Convert dictionary to database format"""
    d = d.copy()  # Make a copy to avoid modifying the original
    if 'documents' in d:
        # Ensure documents is a list before converting to JSON
        if isinstance(d['documents'], str):
            # If it's a comma-separated string, convert to list
            d['documents'] = [doc.strip() for doc in d['documents'].split(',') if doc.strip()]
        # Convert list to JSON string
        d['documents'] = json.dumps(d['documents'])
    return d

def db_to_dict(row, cursor):
    """Convert database row to dictionary"""
    columns = [desc[0] for desc in cursor.description]
    result = dict(zip(columns, row))
    
    # Handle documents field
    if 'documents' in result:
        try:
            if result['documents']:
                # Try to parse as JSON
                result['documents'] = json.loads(result['documents'])
            else:
                # If empty, initialize as empty list
                result['documents'] = []
        except json.JSONDecodeError:
            # If JSON parsing fails, treat as comma-separated string
            result['documents'] = [doc.strip() for doc in result['documents'].split(',') if doc.strip()]
    return result

# Database operations
def get_all_customers():
    """Get all customers from database"""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM customers')
    customers = {row[0]: db_to_dict(row, c) for row in c.fetchall()}
    conn.close()
    return customers

def refresh_customer_state():
    """Refresh customer state after database operations"""
    st.session_state.customers = get_all_customers()

def add_customer(customer_data):
    """Add new customer to database"""
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Convert data to database format
        customer_data = dict_to_db(customer_data.copy())
        
        columns = ', '.join(customer_data.keys())
        placeholders = ', '.join('?' * len(customer_data))
        sql = f'INSERT INTO customers ({columns}) VALUES ({placeholders})'
        
        c.execute(sql, list(customer_data.values()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def update_customer(customer_id, data):
    """Update customer in database with proper error handling"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Clean and prepare data
        clean_data = dict_to_db(data.copy())  # Make a copy to avoid modifying original
        
        # Log the update attempt for debugging
        print(f"Updating customer {customer_id} with data:", clean_data)
        
        # Build the SQL query dynamically based on available fields
        update_fields = []
        values = []
        for key in [
            "full_name", "nik", "dob", "address", "occupation", 
            "income_level", "risk_score", "risk_category",
            "verification_status", "documents", "suspicious_activity",
            "notes", "transaction_profile", "pep_status", "last_updated"
        ]:
            if key in clean_data:
                update_fields.append(f"{key} = ?")
                values.append(clean_data[key])
        
        # Add customer_id as last value
        values.append(customer_id)
        
        # Construct and execute SQL
        sql = f"UPDATE customers SET {', '.join(update_fields)} WHERE id = ?"
        print("SQL Query:", sql)  # For debugging
        
        cursor.execute(sql, values)
        db.commit()
        
        # Verify the update
        if cursor.rowcount > 0:
            return True
        else:
            print(f"No rows updated for customer {customer_id}")
            return False
            
    except Exception as e:
        print(f"Database update error: {str(e)}")
        if db:
            db.rollback()
        return False
        
    finally:
        if db:
            db.close()

def delete_customer(customer_id):
    """Delete customer from database"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Delete customer record
        cursor.execute('DELETE FROM customers WHERE id = ?', (customer_id,))
        
        # Commit changes
        conn.commit()
        
        # Check if deletion was successful
        if cursor.rowcount > 0:
            return True
        return False
        
    except Exception as e:
        print(f"Database deletion error: {str(e)}")
        return False
        
    finally:
        if conn:
            conn.close()

def archive_customer(customer_id, reason):
    """Archive customer instead of deletion"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get customer data before deletion
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        customer = cursor.fetchone()
        
        if customer:
            # Store in archived_customers
            customer_data = db_to_dict(customer, cursor)
            archive_date = datetime.now().strftime("%Y-%m-%d")
            customer_data['archive_date'] = archive_date
            customer_data['archive_reason'] = reason
            
            # Modify NIK for archive by adding timestamp
            original_nik = customer_data['nik']
            archived_nik = f"{original_nik}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            try:
                # Insert into archived_customers with modified NIK
                cursor.execute('''
                    INSERT INTO archived_customers 
                    (id, full_name, nik, archive_date, archive_reason, customer_data)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    customer_id,
                    customer_data['full_name'],
                    archived_nik,  # Use modified NIK
                    archive_date,
                    reason,
                    json.dumps(customer_data)  # Original data with original NIK
                ))
                
                # Delete from active customers
                cursor.execute('DELETE FROM customers WHERE id = ?', (customer_id,))
                conn.commit()
                return True
                
            except sqlite3.IntegrityError as e:
                print(f"Archive error (handled): {str(e)}")
                conn.rollback()
                # If still fails, try with more unique identifier
                final_nik = f"{archived_nik}_{str(hash(datetime.now().isoformat()))[-8:]}"
                cursor.execute('''
                    INSERT INTO archived_customers 
                    (id, full_name, nik, archive_date, archive_reason, customer_data)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    customer_id,
                    customer_data['full_name'],
                    final_nik,
                    archive_date,
                    reason,
                    json.dumps(customer_data)
                ))
                
                cursor.execute('DELETE FROM customers WHERE id = ?', (customer_id,))
                conn.commit()
                return True
        
        return False
        
    except Exception as e:
        print(f"Archive error: {str(e)}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()

def get_archived_customers():
    """Get all archived customers from database"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM archived_customers')
        archived = {}
        
        for row in cursor.fetchall():
            archived[row[0]] = {
                "id": row[0],
                "full_name": row[1],
                "nik": row[2],
                "archive_date": row[3],
                "archive_reason": row[4],
                "customer_data": json.loads(row[5])
            }
        return archived
    finally:
        if conn:
            conn.close()

def save_alert(alert_data):
    """Save or update alert in database"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Clean data
        alert = alert_data.copy()
        alert['last_updated'] = datetime.now().strftime("%Y-%m-%d")
        
        # Check if alert exists
        cursor.execute('SELECT id FROM alerts WHERE id = ?', (alert['id'],))
        exists = cursor.fetchone()
        
        if exists:
            # Update existing alert
            update_fields = []
            values = []
            for key in ["status", "description", "severity", "assigned_to", "last_updated"]:
                if key in alert:
                    update_fields.append(f"{key} = ?")
                    values.append(alert[key])
            
            values.append(alert['id'])
            sql = f"UPDATE alerts SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(sql, values)
        else:
            # Insert new alert
            columns = ', '.join(alert.keys())
            placeholders = ', '.join('?' * len(alert))
            sql = f'INSERT INTO alerts ({columns}) VALUES ({placeholders})'
            cursor.execute(sql, list(alert.values()))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Error saving alert: {str(e)}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()

def get_customer_alerts(customer_id):
    """Get all alerts for a customer"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Debug print
        print(f"Fetching alerts for customer {customer_id}")
        
        cursor.execute('SELECT * FROM alerts WHERE customer_id = ? ORDER BY date DESC', (customer_id,))
        alerts = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
        
        # Debug print
        print(f"Found {len(alerts)} alerts")
        
        return alerts
    except Exception as e:
        print(f"Error getting alerts: {str(e)}")
        return []
    finally:
        if conn:
            conn.close()

def delete_alert(alert_id):
    """Delete alert from database"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM alerts WHERE id = ?', (alert_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting alert: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()
