import streamlit as st
from database import create_user, get_user, check_password

def login():
    st.title("Login to Big Boss Chat")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            user = get_user(username)
            if user and check_password(user["password_hash"], password):
                st.session_state.username = username
                st.session_state.display_name = user["profile"].get("display_name", username)
                st.success("Logged in!")
                st.rerun()
            else:
                st.error("Invalid username or password")

def signup():
    st.title("Sign Up")
    with st.form("signup_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        display_name = st.text_input("Display Name (optional)")
        submitted = st.form_submit_button("Sign Up")
        if submitted:
            if get_user(username):
                st.error("Username already exists")
            else:
                profile = {"name": username, "bio": "", "pic": None, "show_bio": False, "show_pic": False}
                if display_name:
                    profile["display_name"] = display_name
                create_user(username, password, profile)
                st.success("Account created! Please log in.")
                st.session_state.username = username
                st.session_state.display_name = display_name or username
                st.rerun()

def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]