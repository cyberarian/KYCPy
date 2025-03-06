import sqlite3
from pathlib import Path

def check_database():
    """Check database tables and content"""
    DB_PATH = Path(__file__).parent.parent / "data" / "kyc.db"
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in database:", tables)
    
    # Check alerts table structure
    cursor.execute("PRAGMA table_info(alerts);")
    alert_columns = cursor.fetchall()
    print("\nAlert table structure:", alert_columns)
    
    # Check alerts content
    cursor.execute("SELECT * FROM alerts;")
    alerts = cursor.fetchall()
    print("\nTotal alerts:", len(alerts))
    
    # Check alerts for CUS007
    cursor.execute("SELECT * FROM alerts WHERE customer_id = 'CUS007';")
    cus007_alerts = cursor.fetchall()
    print("\nCUS007 alerts:", cus007_alerts)
    
    conn.close()

if __name__ == "__main__":
    check_database()
