import streamlit as st
import pandas as pd
import sqlite3
import re
import os
from fpdf import FPDF
from dotenv import load_dotenv
import google.generativeai as genai
import plotly.graph_objects as go
from streamlit_lottie import st_lottie
import requests
from bs4 import BeautifulSoup

def load_lottieurl(url: str):
    """Helper function to load Lottie animations from a URL."""
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

# Import your local modules
from backend import init_db, fetch_rss_jobs, DB_NAME, save_job_for_user, get_saved_jobs, remove_saved_job
from ai_engine import extract_text_from_pdf, clean_text, calculate_similarity

def format_raw_job_description(raw_html):
    """Smart parser that identifies job sections and formats them with clear visual hierarchy."""
    from bs4 import BeautifulSoup
    import re
    
    if not isinstance(raw_html, str):
        return ""
        
    # 1. Parse the HTML
    soup = BeautifulSoup(raw_html, "html.parser")
    
    # 2. Insert newlines to separate HTML blocks properly
    for element in soup.find_all(["br", "p", "div", "h1", "h2", "h3", "h4"]):
        element.insert_after("\n")
    for element in soup.find_all("li"):
        element.insert_before("- ")
        element.insert_after("\n")
        
    text = soup.get_text()
    
    # 3. Standardize messy bullet characters
    text = text.replace("•", "-").replace("·", "-").replace(" * ", "\n- ")
    
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    cleaned_lines = []
    
    # 4. Dictionary of common section headers to hunt for
    section_keywords = [
        "requirements", "qualifications", "responsibilities", "what you'll do", 
        "about the role", "skills", "experience", "what we're looking for", 
        "benefits", "perks", "who you are", "role overview", "description",
        "key responsibilities", "required skills & experience", "good to have",
        "mandatory technical requirements"
    ]

    for line in lines:
        lower_line = line.lower()
        is_heading = False
        
        # --- HEADING DETECTION LOGIC ---
        # A. Short line ending with a colon (e.g., "Requirements:")
        if len(line) < 60 and line.endswith(':'):
            is_heading = True
            
        # B. Exact match or starts with common section keywords
        elif any(lower_line.startswith(kw) for kw in section_keywords) and len(line) < 50:
            is_heading = True
            
        # C. Short line that is ALL CAPS (e.g., "REQUIRED SKILLS")
        elif len(line) < 40 and line.isupper() and len(line) > 4:
            is_heading = True

        # --- APPLYING THE CLEAN FORMATTING ---
        if is_heading:
            # Strip the colon, title-case it, and make it a distinct Streamlit Subheader
            clean_heading = line.rstrip(':').title()
            # The '---' creates a clean horizontal line above the section
            cleaned_lines.append(f"\n---\n### 📌 {clean_heading}\n")
        elif line.startswith("-"):
            cleaned_lines.append(f"{line}")
        else:
            cleaned_lines.append(f"{line}\n")
            
    # 5. Bring it all together and clean up excess spacing
    final_text = "\n".join(cleaned_lines)
    final_text = re.sub(r'\n{3,}', '\n\n', final_text) 
    
    return final_text.strip()

#CSS INGECTION
def apply_dashboard_css():
    """Injects premium custom CSS and mobile-responsive media queries."""
    st.markdown("""
    <style>
        /* IMPORT PREMIUM GOOGLE FONT */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        /* Apply the font to text elements, avoiding Streamlit's internal icon spans */
        .stApp, p, h1, h2, h3, h4, h5, h6, label, input, select, button {
            font-family: 'Inter', sans-serif !important;
        }
        
        /* Explicitly protect Streamlit's Material Icons from being overwritten */
        .material-symbols-rounded, .material-icons {
            font-family: 'Material Symbols Rounded', 'Material Icons' !important;
        }

        /* --- THE NEW PROFESSIONAL DOT GRID BACKGROUND --- */
        .stApp { 
            background-color: #F9FAFB !important; 
            background-image: radial-gradient(#D1D5DB 1px, transparent 1px) !important;
            background-size: 24px 24px !important;
        }

        /* --- SIDEBAR STYLING --- */
        section[data-testid="stSidebar"] {
            background-color: #FFFFFF !important;
            border-right: 1px solid #E5E7EB !important;
            box-shadow: 4px 0 15px rgba(0,0,0,0.03) !important;
        }

        /* --- GLASSMORPHISM CARDS & EXPANDERS --- */
        div[data-testid="stExpander"], div[data-testid="stForm"], div[data-testid="stTabs"] {
            background: rgba(255, 255, 255, 0.65) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border: 1px solid rgba(255, 255, 255, 0.5) !important;
            border-radius: 12px !important;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.05) !important;
            transition: all 0.3s ease-in-out !important;
        }

        /* --- FLUID INPUT ANIMATIONS --- */
        div[data-testid="stTextInput"] div[data-baseweb="input"], 
        div[data-testid="stTextArea"] div[data-baseweb="textarea"] {
            background-color: #F3F4F6 !important; 
            border: 1px solid #9CA3AF !important; 
            border-radius: 6px !important; 
            transition: all 0.3s ease-in-out !important; 
        }
        div[data-testid="stTextInput"] input, 
        div[data-testid="stTextArea"] textarea {
            color: #111827 !important;
        }

        /* Active State */
        div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within,
        div[data-testid="stTextArea"] div[data-baseweb="textarea"]:focus-within {
            border: 1px solid #0066CC !important;
            box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.15) !important; 
            background-color: #FFFFFF !important; 
        }

        /* --- FLUID BUTTONS --- */
        div[data-testid="stButton"] > button {
            border-radius: 6px !important; 
            font-weight: 600 !important;
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important; 
        }
        div[data-testid="stButton"] > button:hover {
            transform: translateY(-2px) !important; 
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1) !important;
        }

        /* ==========================================
           📱 MOBILE RESPONSIVENESS (Media Queries)
           ========================================== */
        @media (max-width: 768px) {
            .block-container {
                padding-top: 2rem !important;
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }
            h1 { font-size: 1.8rem !important; }
            h2 { font-size: 1.5rem !important; }
            div[style*="background-color: #FEF2F2"], 
            div[style*="background-color: #F0FDF4"] {
                padding: 10px !important;
                font-size: 0.9rem !important;
            }
            div[data-testid="stMetricValue"] {
                font-size: 1.8rem !important;
            }
            div[style*="text-align: right;"] {
                text-align: left !important;
                margin-top: 10px !important;
            }
        }
    </style>
    """, unsafe_allow_html=True)

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
# FEATURE: CLASSIC ATS RESUME BUILDER
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
    first_name = col1.text_input("First Name *", value="Alex")
    last_name = col2.text_input("Last Name *", value="Carter")
    
    col3, col4 = st.columns(2)
    email = col3.text_input("Email Address *", value="alex.carter@email.com")
    phone = col4.text_input("Phone Number", value="(555) 012-3456")
    
    col5, col6 = st.columns(2)
    location = col5.text_input("City, State", value="San Francisco, CA")
    linkedin = col6.text_input("LinkedIn / Portfolio URL", value="linkedin.com/in/alexcarter")

    # --- 2. Professional Summary ---
    st.subheader("2. Professional Summary")
    summary = st.text_area("Short summary of your background", value="Detail-oriented Software Engineer with a strong foundation in backend development and data analysis. Passionate about building scalable applications and leveraging machine learning.")

    # --- 3. Education ---
    st.subheader("3. Education")
    col_ed1, col_ed2 = st.columns(2)
    degree = col_ed1.text_input("Degree / Program", value="B.S. in Computer Science")
    school = col_ed2.text_input("University / Institution", value="University of Technology")
    grad_date = st.text_input("Graduation Date (e.g., Expected May 2026)", value="Expected May 2026")

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
    skills = st.text_input("Technical Skills (Comma separated)", value="Python, Java, SQL, React, AWS, Docker, Machine Learning, Git")

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
                def clean_text_pdf(text):
                    text = text.replace("•", "-").replace("⭐", "").replace("✨", "")
                    return text.encode('latin-1', 'replace').decode('latin-1')

                # --- HEADER ---
                full_name = f"{first_name} {last_name}"
                pdf.set_font("Times", "B", 24)
                pdf.cell(0, 10, clean_text_pdf(full_name), ln=True, align="C")
                
                contact_info = []
                if location: contact_info.append(location)
                if phone: contact_info.append(phone)
                if email: contact_info.append(email)
                if linkedin: contact_info.append(linkedin)
                
                pdf.set_font("Times", "", 10)
                pdf.cell(0, 5, clean_text_pdf(" | ".join(contact_info)), ln=True, align="C")
                pdf.ln(4)

                def draw_section_header(title):
                    pdf.set_font("Times", "B", 11)
                    pdf.cell(0, 6, clean_text_pdf(title), ln=True, align="L")
                    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                    pdf.ln(2)

                # --- SUMMARY ---
                if summary:
                    draw_section_header("PROFESSIONAL SUMMARY")
                    pdf.set_font("Times", "", 10)
                    pdf.multi_cell(0, 5, clean_text_pdf(summary))
                    pdf.ln(4)

                # --- EDUCATION ---
                if degree or school:
                    draw_section_header("EDUCATION")
                    pdf.set_font("Times", "B", 10)
                    pdf.cell(0, 5, clean_text_pdf(school), ln=True)
                    pdf.set_font("Times", "", 10)
                    pdf.cell(0, 5, clean_text_pdf(f"{degree} | {grad_date}"), ln=True)
                    pdf.ln(4)

                # --- EXPERIENCE (Dynamic Loop) ---
                draw_section_header("WORK EXPERIENCE")
                for exp in experiences:
                    if exp["title"] or exp["company"]:
                        pdf.set_font("Times", "B", 10)
                        pdf.cell(0, 5, clean_text_pdf(exp["title"]), ln=True)
                        pdf.set_font("Times", "I", 10)
                        pdf.cell(0, 5, clean_text_pdf(f"{exp['company']} | {exp['dates']}"), ln=True)
                        
                        pdf.set_font("Times", "", 10)
                        for line in exp["bullets"].split('\n'):
                            if line.strip():
                                bullet = line.strip() if line.strip().startswith("-") else f"- {line.strip()}"
                                pdf.set_x(15) 
                                pdf.multi_cell(0, 5, clean_text_pdf(bullet))
                        pdf.ln(2)
                pdf.ln(2)

                # --- PROJECTS (Dynamic Loop) ---
                draw_section_header("PROJECTS")
                for proj in projects:
                    if proj["name"]:
                        pdf.set_font("Times", "B", 10)
                        pdf.cell(0, 5, clean_text_pdf(proj["name"]), ln=True)
                        pdf.set_font("Times", "I", 10)
                        pdf.cell(0, 5, clean_text_pdf(f"{proj['role']} | {proj['dates']}"), ln=True)
                        
                        pdf.set_font("Times", "", 10)
                        for line in proj["bullets"].split('\n'):
                            if line.strip():
                                bullet = line.strip() if line.strip().startswith("-") else f"- {line.strip()}"
                                pdf.set_x(15)
                                pdf.multi_cell(0, 5, clean_text_pdf(bullet))
                        pdf.ln(2)
                pdf.ln(2)

                # --- SKILLS ---
                if skills:
                    draw_section_header("TECHNICAL SKILLS")
                    pdf.set_font("Times", "", 10)
                    skills_list = [s.strip() for s in skills.split(',') if s.strip()]
                    pdf.multi_cell(0, 5, clean_text_pdf(", ".join(skills_list)))

                pdf_bytes = pdf.output()

            st.success("✨ Professional PDF Resume Generated Successfully!")
            st.download_button(
                label="📥 Click Here to Download PDF",
                data=bytes(pdf_bytes),
                file_name=f"{first_name}_{last_name}_Resume.pdf",
                mime="application/pdf"
            )

# ==========================================
# PAGE ROUTING FUNCTIONS
# ==========================================

def render_home():
    """Renders the landing dashboard with quick stats."""
    st.title("🏠 Career Command Center")
    st.markdown("<p style='color: #6B7280; font-size: 1.1rem; margin-top: -10px;'>Welcome to your personal workspace. Track your progress, build your resume, and let AI find your next big opportunity.</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Mock Stats for a premium feel
    col1, col2, col3 = st.columns(3)
    col1.metric(label="Active Jobs Scanned", value="1,245", delta="+12 today")
    col2.metric(label="Profile Match Strength", value="85%", delta="High")
    col3.metric(label="Resumes Generated", value="1", delta="Ready")
    
    st.markdown("---")
    st.subheader("🚀 Quick Actions")
    c1, c2 = st.columns(2)
    with c1:
        st.info("💡 **Tip:** Keep your resume updated in the Builder tab to get the most accurate job recommendations.")
    with c2:
        st.success("🎯 **Goal:** Try hitting a 90%+ match score on your next job application by following the AI learning roadmap!")

def render_job_match():
    """Renders the AI Job Matching engine with compact cards and lazy-loaded AI."""
    st.title("🔍 AI Job Match Engine")
    st.markdown("<p style='color: #6B7280; font-size: 1.1rem; margin-top: -10px;'>Upload your latest resume below. Our neural network will instantly analyze your skills and compare them against live job postings.</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

    if uploaded_file:
        loading_placeholder = st.empty()
        with loading_placeholder.container():
            lottie_anim = load_lottieurl("https://assets2.lottiefiles.com/packages/lf20_bhebjzpu.json")
            if lottie_anim:
                st_lottie(lottie_anim, height=250, key="loading_ai")
            st.markdown("<h4 style='text-align: center; color: #0066CC;'>Calculating Semantic Match Scores...</h4>", unsafe_allow_html=True)
            
            # Fast Backend Processing (No Gemini API calls here!)
            raw_resume_text = extract_text_from_pdf(uploaded_file)
            resume_text = clean_text(raw_resume_text)

            conn = sqlite3.connect(DB_NAME)
            df = pd.read_sql_query("SELECT title, company, location, description, link, source FROM jobs", conn)
            conn.close()

            df = df.drop_duplicates(subset="link")

        if df.empty:
            loading_placeholder.empty()
            st.warning("No jobs available in the database. Please fetch jobs first using the sidebar.")
        else:
            job_descriptions = (df["title"] + " " + df["description"]).apply(clean_text).tolist()
            scores = calculate_similarity(resume_text, job_descriptions)

            df["match_score"] = scores
            df = df.sort_values(by="match_score", ascending=False)
            
            loading_placeholder.empty() # Clear loading animation instantly

            st.markdown("---")
            st.subheader("🎯 Top Curated Matches")

            top_jobs = df.head(5)

            def clean_html(text):
                clean = re.compile('<.*?>')
                return re.sub(clean, '', text)

            # --- RENDER COMPACT JOB CARDS ---
            for idx, row in top_jobs.reset_index().iterrows():
                
                # Create a visual boundary card using Streamlit's container
                with st.container(border=True):
                    card_col1, card_col2 = st.columns([3, 1])
                    
                    with card_col1:
                        st.subheader(row["title"])
                        st.markdown(f"**🏢 {row['company']}** &nbsp; | &nbsp; **📍 {row['location']}** &nbsp; | &nbsp; 🌐 {row['source']}")
                    
                    with card_col2:
                        raw_score = row['match_score']
                        safe_score = max(0.0, min(1.0, float(raw_score)))
                        score_percentage = int(safe_score * 100)
                        
                        if score_percentage >= 80: color = "#10B981"
                        elif score_percentage >= 60: color = "#F59E0B"
                        else: color = "#EF4444"
                            
                        fig = go.Figure(go.Indicator(
                            mode = "gauge+number",
                            value = score_percentage,
                            number = {'suffix': "%", 'font': {'color': color, 'size': 32, 'family': "Inter"}},
                            domain = {'x': [0, 1], 'y': [0, 1]},
                            gauge = {
                                'axis': {'range': [None, 100], 'visible': False},
                                'bar': {'color': color, 'thickness': 0.8},
                                'bgcolor': "#F3F4F6",
                                'borderwidth': 0,
                            }
                        ))
                        fig.update_layout(height=120, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)")
                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key=f"gauge_chart_{idx}")

                    # --- COMPACT EXPANDER FOR DETAILS ---
                    with st.expander("📄 View Job Description & AI Insights"):
                        # 1. Clean the text ONLY for the AI to read
                        ai_clean_description = clean_html(row["description"])
                        
                        tab1, tab2, tab3 = st.tabs(["Job Description", "⚠️ AI Skill Gap", "🗺️ AI Roadmap"])
                        
                        with tab1:
                            beautiful_desc = format_raw_job_description(row["description"])
                            st.markdown(beautiful_desc)
                            
                            st.markdown("<br>", unsafe_allow_html=True)
                            
                            # --- COMBINED APPLY & SAVE BUTTONS ---
                            col_btn1, col_btn2 = st.columns([2, 2])
                            with col_btn1:
                                st.markdown(f"<a href='{row['link']}' target='_blank'><button style='background-color: #0066CC; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; width: 100%;'>🔗 Apply on Original Site</button></a>", unsafe_allow_html=True)
                            with col_btn2:
                                # We grab the username from session state just like your friend did
                                current_user = st.session_state.get('username', 'Guest')
                                if st.button("⭐ Save Job to Profile", key=f"save_btn_{idx}", use_container_width=True):
                                    success = save_job_for_user(current_user, row['link'])
                                    if success:
                                        st.toast("Job saved to your dashboard! 📁", icon="✅")
                                    else:
                                        st.toast("You already saved this job!", icon="⚠️")
                        
                        with tab2:
                            st.info("💡 Want to know what you're missing? Ask AI to compare your resume to this specific job.")
                            if st.button("Generate Skill Gap Analysis ✨", key=f"gap_btn_{idx}"):
                                with st.spinner(f"AI is analyzing skill gaps for {row['company']}..."):
                                    prompt = f"You are an expert career coach. Compare the following resume to the specific job description. List ONLY the specific skills, tools, or experience required by the job that are MISSING from the resume. Keep it very brief and use bullet points. If there are no missing skills, say 'Strong match! No major missing skills.'\nJob Description: {ai_clean_description}\nResume: {resume_text}"
                                    st.session_state[f"gap_result_{idx}"] = ask_gemini(prompt)
                            
                            if f"gap_result_{idx}" in st.session_state:
                                st.markdown(f"""
                                <div style='background-color: rgba(254, 242, 242, 0.8); padding: 15px; border-radius: 8px; border-left: 5px solid #EF4444; margin-top: 10px;'>
                                    <h5 style='color: #991B1B; margin-top: 0px;'>⚠️ Missing Skills & Requirements</h5>
                                    <span style='color: #7F1D1D;'>{st.session_state[f"gap_result_{idx}"]}</span>
                                </div>
                                """, unsafe_allow_html=True)

                        with tab3:
                            st.info("💡 Need a plan? Ask AI to build a custom study guide based on your skill gaps.")
                            if st.button("Generate Learning Roadmap ✨", key=f"road_btn_{idx}"):
                                skills_to_learn = st.session_state.get(f"gap_result_{idx}", "the skills required for this job that I am currently missing.")
                                with st.spinner(f"AI is building a learning roadmap..."):
                                    roadmap_prompt = f"You are a senior technical mentor. A candidate is missing the following skills for a job: {skills_to_learn}. Create a very brief, step-by-step learning roadmap. Tell the candidate the logical order they should learn these missing skills. Keep it concise, actionable, and use a numbered list."
                                    st.session_state[f"road_result_{idx}"] = ask_gemini(roadmap_prompt)
                            
                            if f"road_result_{idx}" in st.session_state:
                                st.markdown(f"""
                                <div style='background-color: rgba(240, 253, 244, 0.8); padding: 15px; border-radius: 8px; border-left: 5px solid #10B981; margin-top: 10px;'>
                                    <h5 style='color: #065F46; margin-top: 0px;'>🗺️ Recommended Learning Roadmap</h5>
                                    <span style='color: #064E3B;'>{st.session_state[f"road_result_{idx}"]}</span>
                                </div>
                                """, unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True) 
    else:
        st.info("👆 Upload your resume to initiate the matching process.")

# ==========================================
# MAIN DASHBOARD CONTROLLER
# ==========================================
def main():
    apply_dashboard_css()
    init_db()

    # --- 1. USER SIDEBAR & NAVIGATION ---
    current_user = st.session_state.get('username', 'Guest')
    
    st.sidebar.title(f"Welcome, {st.session_state.get('first_name', current_user)}!")
    st.sidebar.divider()
    
    page = st.sidebar.radio("Workspace Navigation", ["🏠 Dashboard Home", "🔍 AI Job Match", "📝 Resume Builder"])
    
    st.sidebar.divider()
    st.sidebar.header("Data Controls")
    if st.sidebar.button("🔄 Fetch Latest Jobs", use_container_width=True):
        with st.spinner("Fetching jobs from APIs and RSS feeds..."):
            new_jobs = fetch_rss_jobs()
            st.sidebar.success(f"{new_jobs} jobs added!")
            
    # --- SAVED JOBS DASHBOARD (Sidebar) ---
    with st.sidebar.expander("📁 View My Saved Jobs", expanded=False):
        saved_jobs = get_saved_jobs(current_user)
        
        if not saved_jobs:
            st.info("You haven't saved any jobs yet. Start exploring!")
        else:
            for i, job in enumerate(saved_jobs):
                title, company, link = job
                st.markdown(f"**{title}**\n*{company}*")
                
                # Side-by-side View and Unsave buttons
                col_sb1, col_sb2 = st.columns(2)
                with col_sb1:
                    st.link_button("View", link, use_container_width=True)
                with col_sb2:
                    if st.button("❌ Unsave", key=f"unsave_sidebar_{i}", use_container_width=True):
                        remove_saved_job(current_user, link)
                        st.rerun() # Instantly refreshes the UI
                st.divider()

    st.sidebar.divider()
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state['logged_in'] = False
        st.rerun()

    # --- 2. RENDER THE SELECTED PAGE ---
    if page == "🏠 Dashboard Home":
        render_home()
    elif page == "🔍 AI Job Match":
        render_job_match()
    elif page == "📝 Resume Builder":
        render_resume_builder()