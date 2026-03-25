import streamlit as st
import pandas as pd
import sqlite3
import re
import os
from fpdf import FPDF
from dotenv import load_dotenv
import google.generativeai as genai

# Import your local modules
from backend import init_db, fetch_rss_jobs, DB_NAME, save_job_for_user, get_saved_jobs, remove_saved_job
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
# FEATURE: AI ATS RESUME BUILDER
# --------------------------------
def render_resume_builder():
    """Renders a dynamic, AI-powered ATS resume builder."""
    st.markdown("---")
    st.header("📝 AI-Powered ATS Resume Builder")
    st.write("Fill out your details below. Use the ✨ **AI Enhance** button to instantly upgrade your bullet points!")

    # --- Callbacks for AI Enhancements (Runs before the UI updates) ---
    def enhance_exp_callback(idx):
        st.toast("✨ AI is rewriting your experience...", icon="🤖")
        current_text = st.session_state[f"exp_bullets_{idx}"]
        prompt = f"You are an expert tech recruiter. Rewrite these resume bullet points to be highly professional, impactful, and ATS-friendly. Start every line with a hyphen (-). Do not include any conversational text. Here are the points:\n{current_text}"
        st.session_state[f"exp_bullets_{idx}"] = ask_gemini(prompt)
        st.toast("✅ Enhancement complete!", icon="✅")

    def enhance_proj_callback(idx):
        st.toast("✨ AI is rewriting your project...", icon="🤖")
        current_text = st.session_state[f"proj_bullets_{idx}"]
        prompt = f"You are an expert tech recruiter. Rewrite these project bullet points to highlight technical skills and impact. Start every line with a hyphen (-). Do not include conversational text. Here are the points:\n{current_text}"
        st.session_state[f"proj_bullets_{idx}"] = ask_gemini(prompt)
        st.toast("✅ Enhancement complete!", icon="✅")

    # --- Initialize Session State for Dynamic Fields ---
    if 'exp_count' not in st.session_state: st.session_state['exp_count'] = 1
    if 'proj_count' not in st.session_state: st.session_state['proj_count'] = 1

    # Default initial values for the first text areas so they aren't blank
    if 'exp_bullets_0' not in st.session_state:
        st.session_state['exp_bullets_0'] = "- Developed RESTful APIs using Python, improving data retrieval speeds by 15%.\n- Collaborated with frontend team to integrate backend services."
    if 'proj_bullets_0' not in st.session_state:
        st.session_state['proj_bullets_0'] = "- Built an interactive dashboard using Streamlit and Pandas.\n- Implemented a recommendation algorithm using Scikit-Learn."

    # --- 1. Personal Details ---
    st.subheader("1. Personal Details")
    col1, col2 = st.columns(2)
    first_name = col1.text_input("First Name *", value="Samriti")
    last_name = col2.text_input("Last Name *", value="")
    
    col3, col4 = st.columns(2)
    email = col3.text_input("Email Address *", value="samriti@email.com")
    phone = col4.text_input("Phone Number", value="(555) 012-3456")
    
    col5, col6 = st.columns(2)
    location = col5.text_input("City, State", value="Jalandhar, Punjab")
    linkedin = col6.text_input("LinkedIn / Portfolio URL", value="linkedin.com/in/samriti")

    # --- 2. Professional Summary ---
    st.subheader("2. Professional Summary")
    summary = st.text_area("Short summary of your background", value="Detail-oriented Software Engineer with a strong foundation in backend development and data analysis. Passionate about building scalable applications and leveraging machine learning.")

    # --- 3. Education ---
    st.subheader("3. Education")
    col_ed1, col_ed2 = st.columns(2)
    degree = col_ed1.text_input("Degree / Program", value="B.Tech in Computer Science")
    school = col_ed2.text_input("University / Institution", value="DAV Institute of Engineering & Technology")
    grad_date = st.text_input("Graduation Date (e.g., Expected May 2026)", value="Expected 2027")

    # --- 4. Work Experience (Dynamic) ---
    st.subheader("4. Work Experience")
    experiences = []
    
    for i in range(st.session_state['exp_count']):
        st.markdown(f"**💼 Role {i+1}**")
        col_e1, col_e2 = st.columns(2)
        job_title = col_e1.text_input("Job Title", key=f"job_title_{i}", value="Software Engineering Intern" if i==0 else "")
        company = col_e2.text_input("Company Name", key=f"company_{i}", value="TechNova Solutions" if i==0 else "")
        job_dates = st.text_input("Dates (e.g., Jun 2025 - Aug 2025)", key=f"job_dates_{i}", value="Jun 2025 - Aug 2025" if i==0 else "")
        
        st.write("Job Description (Bullet Points)")
        c_text, c_btn = st.columns([4, 1])
        with c_text:
            bullets = st.text_area("Bullets", key=f"exp_bullets_{i}", label_visibility="collapsed", height=120)
        with c_btn:
            st.button("✨ Enhance via AI", key=f"ai_exp_{i}", on_click=enhance_exp_callback, args=(i,))
                    
        experiences.append({"title": job_title, "company": company, "dates": job_dates, "bullets": bullets})
        st.markdown("---")

    if st.button("➕ Add Another Job"):
        st.session_state['exp_count'] += 1
        st.session_state[f"exp_bullets_{st.session_state['exp_count']-1}"] = "- Add your responsibilities here..."
        st.rerun()

    # --- 5. Projects (Dynamic) ---
    st.subheader("5. Key Projects")
    projects = []
    
    for i in range(st.session_state['proj_count']):
        st.markdown(f"**🚀 Project {i+1}**")
        col_p1, col_p2 = st.columns(2)
        proj_name = col_p1.text_input("Project Name", key=f"proj_name_{i}", value="E-Commerce Analytics Dashboard" if i==0 else "")
        proj_role = col_p2.text_input("Your Role", key=f"proj_role_{i}", value="Lead Developer" if i==0 else "")
        proj_dates = st.text_input("Dates", key=f"proj_dates_{i}", value="Jan 2025 - May 2025" if i==0 else "")
        
        st.write("Project Description (Bullet Points)")
        c_text_p, c_btn_p = st.columns([4, 1])
        with c_text_p:
            p_bullets = st.text_area("Project Bullets", key=f"proj_bullets_{i}", label_visibility="collapsed", height=100)
        with c_btn_p:
            st.button("✨ Enhance via AI", key=f"ai_proj_{i}", on_click=enhance_proj_callback, args=(i,))
                    
        projects.append({"name": proj_name, "role": proj_role, "dates": proj_dates, "bullets": p_bullets})
        st.markdown("---")

    if st.button("➕ Add Another Project"):
        st.session_state['proj_count'] += 1
        st.session_state[f"proj_bullets_{st.session_state['proj_count']-1}"] = "- Describe what you built..."
        st.rerun()

    # --- 6. Skills ---
    st.subheader("6. Core Skills")
    skills = st.text_input("Technical Skills (Comma separated)", value="Python, SQL, Machine Learning, Data Analytics, Networking, Streamlit, Pandas")

    st.markdown("---")
    
    # --- Generate PDF Logic ---
    if st.button("⬇️ Generate Professional PDF", type="primary", use_container_width=True):
        if not first_name or not email:
            st.error("⚠️ Please enter at least your First Name and Email.")
        else:
            with st.spinner("Compiling ATS-Compliant PDF..."):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_auto_page_break(auto=True, margin=15)
                
                # Helper function to remove weird characters (ATS safety)
                def clean_pdf_text(text):
                    text = text.replace("•", "-").replace("⭐", "").replace("✨", "")
                    return text.encode('latin-1', 'replace').decode('latin-1')

                # --- HEADER ---
                full_name = f"{first_name} {last_name}".strip()
                pdf.set_font("Times", "B", 24)
                pdf.cell(0, 10, clean_pdf_text(full_name), ln=True, align="C")
                
                contact_info = []
                if location: contact_info.append(location)
                if phone: contact_info.append(phone)
                if email: contact_info.append(email)
                if linkedin: contact_info.append(linkedin)
                
                pdf.set_font("Times", "", 10)
                pdf.cell(0, 5, clean_pdf_text(" | ".join(contact_info)), ln=True, align="C")
                pdf.ln(4)

                def draw_section_header(title):
                    pdf.set_font("Times", "B", 11)
                    pdf.cell(0, 6, clean_pdf_text(title), ln=True, align="L")
                    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                    pdf.ln(2)

                # --- SUMMARY ---
                if summary:
                    draw_section_header("PROFESSIONAL SUMMARY")
                    pdf.set_font("Times", "", 10)
                    pdf.multi_cell(0, 5, clean_pdf_text(summary))
                    pdf.ln(4)

                # --- EDUCATION ---
                if degree or school:
                    draw_section_header("EDUCATION")
                    pdf.set_font("Times", "B", 10)
                    pdf.cell(0, 5, clean_pdf_text(school), ln=True)
                    pdf.set_font("Times", "", 10)
                    pdf.cell(0, 5, clean_pdf_text(f"{degree} | {grad_date}"), ln=True)
                    pdf.ln(4)

                # --- EXPERIENCE (Dynamic Loop) ---
                draw_section_header("WORK EXPERIENCE")
                for exp in experiences:
                    if exp["title"] or exp["company"]:
                        pdf.set_font("Times", "B", 10)
                        pdf.cell(0, 5, clean_pdf_text(exp["title"]), ln=True)
                        pdf.set_font("Times", "I", 10)
                        pdf.cell(0, 5, clean_pdf_text(f"{exp['company']} | {exp['dates']}"), ln=True)
                        
                        pdf.set_font("Times", "", 10)
                        for line in exp["bullets"].split('\n'):
                            if line.strip():
                                bullet = line.strip() if line.strip().startswith("-") else f"- {line.strip()}"
                                pdf.set_x(15) 
                                pdf.multi_cell(0, 5, clean_pdf_text(bullet))
                        pdf.ln(2)
                pdf.ln(2)

                # --- PROJECTS (Dynamic Loop) ---
                draw_section_header("PROJECTS")
                for proj in projects:
                    if proj["name"]:
                        pdf.set_font("Times", "B", 10)
                        pdf.cell(0, 5, clean_pdf_text(proj["name"]), ln=True)
                        pdf.set_font("Times", "I", 10)
                        pdf.cell(0, 5, clean_pdf_text(f"{proj['role']} | {proj['dates']}"), ln=True)
                        
                        pdf.set_font("Times", "", 10)
                        for line in proj["bullets"].split('\n'):
                            if line.strip():
                                bullet = line.strip() if line.strip().startswith("-") else f"- {line.strip()}"
                                pdf.set_x(15)
                                pdf.multi_cell(0, 5, clean_pdf_text(bullet))
                        pdf.ln(2)
                pdf.ln(2)

                # --- SKILLS ---
                if skills:
                    draw_section_header("TECHNICAL SKILLS")
                    pdf.set_font("Times", "", 10)
                    skills_list = [s.strip() for s in skills.split(',') if s.strip()]
                    pdf.multi_cell(0, 5, clean_pdf_text(", ".join(skills_list)))

                pdf_bytes = pdf.output()

            st.success("✨ Professional PDF Resume Generated Successfully!")
            st.download_button(
                label="📥 Click Here to Download PDF",
                data=bytes(pdf_bytes),
                file_name=f"{first_name}_{last_name}_Resume.pdf",
                mime="application/pdf"
            )

# --------------------------------
# THE MAIN DASHBOARD FUNCTION
# --------------------------------
def main():
    # --- 1. USER SIDEBAR ---
    current_user = st.session_state.get('username', 'Guest')
    
    st.sidebar.title(f"Welcome, {st.session_state.get('first_name', current_user)}!")
    st.sidebar.divider()
    
    st.sidebar.header("Job Controls")
    if st.sidebar.button("🔄 Fetch Latest Jobs"):
        with st.spinner("Fetching jobs from APIs and RSS feeds..."):
            new_jobs = fetch_rss_jobs()
            st.sidebar.success(f"{new_jobs} jobs added!")
            
    # --- SAVED JOBS DASHBOARD (Sidebar) ---
    with st.sidebar.expander("📁 View My Saved Jobs", expanded=False):
        saved_jobs = get_saved_jobs(current_user)
        
        # We extract just the links into a list so our main page buttons know what is saved!
        saved_links = [job[2] for job in saved_jobs] 
        
        if not saved_jobs:
            st.info("You haven't saved any jobs yet. Start exploring!")
        else:
            for i, job in enumerate(saved_jobs):
                title, company, link = job
                st.markdown(f"**{title}**\n*{company}*")
                
                # Side-by-side View and Unsave buttons in the sidebar
                col_sb1, col_sb2 = st.columns(2)
                with col_sb1:
                    st.link_button("View", link, use_container_width=True)
                with col_sb2:
                    if st.button("❌ Unsave", key=f"unsave_sidebar_{i}", use_container_width=True):
                        remove_saved_job(current_user, link)
                        st.rerun() # Instantly refreshes the UI
                st.divider()
                
    st.sidebar.button("Logout", use_container_width=True, on_click=lambda: st.session_state.update({'logged_in': False}))

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

                    # --- APPLY & SAVE BUTTONS ---
                    col_btn1, col_btn2 = st.columns([1, 4])
                    with col_btn1:
                        st.link_button("🚀 Apply Here", row['link'], type="primary")
                    with col_btn2:
                        if st.button("⭐ Save Job", key=f"save_{row['link']}"):
                            success = save_job_for_user(current_user, row['link'])
                            if success:
                                st.toast("Job saved to your dashboard! 📁", icon="✅")
                            else:
                                st.toast("You already saved this job!", icon="⚠️")
        else:
            st.info("👆 Upload your resume to see job recommendations!")

    # ==========================================
    # TAB 2: RESUME BUILDER
    # ==========================================
    with tab2:
        render_resume_builder()