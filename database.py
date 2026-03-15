import sqlite3
import hashlib

# Secure password hashing
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# Database Connection
def create_connection():
    # check_same_thread=False is needed for Streamlit's execution model
    conn = sqlite3.connect('users.db', check_same_thread=False)
    return conn

# Create Table
def create_usertable():
    conn = create_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS userstable(
            first_name TEXT,
            last_name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            phone_number TEXT,
            professional_status TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Add New User
def add_userdata(first_name, last_name, email, password, phone, status):
    conn = create_connection()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO userstable(first_name, last_name, email, password, phone_number, professional_status) VALUES (?,?,?,?,?,?)',
                  (first_name, last_name, email, password, phone, status))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # Email already exists in the database
    finally:
        conn.close()

# Verify Login
def login_user(email, password):
    conn = create_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM userstable WHERE email =? AND password = ?', (email, password))
    data = c.fetchall()
    conn.close()
    return data