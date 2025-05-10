import streamlit as st
from dotenv import load_dotenv
from auth import login, logout
from database import init_db, get_notifications

# Page config
st.set_page_config(
    page_title="Big Boss Chat",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for padding, animations, and slick look
st.markdown("""
<style>
    /* General padding and font */
    .main .block-container {
        padding: 2rem;
        max-width: 1200px;
    }
    body {
        font-family: 'Segoe UI', sans-serif;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #f0f2f6;
        padding: 1rem;
        border-right: 2px solid #ddd;
        transition: all 0.3s ease;
    }
    [data-testid="stSidebar"] .stRadio > div {
        background-color: #fff;
        border-radius: 8px;
        padding: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    [data-testid="stSidebar"] .stRadio > div:hover {
        transform: scale(1.02);
        transition: transform 0.2s;
    }

    /* Dark mode */
    .dark [data-testid="stSidebar"] {
        background-color: #2c2c2c;
        border-right: 2px solid #444;
    }
    .dark .main {
        background-color: #1e1e1e;
        color: #fff;
    }
    .dark [data-testid="stSidebar"] .stRadio > div {
        background-color: #444;
        color: #fff;
    }

    /* Welcome banner */
    .welcome-banner {
        background: linear-gradient(90deg, #007bff, #00d4ff);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        animation: slideIn 0.5s ease;
    }

    /* Animations */
    @keyframes slideIn {
        from { transform: translateY(-20px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }

    /* Chat message styling */
    .stChatMessage {
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    /* Hide Streamlit defaults */
    #MainMenu, footer, .stDeployButton { display: none; }
</style>
""", unsafe_allow_html=True)

load_dotenv()
init_db()

# Initialize session state
if "theme" not in st.session_state:
    st.session_state.theme = "light"
if "display_name" not in st.session_state:
    st.session_state.display_name = None

# Apply theme
if st.session_state.theme == "dark":
    st.markdown('<script>document.body.classList.add("dark");</script>', unsafe_allow_html=True)

# Login check
if "username" not in st.session_state:
    login()
    st.stop()

# Welcome banner
username = st.session_state.username
display_name = st.session_state.display_name or username
st.markdown(f"""
<div class="welcome-banner">
    <h2>Welcome, {display_name}! 🚀</h2>
    <p>Ready to chat like a boss? You've got {len(get_notifications(username))} unread notifications!</p>
</div>
""", unsafe_allow_html=True)

# Sidebar with slick menu
with st.sidebar:
    st.title("Big Boss Chat")
    st.markdown(f"**Logged in as:** {display_name}")
    
    # Navigation with notification badge
    notifications = len(get_notifications(username))
    choice = st.radio(
        "Navigate",
        [
            "Home",
            f"Chat {'🔔' + str(notifications) if notifications > 0 else ''}",
            "Groups",
            "Profile"
        ]
    )
    
    # Theme toggle and logout
    st.markdown("---")
    theme = st.selectbox("Theme", ["Light", "Dark"], index=0 if st.session_state.theme == "light" else 1)
    if theme.lower() != st.session_state.theme:
        st.session_state.theme = theme.lower()
        st.rerun()
    
    if st.button("Logout"):
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