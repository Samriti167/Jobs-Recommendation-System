import streamlit as st
import database as db
import time
import re

# 1. Page Configuration 
st.set_page_config(page_title="INTELLIGENT RESUME SCREENING AND REAL TIME JOB RECOMMENDATION SYSTEM", page_icon="💼", layout="wide")

# 2. Premium CSS Overhaul: Typography, Fluid Animations & Dot Grid Background
def local_css():
    st.markdown("""
    <style>
        /* IMPORT PREMIUM GOOGLE FONT */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        /* Apply the font globally */
        html, body, [class*="css"], span, div, p, h1, h2, h3, h4, h5, h6, label, input, select, button {
            font-family: 'Inter', sans-serif !important;
        }

        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* --- THE NEW PROFESSIONAL DOT GRID BACKGROUND --- */
        .stApp { 
            background-color: #F9FAFB !important; 
            background-image: radial-gradient(#D1D5DB 1px, transparent 1px) !important;
            background-size: 24px 24px !important; /* Spacing of the dots */
        }

        /* The Main Form Container */
        div[data-testid="stForm"] {
            background-color: #FFFFFF !important;
            border: 1px solid #D1D5DB !important;
            border-radius: 0px !important; 
            padding: 2.5rem !important;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.03) !important; /* Extremely soft shadow to lift form off the grid */
        }

        /* --- FLUID INPUT ANIMATIONS --- */
        div[data-testid="stTextInput"] div[data-baseweb="input"], 
        div[data-testid="stSelectbox"] div[data-baseweb="select"] {
            background-color: #F3F4F6 !important; 
            border: 1px solid #9CA3AF !important; 
            border-radius: 0px !important; 
            transition: all 0.3s ease-in-out !important; 
        }

        div[data-testid="stTextInput"] input, 
        div[data-testid="stSelectbox"] select {
            color: #111827 !important;
            background-color: transparent !important; 
        }

        /* Active State: Smoothly lightens background and adds a glowing ring */
        div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within,
        div[data-testid="stSelectbox"] div[data-baseweb="select"]:focus-within {
            border: 1px solid #0066CC !important;
            box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.15) !important; 
            background-color: #FFFFFF !important; 
        }

        /* --- FLUID BUTTON ANIMATIONS --- */
        div[data-testid="stFormSubmitButton"] > button,
        div[data-testid="stButton"] > button {
            border-radius: 0px !important; 
            font-weight: 600 !important;
            letter-spacing: 0.5px !important; 
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important; 
        }
        
        /* Primary Form Submit Buttons */
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #0066CC !important; 
            color: #FFFFFF !important; 
            border: none !important;
            padding: 0.6rem 1.2rem !important;
        }
        
        div[data-testid="stFormSubmitButton"] > button:hover {
            background-color: #0052A3 !important; 
            transform: translateY(-2px) !important; 
            box-shadow: 0 6px 15px rgba(0, 102, 204, 0.25) !important; 
        }

        div[data-testid="stFormSubmitButton"] > button:active {
            transform: translateY(0px) !important; 
            box-shadow: 0 2px 5px rgba(0, 102, 204, 0.25) !important;
        }
        
        /* Secondary Social Buttons */
        div[data-testid="stButton"] > button {
            background-color: #FFFFFF !important;
            color: #374151 !important;
            border: 1px solid #D1D5DB !important;
            width: 100% !important;
        }
        
        div[data-testid="stButton"] > button:hover {
            border-color: #9CA3AF !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05) !important;
        }
    </style>
    """, unsafe_allow_html=True)

def is_valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email) is not None

def main():
    local_css()
    db.create_usertable()
    
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if not st.session_state['logged_in']:
        
        left_col, right_col = st.columns([1.2, 1], gap="large")
        
        with left_col:
            st.header("💼 Intelligent Resume Screening & Real-Time Job Recommendation System")
            st.write("Welcome to your personal workspace. Let AI enhance your resume, find your skill gaps, and match you with your next big opportunity.")
    
            st.markdown("#### Platform Features")
            st.markdown("📝 **ATS Resume Builder:** Generate professional, ATS-compliant PDFs and use AI to instantly rewrite your experience bullets.")
            st.markdown("🔍 **Semantic Job Matching:** Upload your resume and let our neural network calculate real-time match scores against live job postings.")
            st.markdown("🧠 **AI Career Insights:** Instantly identify missing skills for specific roles and generate custom step-by-step learning roadmaps.")
            st.markdown("📁 **Track Your Progress:** Save top matches to your profile and monitor your live job feed.")
    
            st.write("<br><br><br>", unsafe_allow_html=True)

        with right_col:
            menu = ["Login", "Sign Up"]
            choice = st.radio("Access Portal", menu, horizontal=True)

            if choice == "Login":
                st.subheader("Welcome Back")
                
                
                st.markdown("<div style='text-align: center; color: #6B7280; margin: 15px 0; font-size: 0.85rem; font-weight: 600;'>OR LOGIN WITH EMAIL</div>", unsafe_allow_html=True)

                with st.form("login_form"):
                    email = st.text_input("Email Address")
                    password = st.text_input("Password", type='password')
                    submit_button = st.form_submit_button("Login to Dashboard", use_container_width=True)
                    
                    if submit_button:
                        if not is_valid_email(email):
                            st.error("Please enter a valid email format.")
                        elif email and password:
                            hashed_pswd = db.make_hashes(password)
                            result = db.login_user(email, hashed_pswd)
                            if result:
                                st.session_state['logged_in'] = True
                                st.session_state['first_name'] = result[0][0] 
                                st.rerun() 
                            else:
                                st.error("Incorrect Email or Password.")
                        else:
                            st.warning("Please fill out both fields.")

            elif choice == "Sign Up":
                st.subheader("Create a New Account")
                
                st.button("Sign up with Google 🌐")
                st.button("Sign up with LinkedIn 💼")
                st.markdown("<div style='text-align: center; color: #6B7280; margin: 15px 0; font-size: 0.85rem; font-weight: 600;'>OR REGISTER WITH EMAIL</div>", unsafe_allow_html=True)

                with st.form("signup_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_first = st.text_input("First Name*")
                    with col2:
                        new_last = st.text_input("Last Name*")
                        
                    new_email = st.text_input("Email Address*")
                    new_phone = st.text_input("Phone Number")
                    status = st.selectbox("Professional Status", ["Student", "Fresher", "Experienced"])
                    
                    new_password = st.text_input("Password (Min. 8 characters)*", type='password')
                    confirm_password = st.text_input("Confirm Password*", type='password')
                    st.caption("By registering, you agree to our Terms of Service.")
                    
                    submit_button = st.form_submit_button("Create Account", use_container_width=True)

                    if submit_button:
                        if not is_valid_email(new_email):
                            st.error("Please enter a valid email address.")
                        elif len(new_password) < 8:
                            st.error("Password must be at least 8 characters long.")
                        elif new_password != confirm_password:
                            st.error("Passwords do not match!")
                        elif not new_first or not new_last:
                            st.warning("Please provide your full name.")
                        else:
                            hashed_new_password = db.make_hashes(new_password)
                            success = db.add_userdata(new_first, new_last, new_email, hashed_new_password, new_phone, status)
                            if success:
                                st.success("Account created! Switch to Login to access your dashboard.")
                                st.balloons()
                            else:
                                st.error("An account with this email already exists.")

    else:
        # --- MAIN DASHBOARD ---
        st.sidebar.title(f"Welcome, {st.session_state['first_name']}!")
        st.sidebar.divider()
        if st.sidebar.button("Logout", use_container_width=True):
            st.session_state['logged_in'] = False
            st.rerun()

        st.title("📄 Resume Analysis Dashboard")
        st.write("Upload your resume below to initiate the ML screening process.")
        uploaded_file = st.file_uploader("Upload PDF or DOCX", type=["pdf", "docx"])
