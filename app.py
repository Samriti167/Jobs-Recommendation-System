import streamlit as st
import pandas as pd
import sqlite3
import re
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Import your local modules
from backend import init_db, update_jobs, DB_NAME
from ai_engine import extract_text_from_pdf, clean_text, calculate_similarity

# --------------------------------
# Page Config
# --------------------------------
st.set_page_config(
    page_title="AI Job Recommender",
    page_icon="💼",
    layout="wide"
)

st.title("💼 AI Job Recommendation System")
st.write("Upload your resume and get AI-matched jobs.")

# --------------------------------
# Initialize Free Gemini API via .env
# --------------------------------
# Load the .env file safely
load_dotenv()

# Safely fetch the key from the environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Stop the app and warn you if the key is missing
if not GEMINI_API_KEY:
    st.error("🚨 GEMINI_API_KEY is missing! Please check your .env file.")
    st.stop()

# Configure the AI with the loaded key
genai.configure(api_key=GEMINI_API_KEY)

def ask_gemini(prompt):
    """Uses the free Gemini API to analyze text."""
    try:
        # Note: Depending on your exact Google SDK version, if 2.5 throws a 404, 
        # you can change this back to 'gemini-2.0-flash' or 'gemini-1.5-flash'
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error connecting to AI: {e}"

# --------------------------------
# Initialize Database
# --------------------------------
init_db()

# --------------------------------
# Sidebar Controls
# --------------------------------
st.sidebar.header("Job Controls")

if st.sidebar.button("🔄 Fetch Latest Jobs"):
    with st.spinner("Fetching jobs from APIs and RSS feeds..."):
        new_jobs = update_jobs()
        st.sidebar.success(f"{new_jobs} jobs added!")

# --------------------------------
# Upload Resume
# --------------------------------
uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

if uploaded_file is None:
    st.info("Upload your resume to see job recommendations.")
    st.stop()

# --------------------------------
# Extract Resume Text
# --------------------------------
with st.spinner("Reading resume..."):
    raw_resume_text = extract_text_from_pdf(uploaded_file)
    resume_text = clean_text(raw_resume_text)

# --------------------------------
# Load Jobs from Database
# --------------------------------
conn = sqlite3.connect(DB_NAME)
df = pd.read_sql_query(
    "SELECT title, company, location, description, link, source FROM jobs",
    conn
)
conn.close()

# Drop duplicate jobs based on the link
df = df.drop_duplicates(subset="link")

if df.empty:
    st.warning("No jobs available in the database. Please fetch jobs first using the sidebar.")
    st.stop()

# --------------------------------
# AI Similarity Matches (Local)
# --------------------------------
with st.spinner("Calculating match scores..."):
    job_descriptions = (df["title"] + " " + df["description"]).apply(clean_text).tolist()
    scores = calculate_similarity(resume_text, job_descriptions)

    df["match_score"] = scores
    df = df.sort_values(by="match_score", ascending=False)


# --------------------------------
# Display Top Jobs & Per-Job AI Analysis
# --------------------------------
st.markdown("---")
st.subheader("🎯 Top Job Matches")

# Changed to 5 to avoid hitting the free Gemini rate limit (15 requests/minute)
top_jobs = df.head(5)

def clean_html(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

for _, row in top_jobs.iterrows():
    st.markdown("---")
    st.subheader(row["title"])
    st.write(f"**🏢 Company:** {row['company']}")
    st.write(f"**📍 Location:** {row['location']}")
    st.write(f"**🌐 Source:** {row['source']}")

    # Safely calculate the match score so the progress bar doesn't break
    raw_score = row['match_score']
    # Clamp the score between 0.0 and 1.0 just in case the math model is slightly off
    safe_score = max(0.0, min(1.0, float(raw_score)))
    score_percentage = int(safe_score * 100)
    
    st.write(f"**🎯 Match Score:** {score_percentage}%")
    st.progress(score_percentage)

    # Clean the description for the AI and the UI
    description = clean_html(row["description"])
    
    with st.expander("Read Job Description"):
        st.markdown(row["description"], unsafe_allow_html=True)
    
    # Per-Job Skill Gap Analysis using Gemini
    with st.spinner(f"AI is analyzing missing skills for {row['company']}..."):
        prompt = f"""
        You are an expert career coach. Compare the following resume to the specific job description.
        List ONLY the specific skills, tools, or experience required by the job that are MISSING from the resume.
        Keep it very brief and use bullet points. If there are no missing skills, say "Strong match! No major missing skills."

        Job Description: {description}

        Resume: {resume_text}
        """
        missing_skills = ask_gemini(prompt)
    
    # Display the missing skills for this specific job
    st.write("**⚠ Missing Skills for this Role:**")
    st.markdown(
        f"<div style='background-color: #2b0000; padding: 15px; border-radius: 10px; font-size: 15px; color:#ffcccc; border: 1px solid #ff4d4d;'>{missing_skills}</div><br>", 
        unsafe_allow_html=True
    )

    # ---------------------------------------------------------
    # Generate Learning Roadmap using Gemini
    # ---------------------------------------------------------
    with st.spinner(f"AI is building a learning roadmap for {row['company']}..."):
        roadmap_prompt = f"""
        You are a senior technical mentor. A candidate is missing the following skills for a job:
        {missing_skills}

        Create a very brief, step-by-step learning roadmap. Tell the candidate the logical order they should learn these missing skills (e.g., what to learn first, second, and why). 
        Keep it concise, actionable, and use a numbered list. 
        If the missing skills say "Strong match", simply reply: "You are ready! Focus on interview prep."
        """
        roadmap = ask_gemini(roadmap_prompt)
    
    # Display the Roadmap for this specific job
    st.write("**🗺️ Actionable Learning Roadmap:**")
    st.markdown(
        f"<div style='background-color: #001a33; padding: 15px; border-radius: 10px; font-size: 15px; color:#cce6ff; border: 1px solid #3399ff;'>{roadmap}</div><br>", 
        unsafe_allow_html=True
    )

    st.markdown(f"[**Apply Here**]({row['link']})")