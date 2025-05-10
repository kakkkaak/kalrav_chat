import streamlit as st
from database import init_db, create_user, get_user, check_password
import os

def login():
    init_db()
    st.title("🔐 Login / Sign Up")
    mode = st.radio("Mode", ["Login","Sign Up"])
    if mode=="Login":
        u = st.text_input("Username", key="li_u")
        p = st.text_input("Password", type="password", key="li_p")
        if st.button("Login"):
            user = get_user(u)
            if user and check_password(user["password_hash"], p):
                st.session_state.username = u
                st.session_state.is_admin = user.get("is_admin", False)
            else:
                st.error("Invalid credentials")
    else:
        u = st.text_input("Username", key="su_u")
        p = st.text_input("Password", type="password", key="su_p")
        n = st.text_input("Display Name", key="su_n")
        if st.button("Sign Up"):
            if get_user(u):
                st.error("Username taken")
            else:
                is_admin = (u==os.getenv("ADMIN_USERNAME") and p==os.getenv("ADMIN_PASSWORD"))
                create_user(u, p, n, is_admin)
                st.success("Account created! Please log in.")
