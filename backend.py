import sqlite3
import requests
import feedparser
import os
from openai import OpenAI

from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
client = OpenAI(api_key=OPENAI_API_KEY)

# -----------------------------
# Database setup
# -----------------------------

DB_DIR = os.path.join(os.getcwd(), "data")

if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

DB_NAME = os.path.join(DB_DIR, "jobs_database.db")


# -----------------------------
# Initialize Database
# -----------------------------

def init_db():

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS jobs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        company TEXT,
        location TEXT,
        description TEXT,
        link TEXT UNIQUE,
        source TEXT,
        date_posted DATE DEFAULT CURRENT_DATE
    )
    """)

    conn.commit()
    conn.close()


# -----------------------------
# Insert Job Safely
# -----------------------------

def insert_job(title, company, location, description, link, source):

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    try:
        c.execute("""
        INSERT INTO jobs (title, company, location, description, link, source)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (title, company, location, description, link, source))

        conn.commit()

    except sqlite3.IntegrityError:
        pass

    conn.close()


# -----------------------------
# Remotive API Jobs
# -----------------------------

def fetch_remotive_jobs():

    url = "https://remotive.com/api/remote-jobs"

    response = requests.get(url)
    data = response.json()

    count = 0

    for job in data["jobs"]:

        insert_job(
            job["title"],
            job["company_name"],
            job["candidate_required_location"],
            job["description"],
            job["url"],
            "Remotive"
        )

        count += 1

    return count


# -----------------------------
# Arbeitnow API Jobs
# -----------------------------

def fetch_arbeitnow_jobs():

    url = "https://www.arbeitnow.com/api/job-board-api"

    response = requests.get(url)
    data = response.json()

    count = 0

    for job in data["data"]:

        insert_job(
            job["title"],
            job["company_name"],
            job["location"],
            job["description"],
            job["url"],
            "Arbeitnow"
        )

        count += 1

    return count


# -----------------------------
# RSS Job Feeds
# -----------------------------

def fetch_rss_jobs():

    rss_feeds = [
        "https://weworkremotely.com/categories/remote-programming-jobs.rss",
        "https://www.python.org/jobs/feed/rss/"
    ]

    total = 0

    for url in rss_feeds:

        feed = feedparser.parse(url)

        for entry in feed.entries:

            insert_job(
                entry.title,
                "Tech Company",
                "Remote / Global",
                entry.summary,
                entry.link,
                "RSS Feed"
            )

            total += 1

    return total


# -----------------------------
# Update All Jobs
# -----------------------------

def update_jobs():

    remotive = fetch_remotive_jobs()
    arbeitnow = fetch_arbeitnow_jobs()
    rss = fetch_rss_jobs()

    total = remotive + arbeitnow + rss

    print(f"{total} jobs added")

    return total


# -----------------------------
# Get All Jobs
# -----------------------------

def get_all_jobs():

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    SELECT title, company, location, description, link, source
    FROM jobs
    ORDER BY date_posted DESC
    """)

    jobs = c.fetchall()

    conn.close()

    return jobs


def ask_openai(prompt, max_tokens=500):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature= 0.5,
        max_tokens=max_tokens
    )

    return response.choices[0].message.content