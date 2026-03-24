import sqlite3
import pandas as pd
import feedparser
import requests
import os

# Ensure the absolute path so app.py and backend.py always use the EXACT same file
DB_DIR = os.path.join(os.getcwd(), 'data')
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)
    
DB_NAME = os.path.join(DB_DIR, "jobs_database.db")

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

    c.execute("""
    CREATE TABLE IF NOT EXISTS saved_jobs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        job_link TEXT,
        UNIQUE(username, job_link)
    )
    """)
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
                        
                        # Extract location safely (Default to "Remote / Global" if not found)
                        location = getattr(entry, 'location', 'Remote / Global')
                        
                        # We also insert a generic company name since RSS sometimes hides it
                        company_name = "Tech Company" 
                        
                        # INSERT including the new location variable
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
    
    # Notice the new "Location" string added to these dummy jobs (e.g., "New York, NY")
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
# def init_db():
#     """Initializes the database and creates the table if it doesn't exist."""
#     conn = sqlite3.connect(DB_NAME)
#     c = conn.cursor()
#     c.execute('''
#         CREATE TABLE IF NOT EXISTS jobs (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             title TEXT,
#             company TEXT,
#             description TEXT,
#             link TEXT,
#             source TEXT,
#             date_posted DATE DEFAULT CURRENT_DATE
#         )
#     ''')
#     conn.commit()
#     conn.close()

# def fetch_rss_jobs():
#     """Fetches LIVE jobs from multiple diverse RSS feeds without limits."""
#     # odl rss feed
#     # # The Diverse Array of Open Job Boards
#     # rss_feeds = [
#     #     "https://weworkremotely.com/categories/remote-programming-jobs.rss",
#     #     "https://remotive.com/remote-jobs/software-dev/feed",
#     #     "https://www.python.org/jobs/feed/rss/"
#     # ]
#     # The "All Domains" Diverse Array of Open Job Boards
#     rss_feeds = [
#         # --- SOFTWARE & IT ---
#         "https://weworkremotely.com/categories/remote-programming-jobs.rss",
#         "https://remotive.com/remote-jobs/software-dev/feed",
        
#         # --- DESIGN & UI/UX ---
#         "https://weworkremotely.com/categories/remote-design-jobs.rss",
#         "https://remotive.com/remote-jobs/design/feed",
        
#         # --- SALES & MARKETING ---
#         "https://weworkremotely.com/categories/remote-sales-and-marketing-jobs.rss",
#         "https://remotive.com/remote-jobs/marketing/feed",
#         "https://remotive.com/remote-jobs/sales/feed",
        
#         # --- FINANCE, HR & MANAGEMENT ---
#         "https://weworkremotely.com/categories/remote-management-and-finance-jobs.rss",
#         "https://remotive.com/remote-jobs/hr/feed",
        
#         # --- CUSTOMER SUPPORT ---
#         "https://weworkremotely.com/categories/remote-customer-support-jobs.rss",
#         "https://remotive.com/remote-jobs/customer-support/feed",
        
#         # --- GENERAL / ALL OTHER JOBS (Copywriting, Data Entry, etc.) ---
#         "https://weworkremotely.com/categories/remote-copywriting-jobs.rss",
#         "https://remoteok.com/api?format=rss"
#     ]
    
#     headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
#     total_added = 0
    
#     # --- OUTER TRY BLOCK: Protects the Database ---
#     try:
#         conn = sqlite3.connect(DB_NAME)
#         c = conn.cursor()
        
#         # Loop through every URL in our list
#         for url in rss_feeds:
            
#             # --- INNER TRY BLOCK: Protects the Web Request ---
#             try:
#                 response = requests.get(url, headers=headers, timeout=10)
#                 feed = feedparser.parse(response.content)
                
#                 for entry in feed.entries: 
#                     # Duplicate check using the link
#                     c.execute("SELECT id FROM jobs WHERE link = ?", (entry.link,))
#                     if c.fetchone() is None:
#                         # Safely grab the description/summary
#                         desc = entry.title + " " + getattr(entry, 'summary', '')
                        
#                         c.execute("INSERT INTO jobs (title, company, description, link, source) VALUES (?, ?, ?, ?, ?)",
#                                   (entry.title, "Remote Company", desc, entry.link, "RSS Feed"))
#                         total_added += 1
                        
#             except Exception as e:
#                 # If ONE website fails, it prints the error here and CONTINUES to the next website!
#                 print(f"⚠️ Failed to fetch from {url}: {e}")
#                 continue 
#             # ------------------------------------------------
                    
#         conn.commit()
#         conn.close()
#         return total_added
        
#     except Exception as e:
#         print(f"❌ Database Error: {e}")
#         return total_added
#     # ----------------------------------------------

def insert_dummy_jobs():
    """Fallback function to inject test data."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    dummy_jobs = [
        ("Python Backend Developer", "TechCorp", "Looking for a Python developer with Django, API, and SQL experience.", "http://test.com/python-dev", "Manual Test Data"),
        ("Machine Learning Engineer", "AI Startup", "Must know Deep Learning, NLP, Python, and Vector Databases like FAISS.", "http://test.com/ml-engineer", "Manual Test Data"),
        ("React Frontend Developer", "WebStudio", "We need a frontend developer skilled in React, CSS, JavaScript and HTML.", "http://test.com/react-dev", "Manual Test Data")
    ]
    
    count = 0
    for job in dummy_jobs:
        c.execute("SELECT id FROM jobs WHERE link = ?", (job[3],))
        if c.fetchone() is None:
            c.execute("INSERT INTO jobs (title, company, description, link, source) VALUES (?, ?, ?, ?, ?)", job)
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


# Add these to the bottom of backend.py
def save_job_for_user(username, job_link):
    """Saves a job link to a user's profile."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO saved_jobs (username, job_link) VALUES (?, ?)", (username, job_link))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # Job was already saved
    finally:
        conn.close()

def get_saved_jobs(username):
    """Fetches all saved jobs for a specific user."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT jobs.title, jobs.company, jobs.link 
        FROM jobs 
        JOIN saved_jobs ON jobs.link = saved_jobs.job_link 
        WHERE saved_jobs.username = ?
    """, (username,))
    saved = c.fetchall()
    conn.close()
    return saved