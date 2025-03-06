from dataclasses import dataclass
from datetime import datetime
import sqlite3
from pathlib import Path
import bcrypt
from .roles import ROLES

@dataclass
class User:
    """User data structure"""
    id: str
    username: str
    full_name: str
    email: str
    role: str
    is_active: bool
    last_login: str
    created_at: str

def init_user_db():
    """Initialize user database"""
    db_path = Path(__file__).parent.parent.parent / "data" / "kyc.db"
    
    # Create data directory if it doesn't exist
    db_path.parent.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    try:
        # Create users table
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                role TEXT NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                last_login DATE,
                created_at DATE NOT NULL
            )
        ''')
        
        # Check if admin user exists
        c.execute('SELECT id FROM users WHERE username = ?', ('admin',))
        if not c.fetchone():
            # Create default admin user
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw('admin123'.encode('utf-8'), salt)
            
            c.execute('''
                INSERT INTO users (id, username, password, full_name, email, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                'USR001',
                'admin',
                hashed.decode('utf-8'),
                'System Administrator',
                'admin@kyc-system.com',
                'admin',
                datetime.now().strftime('%Y-%m-%d')
            ))
        
        conn.commit()
        
    except Exception as e:
        print(f"Database initialization error: {str(e)}")
        if conn:
            conn.rollback()
        raise e
        
    finally:
        if conn:
            conn.close()

def authenticate_user(username: str, password: str) -> User:
    """Authenticate user credentials"""
    db_path = Path(__file__).parent.parent.parent / "data" / "kyc.db"
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    try:
        c.execute('SELECT * FROM users WHERE username = ? AND is_active = 1', (username,))
        user = c.fetchone()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
            # Update last login
            c.execute('UPDATE users SET last_login = ? WHERE id = ?', 
                     (datetime.now().strftime('%Y-%m-%d'), user[0]))
            conn.commit()
            
            return User(
                id=user[0],
                username=user[1],
                full_name=user[3],
                email=user[4],
                role=user[5],
                is_active=user[6],
                last_login=user[7] or datetime.now().strftime('%Y-%m-%d'),
                created_at=user[8]
            )
    finally:
        conn.close()
    
    return None
