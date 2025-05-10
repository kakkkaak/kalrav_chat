import streamlit as st
from dotenv import load_dotenv
from auth import login
from database import init_db

# Must come first
st.set_page_config(
    page_title="Big Boss Chat", 
    layout="wide",
    initial_sidebar_state="expanded"  # Start with sidebar visible
)

# Adjusted CSS to hide Streamlit's default elements but keep custom sidebar
st.markdown("""
<style>
    /* Hide hamburger menu */
    #MainMenu {visibility: hidden;}
    
    /* Hide footer */
    footer {visibility: hidden;}
    
    /* Hide "Deploy", "Manage app", "Rerun" buttons */
    .stDeployButton {display: none;}
    
    /* Adjust padding for main content */
    .main .block-container {padding-top: 1rem;}
    
    /* Ensure custom sidebar is visible */
    [data-testid="stSidebar"] {display: block !important;}
</style>
""", unsafe_allow_html=True)

load_dotenv()
init_db()

# Custom sidebar navigation
if "username" not in st.session_state:
    login()
    st.stop()

# Show custom sidebar after login
with st.sidebar:
    st.title("Big Boss Chat")
    choice = st.radio("Navigation", ["Home", "Chat", "Groups", "Profile"])

# Route to the appropriate page
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