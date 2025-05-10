import streamlit as st
from dotenv import load_dotenv
from auth import login
from database import init_db

# Must come first
st.set_page_config(page_title="Big Boss Chat", layout="wide")

# Hide the default Streamlit sidebar and navigation
st.markdown("""
<style>
    /* Hide the default sidebar */
    section[data-testid="stSidebar"] > div:nth-child(2) {
        display: none;
    }
    
    /* Hide the top file navigation sidebar */
    [data-testid="collapsedControl"] {
        display: none;
    }
    
    /* Remove hamburger menu and footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Adjust padding */
    .main .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

load_dotenv()
init_db()

if "username" not in st.session_state:
    # Hide sidebar until login
    st.sidebar.empty()
    login()
    st.stop()

# After login: show exactly four items
choice = st.sidebar.radio("Navigation", ["Home", "Chat", "Groups", "Profile"])

if choice == "Home":
    from pages.home import show_home
    show_home()
elif choice == "Chat":
    from pages.chat import show_chat
    show_chat()
elif choice == "Groups":
    from pages.groups import show_groups
    show_groups()
elif choice == "Profile":
    from pages.profile import show_profile
    show_profile()