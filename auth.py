import streamlit as st
from database import create_user, get_user, check_password

def login():
    st.title("Login to Big Boss Chat")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            try:
                user = get_user(username)
                if user and check_password(user["password_hash"], password):
                    st.session_state.username = username
                    st.session_state.display_name = user["profile"].get("display_name", username)
                    st.session_state.avatar = user["profile"].get("avatar", "👤")
                    st.session_state.theme = user.get("settings", {}).get("theme", "light")
                    st.session_state.background_color = user.get("settings", {}).get("background_color", "#f0f0f0")
                    st.success("Logged in!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            except Exception as e:
                st.error(f"Error during login: {e}")

def signup():
    st.title("Sign Up")
    with st.form("signup_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        display_name = st.text_input("Display Name (optional)")
        avatar = st.selectbox("Avatar", ["👤", "😎", "🚀", "🐱", "🦁"], index=0)
        submitted = st.form_submit_button("Sign Up")
        if submitted:
            try:
                if get_user(username):
                    st.error("Username already exists")
                else:
                    profile = {
                        "name": username,
                        "bio": "",
                        "pic": None,
                        "show_bio": False,
                        "show_pic": False,
                        "display_name": display_name or username,
                        "avatar": avatar
                    }
                    create_user(username, password, profile)
                    st.session_state.username = username
                    st.session_state.display_name = display_name or username
                    st.session_state.avatar = avatar
                    st.session_state.theme = "light"
                    st.session_state.background_color = "#f0f0f0"
                    st.success("Account created! Please log in.")
                    st.rerun()
            except Exception as e:
                st.error(f"Error during signup: {e}")

def logout():
    # Selectively clear auth-related keys
    keys_to_clear = ["username", "display_name", "avatar"]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]