import streamlit as st
import pandas as pd
import sqlite3
import re
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Import your local modules
from backend import init_db, fetch_rss_jobs, DB_NAME
from ai_engine import extract_text_from_pdf, clean_text, calculate_similarity

# --------------------------------
# Initialize Free Gemini API via .env (Runs once on import)
# --------------------------------
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error("🚨 GEMINI_API_KEY is missing! Please check your .env file.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

def ask_gemini(prompt):
    """Uses the free Gemini API to analyze text."""
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error connecting to AI: {e}"

# --------------------------------
# THE MAIN FUNCTION (Called by app.py)
# --------------------------------
def main():
    # --- 1. USER SIDEBAR (Logout) ---
    st.sidebar.title(f"Welcome, {st.session_state.get('first_name', 'User')}!")
    st.sidebar.divider()
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state['logged_in'] = False
        st.rerun()

    # --- 2. HER JOB CONTROLS ---
    st.sidebar.header("Job Controls")
    if st.sidebar.button("🔄 Fetch Latest Jobs"):
        with st.spinner("Fetching jobs from APIs and RSS feeds..."):
            new_jobs = fetch_rss_jobs()
            st.sidebar.success(f"{new_jobs} jobs added!")

    # --- 3. THE DASHBOARD UI ---
    init_db()
    
    st.title("💼 AI Job Recommendation System")
    st.write("Upload your resume and get AI-matched jobs.")

    uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

    if uploaded_file is None:
        st.info("Upload your resume to see job recommendations.")
        return # Changed from st.stop() to keep the sidebar alive

    # Extract Resume Text
    with st.spinner("Reading resume..."):
        raw_resume_text = extract_text_from_pdf(uploaded_file)
        resume_text = clean_text(raw_resume_text)

    # Load Jobs from Database
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query(
        "SELECT title, company, location, description, link, source FROM jobs",
        conn
    )
    conn.close()

    df = df.drop_duplicates(subset="link")

    if df.empty:
        st.warning("No jobs available in the database. Please fetch jobs first using the sidebar.")
        return # Changed from st.stop()

    # AI Similarity Matches (Local)
    with st.spinner("Calculating match scores..."):
        job_descriptions = (df["title"] + " " + df["description"]).apply(clean_text).tolist()
        scores = calculate_similarity(resume_text, job_descriptions)

        df["match_score"] = scores
        df = df.sort_values(by="match_score", ascending=False)

    # Display Top Jobs & Per-Job AI Analysis
    st.markdown("---")
    st.subheader("🎯 Top Job Matches")

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

        raw_score = row['match_score']
        safe_score = max(0.0, min(1.0, float(raw_score)))
        score_percentage = int(safe_score * 100)
        
        st.write(f"**🎯 Match Score:** {score_percentage}%")
        st.progress(score_percentage)

        description = clean_html(row["description"])
        
        with st.expander("Read Job Description"):
            st.markdown(row["description"], unsafe_allow_html=True)
        
        # Per-Job Skill Gap Analysis
        with st.spinner(f"AI is analyzing missing skills for {row['company']}..."):
            prompt = f"""
            You are an expert career coach. Compare the following resume to the specific job description.
            List ONLY the specific skills, tools, or experience required by the job that are MISSING from the resume.
            Keep it very brief and use bullet points. If there are no missing skills, say "Strong match! No major missing skills."

            Job Description: {description}

            Resume: {resume_text}
            """
            missing_skills = ask_gemini(prompt)
        
        st.write("**⚠ Missing Skills for this Role:**")
        st.markdown(
            f"<div style='background-color: #2b0000; padding: 15px; border-radius: 10px; font-size: 15px; color:#ffcccc; border: 1px solid #ff4d4d;'>{missing_skills}</div><br>", 
            unsafe_allow_html=True
        )

        # Generate Learning Roadmap
        with st.spinner(f"AI is building a learning roadmap for {row['company']}..."):
            roadmap_prompt = f"""
            You are a senior technical mentor. A candidate is missing the following skills for a job:
            {missing_skills}

            Create a very brief, step-by-step learning roadmap. Tell the candidate the logical order they should learn these missing skills (e.g., what to learn first, second, and why). 
            Keep it concise, actionable, and use a numbered list. 
            If the missing skills say "Strong match", simply reply: "You are ready! Focus on interview prep."
            """
            roadmap = ask_gemini(roadmap_prompt)
        
        st.write("**🗺️ Actionable Learning Roadmap:**")
        st.markdown(
            f"<div style='background-color: #001a33; padding: 15px; border-radius: 10px; font-size: 15px; color:#cce6ff; border: 1px solid #3399ff;'>{roadmap}</div><br>", 
            unsafe_allow_html=True
        )

        st.markdown(f"[**Apply Here**]({row['link']})")