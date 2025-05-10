import streamlit as st
import time
from dotenv import load_dotenv
from auth import login
from database import init_db, get_notifications, mark_notifications_read

# Must come first
st.set_page_config(
    page_title="Big Boss Chat",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom styles for cleaner UI
st.markdown("""
<style>
    .css-1d391kg, .css-12aokuf, .css-15tx938 {display: none !important;}
    [data-testid="collapsedControl"] {display: none !important;}
    #MainMenu, footer, .stDeployButton {visibility: hidden;}
    .main .block-container {padding-top: 1rem;}
    header[data-testid="stHeader"] {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

load_dotenv()
init_db()

# Function to keep notifications live without refreshing
def fetch_notifications():
    username = st.session_state.get("username", None)
    if not username:
        return []
    return get_notifications(username)

def show_notifications():
    if "notifications" not in st.session_state:
        st.session_state["notifications"] = []

    while True:
        st.session_state["notifications"] = fetch_notifications()
        time.sleep(5)  # Poll every 5 seconds

# Ensure login persists without session reset
if "username" not in st.session_state or not st.session_state["username"]:
    login()
    st.stop()

# Keep notifications running
show_notifications()

# Custom Sidebar Navigation
with st.sidebar:
    st.title("Big Boss Chat")

    choice = st.radio("Navigation", ["Home", "Chat", "Groups", "Profile"])

    # Show notifications dynamically
    nots = st.session_state.get("notifications", [])
    st.markdown(f"<p style='font-size:18px;'><b>🔔 {len(nots)} Notifications</b></p>", unsafe_allow_html=True)

    if nots:
        with st.expander("📩 View Notifications"):
            for n in nots:
                st.write(f"**{n['msg']['sender']}**: {n['msg']['msg']['content']}")
            mark_notifications_read(st.session_state["username"])

# Route to pages
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
