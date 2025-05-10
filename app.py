import streamlit as st
from dotenv import load_dotenv
from database import init_db
from auth import login

# 1) Page config must be first
st.set_page_config(page_title="Big Boss Chat", layout="wide")

# 2) Load env and init DB
load_dotenv()
init_db()

# 3) If not logged in, show only login (no sidebar)
if "username" not in st.session_state:
    st.sidebar.empty()      # remove any sidebar contents
    login()
    st.stop()

# 4) After login, show exactly four nav items
choice = st.sidebar.radio("Navigation", ["Home", "Chat", "Groups", "Profile"])

if choice == "Home":
    from pages.home    import show_home
    show_home()
elif choice == "Chat":
    from pages.chat    import show_chat
    show_chat()
elif choice == "Groups":
    from pages.groups  import show_groups
    show_groups()
elif choice == "Profile":
    from pages.profile import show_profile
    show_profile()
