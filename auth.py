import os
import streamlit as st
from database import create_user, get_user, check_password

def login():
    st.title("🔐 Login / Sign Up")
    mode = st.radio("Mode", ["Login", "Sign Up"], key="auth_mode")
    if mode == "Login":
        u = st.text_input("Username", key="li_u")
        p = st.text_input("Password", type="password", key="li_p")
        if st.button("Login", key="login_button"):
            if not u or not p:
                st.error("Please enter both username and password")
                return
                
            user = get_user(u)
            if user and check_password(user["password_hash"], p):
                # Set session variables
                st.session_state.username = u
                st.session_state.is_admin = user.get("is_admin", False)
                
                # Initialize chat session state variables
                st.session_state.chat_mode = "private"
                st.session_state.chat_partner = None
                st.session_state.chat_group = None
                
                st.rerun()
            else:
                st.error("Invalid credentials")
    else:
        u = st.text_input("Choose Username", key="su_u")
        p = st.text_input("Choose Password", type="password", key="su_p")
        n = st.text_input("Display Name", key="su_n")
        if st.button("Sign Up", key="signup_button"):
            if not u or not p:
                st.error("Username and password are required")
            elif get_user(u):
                st.error("Username already taken")
            else:
                is_admin = (u == os.getenv("ADMIN_USERNAME") and p == os.getenv("ADMIN_PASSWORD"))
                create_user(u, p, {"name": n or u, "bio": "", "pic": None, "show_bio": False, "show_pic": False})
                st.success("Account created! Please log in.")