import streamlit as st
from dotenv import load_dotenv
from auth import login, logout
from database import init_db, get_notifications

# Page config for wide layout and visible sidebar
st.set_page_config(
    page_title="Big Boss Chat",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for padding, slick menus, and animations
st.markdown("""
<style>
    /* General padding and font */
    .main .block-container {
        padding: 2.5rem !important;
        max-width: 1200px !important;
        border-radius: 10px;
        background: #ffffff;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    body {
        font-family: 'Segoe UI', Tahoma, sans-serif;
        transition: all 0.3s ease;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f0f2f6, #e0e4eb);
        padding: 1.5rem !important;
        border-right: 3px solid #ccc;
        min-width: 250px !important;
    }
    [data-testid="stSidebar"] .stRadio > div {
        background: #ffffff;
        border-radius: 10px;
        padding: 0.8rem;
        margin: 0.3rem 0;
        box-shadow: 0 3px 6px rgba(0,0,0,0.15);
        transition: transform 0.2s ease;
    }
    [data-testid="stSidebar"] .stRadio > div:hover {
        transform: scale(1.05);
        background: #007bff;
        color: white;
    }

    /* Dark mode */
    .dark [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2c2c2c, #3a3a3a);
        border-right: 3px solid #555;
    }
    .dark .main .block-container {
        background: #1e1e1e;
        color: #ffffff;
    }
    .dark [data-testid="stSidebar"] .stRadio > div {
        background: #444;
        color: #ffffff;
    }
    .dark [data-testid="stSidebar"] .stRadio > div:hover {
        background: #0056b3;
    }

    /* Welcome banner */
    .welcome-banner {
        background: linear-gradient(90deg, #007bff, #00d4ff);
        color: white;
        padding: 2rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 6px 12px rgba(0,0,0,0.2);
        animation: slideIn 0.7s ease;
    }

    /* Animations */
    @keyframes slideIn {
        from { transform: translateY(-30px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }

    /* Chat message styling */
    .stChatMessage {
        border-radius: 12px !important;
        padding: 1.2rem !important;
        margin-bottom: 1.2rem !important;
        background: #f9f9f9;
        box-shadow: 0 3px 6px rgba(0,0,0,0.1);
        transition: all 0.2s ease;
    }
    .dark .stChatMessage {
        background: #333;
        color: #fff;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }

    /* Hide Streamlit defaults */
    #MainMenu, footer, .stDeployButton { display: none !important; }
</style>
""", unsafe_allow_html=True)

# JavaScript for dark mode toggle
st.markdown("""
<script>
    function applyTheme(theme) {
        if (theme === 'dark') {
            document.body.classList.add('dark');
        } else {
            document.body.classList.remove('dark');
        }
    }
    // Apply theme from session state
    applyTheme('%s');
</script>
""" % st.session_state.get('theme', 'light'), unsafe_allow_html=True)

load_dotenv()
init_db()

# Initialize session state
if "theme" not in st.session_state:
    st.session_state.theme = "light"
if "display_name" not in st.session_state:
    st.session_state.display_name = None
if "avatar" not in st.session_state:
    st.session_state.avatar = None

# Login check
if "username" not in st.session_state:
    login()
    st.stop()

# Welcome banner with avatar
username = st.session_state.username
display_name = st.session_state.display_name or username
avatar = st.session_state.avatar or "👤"
st.markdown(f"""
<div class="welcome-banner">
    <h2>{avatar} Welcome, {display_name}! 🚀</h2>
    <p>Ready to dominate the chat? You've got {len(get_notifications(username))} unread messages!</p>
</div>
""", unsafe_allow_html=True)

# Sidebar with slick menu
with st.sidebar:
    st.title("Big Boss Chat 🌟")
    st.markdown(f"**{avatar} {display_name}**")
    
    # Navigation with notification badge
    notifications = len(get_notifications(username))
    choice = st.radio(
        "Navigate",
        [
            "Home",
            f"Chat {'🔔' + str(notifications) if notifications > 0 else ''}",
            "Groups",
            "Profile"
        ],
        key="nav_radio"
    )
    
    # Theme toggle and logout
    st.markdown("---")
    theme = st.selectbox("Theme", ["Light", "Dark"], index=0 if st.session_state.theme == "light" else 1, key="theme_select")
    if theme.lower() != st.session_state.theme:
        st.session_state.theme = theme.lower()
        st.rerun()
    
    if st.button("Logout", key="logout_btn"):
        logout()
        st.rerun()

# Route to pages
choice = choice.split(" ")[0]  # Remove notification badge
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