import sqlite3
import pandas as pd
import feedparser
import requests
import os

DB_DIR = os.path.join(os.getcwd(), 'data')
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)
    
DB_NAME = os.path.join(DB_DIR, "jobs_database.db")
# --- NEW: A dedicated database just for saved jobs to prevent conflicts ---
SAVED_DB_NAME = os.path.join(DB_DIR, "saved_jobs_v2.db") 

def init_db():
    """Initializes the database with the new LOCATION column."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            company TEXT,
            location TEXT,  
            description TEXT,
            link TEXT,
            source TEXT,
            date_posted DATE DEFAULT CURRENT_DATE
        )
    ''')
    conn.commit()
    conn.close()

def fetch_rss_jobs():
    """Fetches LIVE jobs and safely extracts Location."""
    rss_feeds = [
        "https://weworkremotely.com/categories/remote-programming-jobs.rss",
        "https://remotive.com/remote-jobs/software-dev/feed",
        "https://www.python.org/jobs/feed/rss/"
    ]
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    total_added = 0
    
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        for url in rss_feeds:
            try:
                response = requests.get(url, headers=headers, timeout=10)
                feed = feedparser.parse(response.content)
                
                for entry in feed.entries: 
                    c.execute("SELECT id FROM jobs WHERE link = ?", (entry.link,))
                    if c.fetchone() is None:
                        desc = entry.title + " " + getattr(entry, 'summary', '')
                        location = getattr(entry, 'location', 'Remote / Global')
                        company_name = "Tech Company" 
                        
                        c.execute("INSERT INTO jobs (title, company, location, description, link, source) VALUES (?, ?, ?, ?, ?, ?)",
                                  (entry.title, company_name, location, desc, entry.link, "RSS Feed"))
                        total_added += 1
                        
            except Exception as e:
                print(f"⚠️ Failed to fetch from {url}: {e}")
                continue 
                    
        conn.commit()
        conn.close()
        return total_added
        
    except Exception as e:
        print(f"❌ Database Error: {e}")
        return total_added

def insert_dummy_jobs():
    """Updated fallback function to include location."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    dummy_jobs = [
        ("Python Backend Developer", "TechCorp", "New York, NY", "Looking for a Python developer with Django, API, and SQL experience.", "http://test.com/python-dev", "Manual Test Data"),
        ("Machine Learning Engineer", "AI Startup", "San Francisco, CA", "Must know Deep Learning, NLP, Python, and Vector Databases like FAISS.", "http://test.com/ml-engineer", "Manual Test Data"),
        ("React Frontend Developer", "WebStudio", "Remote", "We need a frontend developer skilled in React, CSS, JavaScript and HTML.", "http://test.com/react-dev", "Manual Test Data")
    ]
    
    count = 0
    for job in dummy_jobs:
        c.execute("SELECT id FROM jobs WHERE link = ?", (job[4],))
        if c.fetchone() is None:
            c.execute("INSERT INTO jobs (title, company, location, description, link, source) VALUES (?, ?, ?, ?, ?, ?)", job)
            count += 1
            
    conn.commit()
    conn.close()
    return count

def get_all_jobs():
    """Returns all jobs as a Pandas DataFrame."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM jobs", conn)
    conn.close()
    return df

def clear_database():
    """Deletes all jobs so you can start fresh."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM jobs")
    conn.commit()
    conn.close()

# --- THE UPDATED SAVED JOBS FUNCTIONS ---
def save_jobs_for_users(current_user, job_title, company_name, job_link):
    # Using the NEW database file name
    conn = sqlite3.connect(SAVED_DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            title TEXT,
            company TEXT,
            job_link TEXT
        )
    ''')

    cursor.execute('''
        SELECT 1 FROM saved_jobs 
        WHERE user_id = ? AND job_link = ?
    ''', (current_user, job_link))
    
    if cursor.fetchone():
        conn.close()
        return False

    cursor.execute('''
        INSERT INTO saved_jobs (user_id, title, company, job_link)
        VALUES (?, ?, ?, ?)
    ''', (current_user, job_title, company_name, job_link))

    conn.commit()
    conn.close()
    return True

def get_saved_jobs(current_user):
    # Using the NEW database file name
    conn = sqlite3.connect(SAVED_DB_NAME)
    
    try:
        query = "SELECT title, company, job_link FROM saved_jobs WHERE user_id = ?"
        df = pd.read_sql_query(query, conn, params=(current_user,))
    except Exception:
        # If the table doesn't exist yet, return an empty dataframe
        df = pd.DataFrame(columns=['title', 'company', 'job_link'])
        
    conn.close()
    return df

def remove_saved_job(current_user, job_link):
    """Removes a saved job from a user's profile."""
    # Using the NEW database file name
    conn = sqlite3.connect(SAVED_DB_NAME)
    c = conn.cursor()
    
    # Updated to match the user_id column name
    c.execute("DELETE FROM saved_jobs WHERE user_id = ? AND job_link = ?", (current_user, job_link))
    conn.commit()
    conn.close()