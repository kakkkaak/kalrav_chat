import streamlit as st
from dotenv import load_dotenv
from database import init_db
from auth import login

# 1) Global page config (must come first)
st.set_page_config(page_title="Big Boss Chat", layout="wide")

# 2) Load .env and initialize DB
load_dotenv()
init_db()

# 3) If not logged in, show login only (no sidebar)
if "username" not in st.session_state:
    login()
    st.stop()

# 4) After login: define the sidebar menu once
choice = st.sidebar.radio(
    "Navigation",
    ["Home", "Chat", "Groups", "Profile"]
)

# 5) Route to the chosen page
if choice == "Home":
    from pages.home import show_home
    show_home()

elif choice == "Chat":
    # Chat will use st.sidebar buttons only to select partner/room,
    # but those are subordinate to this main nav
    from pages.chat import show_chat
    show_chat()

elif choice == "Groups":
    from pages.groups import show_groups
    show_groups()

elif choice == "Profile":
    from pages.profile import show_profile
    show_profile()
