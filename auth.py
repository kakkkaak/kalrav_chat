# auth.py
import streamlit as st
from database import init_db, create_user, get_user, check_password
import os

def login():
    init_db()
    if "auth_mode" not in st.session_state: st.session_state.auth_mode="login"
    if st.session_state.auth_mode=="login": show_login()
    else: show_signup()

def show_login():
    st.subheader("🔐 Login")
    u = st.text_input("Username",key="login_u")
    p = st.text_input("Password",type="password",key="login_p")
    if st.button("Login"):
        user = get_user(u)
        if user and check_password(user["password_hash"],p):
            st.session_state.username=u
            st.session_state.is_admin=user.get("is_admin",False)
        else: st.error("Invalid credentials")
    if st.button("Go to Sign Up"):
        st.session_state.auth_mode="signup"

def show_signup():
    st.subheader("🆕 Sign Up")
    u=st.text_input("Username",key="su_u")
    p=st.text_input("Password",type="password",key="su_p")
    n=st.text_input("Display Name",key="su_n")
    if st.button("Register"):
        if get_user(u): st.error("Username taken")
        else:
            is_admin = (u==os.getenv("ADMIN_USERNAME") and p==os.getenv("ADMIN_PASSWORD"))
            create_user(u,p,n,is_admin=is_admin)
            st.success("Registered! Please log in.")
            st.session_state.auth_mode="login"
    if st.button("Go to Login"):
        st.session_state.auth_mode="login"
