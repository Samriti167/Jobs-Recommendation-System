import streamlit as st
import pandas as pd
import sqlite3
import re
import os
from fpdf import FPDF
from dotenv import load_dotenv
import google.generativeai as genai

# Import your local modules
from backend import init_db, fetch_rss_jobs, DB_NAME
from ai_engine import extract_text_from_pdf, clean_text, calculate_similarity

# --------------------------------
# Initialize Free Gemini API via .env
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
# FEATURE: RESUME BUILDER FUNCTION
# --------------------------------
# --------------------------------
# FEATURE: RESUME BUILDER FUNCTION (Now with PDF!)
# FEATURE: ADVANCED RESUME BUILDER
# --------------------------------


# --------------------------------
# FEATURE: CLASSIC ATS RESUME BUILDER
# --------------------------------
def render_resume_builder():
    """Renders a classic, single-column resume matching the traditional Patrick Sullivan template."""
    st.markdown("---")
    st.header("📝 Classic ATS Resume Builder")
    st.write("This template generates a traditional, highly professional resume format favored by recruiters.")

    with st.form("classic_resume_form"):
        # 1. Contact Info
        st.subheader("1. Header / Contact Info")
        col1, col2 = st.columns(2)
        name = col1.text_input("Full Name *", value="Samriti")
        address = col2.text_input("City, State", value="Jalandhar, Punjab")
        
        col3, col4 = st.columns(2)
        phone = col3.text_input("Phone", placeholder="(555) 123-4567")
        email = col4.text_input("Email *", value="samriti@email.com")

        # 2. Mission Statement
        st.subheader("2. Mission Statement")
        summary = st.text_area(
            "A brief professional summary.", 
            value="Energetic and detail-oriented Computer Science student with a strong foundation in Machine Learning and Python programming. Looking to leverage my technical skills, passion for AI-driven systems, and data analysis expertise in a challenging engineering role."
        )

        # 3. Education
        st.subheader("3. Education")
        st.caption("Use the '|' symbol to put the date on the right side.")
        education = st.text_area(
            "Education", 
            value="DAV Institute of Engineering & Technology - Jalandhar, PB | Expected June 2027\nB.Tech in Computer Science"
        )

        # 4. Skills (Will be formatted into 3 columns automatically!)
        st.subheader("4. Skills")
        st.caption("Separate skills with commas. The PDF will automatically format them into a 3-column list.")
        skills = st.text_area(
            "Technical Skills", 
            value="Python, Machine Learning, Data Analytics, C++, SQL, Streamlit, Scikit-Learn, Pandas, Git"
        )

        # 5. Experience & Projects
        st.subheader("5. Work Experience & Projects")
        st.caption("Use the '|' symbol to put the date on the right side. Start bullet points with '-'")
        experience = st.text_area(
            "Experience / Projects", 
            value="AI Job Recommendation System - Academic Project | Jan 2026 - Present\nLead Developer\n- Built a robust hybrid job matching engine using Python to accurately connect candidate resumes with relevant jobs.\n- Engineered text extraction and skill gap analysis algorithms to improve recommendation accuracy.\n- Designed an interactive UI using Streamlit and managed backend job data integration using SQLite.\n\nStudent Mentoring Platform - Academic Project | Aug 2025 - Dec 2025\nBackend Developer\n- Developed a hybrid system combining rule-based logic and Machine Learning models to create an intelligent mentoring platform.\n- Built a Student Risk Index algorithm to proactively identify and assist at-risk students.\n- Implemented automated mentor-matching algorithms to optimize pairings based on student needs.",
            height=250
        )

        submit_resume = st.form_submit_button("Generate Classic Resume (.pdf)")

    # --- Generate PDF Logic ---
    if submit_resume:
        if not name or not email:
            st.error("⚠️ Please enter at least your Name and Email to generate the resume.")
        else:
            with st.spinner("Rendering PDF..."):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_auto_page_break(auto=True, margin=15)
                
                # Helper function for text encoding
                def clean_text(text):
                    return text.encode('latin-1', 'replace').decode('latin-1')

                # --- 1. HEADER ---
                # Name (Italicized for elegance)
                pdf.set_font("Times", "I", 24)
                pdf.cell(0, 10, clean_text(name), ln=True, align="C")
                
                # Contact Info
                pdf.set_font("Times", "B", 10)
                if address:
                    pdf.cell(0, 5, clean_text(address), ln=True, align="C")
                if phone:
                    pdf.cell(0, 5, clean_text(phone), ln=True, align="C")
                
                # Email (Blue and underlined like a link)
                pdf.set_text_color(0, 0, 255)
                pdf.set_font("Times", "BU", 10)
                pdf.cell(0, 5, clean_text(email), ln=True, align="C")
                pdf.set_text_color(0, 0, 0) # Reset color
                pdf.ln(5)

                # --- HELPER: SECTION HEADER ---
                def draw_section_header(title, align="L"):
                    pdf.set_font("Times", "B", 11)
                    pdf.cell(0, 6, title, ln=True, align=align)
                    # Draw a horizontal line just below the text
                    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                    pdf.ln(3)

                # --- 2. MISSION STATEMENT ---
                if summary:
                    draw_section_header("MISSION STATEMENT", align="C")
                    pdf.set_font("Times", "", 10)
                    pdf.multi_cell(0, 5, clean_text(summary), align="C")
                    pdf.ln(5)

                # --- 3. EDUCATION ---
                if education:
                    draw_section_header("EDUCATION")
                    for line in education.split('\n'):
                        if not line.strip(): continue
                        if '|' in line:
                            left, right = line.split('|', 1)
                            pdf.set_font("Times", "B", 10)
                            y = pdf.get_y()
                            pdf.cell(140, 5, clean_text(left.strip()))
                            pdf.set_xy(150, y)
                            pdf.cell(45, 5, clean_text(right.strip()), align="R")
                            pdf.ln(5)
                        else:
                            pdf.set_font("Times", "I", 10)
                            pdf.cell(0, 5, clean_text(line.strip()), ln=True)
                    pdf.ln(5)

                # --- 4. SKILLS (3-COLUMN LAYOUT) ---
                if skills:
                    draw_section_header("SKILLS")
                    pdf.set_font("Times", "", 10)
                    skills_list = [s.strip() for s in skills.split(',')]
                    start_y = pdf.get_y()
                    
                    for i, skill in enumerate(skills_list):
                        if not skill: continue
                        col = i % 3
                        row = i // 3
                        x_pos = 15 + (col * 60)
                        y_pos = start_y + (row * 5)
                        pdf.set_xy(x_pos, y_pos)
                        pdf.cell(60, 5, clean_text(f"• {skill}"))
                    
                    # Move Y down past the columns
                    total_rows = (len(skills_list) - 1) // 3 + 1
                    pdf.set_y(start_y + (total_rows * 5) + 5)

                # --- 5. WORK EXPERIENCE ---
                if experience:
                    draw_section_header("WORK EXPERIENCE")
                    for line in experience.split('\n'):
                        if not line.strip():
                            pdf.ln(2)
                            continue
                        
                        if '|' in line:
                            # Company & Date
                            left, right = line.split('|', 1)
                            pdf.set_font("Times", "B", 10)
                            y = pdf.get_y()
                            pdf.cell(140, 5, clean_text(left.strip()))
                            pdf.set_xy(150, y)
                            pdf.cell(45, 5, clean_text(right.strip()), align="R")
                            pdf.ln(5)
                        elif line.strip().startswith('-') or line.strip().startswith('•'):
                            # Bullet points
                            pdf.set_font("Times", "", 10)
                            pdf.set_x(15) # Indent bullets slightly
                            bullet_text = clean_text(f"• {line.strip()[1:].strip()}")
                            pdf.multi_cell(0, 5, bullet_text)
                        else:
                            # Job Title (Italics)
                            pdf.set_font("Times", "I", 10)
                            pdf.cell(0, 5, clean_text(line.strip()), ln=True)

                pdf_bytes = pdf.output()

            st.success("✨ Classic PDF Resume Generated Successfully!")
            
            # Download Button
            st.download_button(
                label="⬇️ Download Professional Resume (.pdf)",
                data=bytes(pdf_bytes),
                file_name=f"{name.replace(' ', '_')}_Resume.pdf",
                mime="application/pdf"
            )
# --------------------------------
# THE MAIN DASHBOARD FUNCTION
# --------------------------------
def main():
    # --- 1. USER SIDEBAR ---
    st.sidebar.title(f"Welcome, {st.session_state.get('first_name', 'User')}!")
    st.sidebar.divider()
    
    st.sidebar.header("Job Controls")
    if st.sidebar.button("🔄 Fetch Latest Jobs"):
        with st.spinner("Fetching jobs from APIs and RSS feeds..."):
            new_jobs = fetch_rss_jobs()
            st.sidebar.success(f"{new_jobs} jobs added!")
            
    st.sidebar.divider()
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state['logged_in'] = False
        st.rerun()

    # --- 2. HEADER & TABS ---
    st.title("💼 AI Job Recommendation System")
    init_db()
    
    # Create the Tabs
    tab1, tab2 = st.tabs(["🔍 Find Jobs", "📝 Resume Builder"])

    # ==========================================
    # TAB 1: FIND JOBS
    # ==========================================
    with tab1:
        st.write("Upload your resume and get AI-matched jobs.")
        uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

        if uploaded_file:
            with st.spinner("Reading resume..."):
                raw_resume_text = extract_text_from_pdf(uploaded_file)
                resume_text = clean_text(raw_resume_text)

            conn = sqlite3.connect(DB_NAME)
            df = pd.read_sql_query(
                "SELECT title, company, location, description, link, source FROM jobs",
                conn
            )
            conn.close()

            df = df.drop_duplicates(subset="link")

            if df.empty:
                st.warning("No jobs available in the database. Please fetch jobs first using the sidebar.")
            else:
                with st.spinner("Calculating match scores..."):
                    job_descriptions = (df["title"] + " " + df["description"]).apply(clean_text).tolist()
                    scores = calculate_similarity(resume_text, job_descriptions)

                    df["match_score"] = scores
                    df = df.sort_values(by="match_score", ascending=False)

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

                    with st.spinner(f"AI is building a learning roadmap for {row['company']}..."):
                        roadmap_prompt = f"""
                        You are a senior technical mentor. A candidate is missing the following skills for a job:
                        {missing_skills}

                        Create a very brief, step-by-step learning roadmap. Tell the candidate the logical order they should learn these missing skills. 
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
        else:
            st.info("👆 Upload your resume to see job recommendations!")

    # ==========================================
    # TAB 2: RESUME BUILDER
    # ==========================================
    with tab2:
        render_resume_builder()