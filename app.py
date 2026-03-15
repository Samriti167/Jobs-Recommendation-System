import streamlit as st
import auth_ui
import dashboard_ui

# The Page Config must be the very first thing in the main file
st.set_page_config(page_title="Job Matcher Pro", page_icon="💼", layout="wide")

def main():
    # 1. Setup the session state (Memory)
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    # 2. The Traffic Cop Logic
    if not st.session_state['logged_in']:
        # User is NOT logged in. Show them YOUR login page.
        auth_ui.main() 
    else:
        # User IS logged in. Show them HER AI dashboard.
        dashboard_ui.main()

if __name__ == '__main__':
    main()