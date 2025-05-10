import streamlit as st
from dotenv import load_dotenv
from auth import login
from database import init_db
import logging

# Set up Streamlit page configuration
st.set_page_config(
    page_title="Big Boss Chat", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide default Streamlit elements
st.markdown("""
<style>
    .css-1d391kg, .css-12aokuf, .css-15tx938 {display: none;}
    [data-testid="collapsedControl"] {display: none !important;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    .main .block-container {padding-top: 1rem;}
    header[data-testid="stHeader"] {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Load environment variables and initialize database
load_dotenv()
init_db()

# Set up logging
logging.basicConfig(filename='app.log', level=logging.ERROR)

# Handle login
if "username" not in st.session_state:
    login()
    st.stop()

# Custom sidebar with navigation and logout
with st.sidebar:
    st.title("Big Boss Chat")
    choice = st.radio("Navigation", ["Home", "Chat", "Groups", "Profile"])
    if st.button("Logout", key="logout_button"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# Route to selected page
if choice == "Home":
    from views.home import show_home
    show_home()
elif choice == "Chat":
    from views.chat import show_chat
    show_chat()
elif choice == "Groups":
    from views.groups import show_groups
    show_groups()
elif choice == "Profile":
    from views.profile import show_profile
    show_profile()