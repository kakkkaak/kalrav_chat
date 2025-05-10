import streamlit as st
from dotenv import load_dotenv
from auth import login
from database import init_db

# Must come first
st.set_page_config(
    page_title="Big Boss Chat", 
    layout="wide",
    initial_sidebar_state="collapsed"  # Start with sidebar collapsed
)

# Even more aggressive sidebar hiding
st.markdown("""
<style>
    /* Hide the default sidebar completely */
    .css-1d391kg, .css-12aokuf, .css-15tx938 {display: none;}
    
    /* Hide the top file navigation sidebar */
    [data-testid="collapsedControl"] {display: none !important;}
    
    /* Hide hamburger menu */
    #MainMenu {visibility: hidden;}
    
    /* Hide footer */
    footer {visibility: hidden;}
    
    /* Hide "Deploy", "Manage app", "Rerun" buttons at the end of output */
    .stDeployButton {display:none;}
    
    /* Adjust padding */
    .main .block-container {padding-top: 1rem;}
    
    /* Additional class to target sidebar */
    header[data-testid="stHeader"] {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

load_dotenv()
init_db()

# Create our own custom sidebar container
if "username" not in st.session_state:
    login()
    st.stop()

# After login: show our custom navigation
with st.sidebar:
    st.title("Big Boss Chat")
    choice = st.radio("Navigation", ["Home", "Chat", "Groups", "Profile"])

# Route to the appropriate page
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