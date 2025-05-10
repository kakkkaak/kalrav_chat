import streamlit as st, io
from database import get_user, update_user_profile, store_file

def show_profile():
    u = st.session_state.username
    user = get_user(u)
    st.title("Profile")
    name = st.text_input("Display Name", user["name"])
    pwd  = st.text_input("New Password", "", type="password")
    bio  = st.text_area("Bio", user["profile"]["bio"])
    sb   = st.checkbox("Show Bio", user["profile"]["show_bio"])
    pic  = st.file_uploader("Profile Picture", type=["png","jpg","jpeg"])
    sp   = st.checkbox("Show Pic", user["profile"]["show_pic"])

    if st.button("Save"):
        pid = user["profile"]["pic"]
        if pic:
            pid = store_file(io.BytesIO(pic.getvalue()), pic.name)
        update_user_profile(u, name, pwd, {
            "bio": bio,
            "pic": pid,
            "show_bio": sb,
            "show_pic": sp
        })
        st.success("Profile updated.")
