import streamlit as st, io
from database import get_user, update_profile, store_file, update_password

def show_profile():
    u = st.session_state.username
    user = get_user(u)
    st.title("Profile Settings")

    prof = user["profile"]
    name = st.text_input("Display Name", prof.get("name", u), key="profile_name")
    pwd = st.text_input("New Password", "", type="password", key="profile_password")
    bio = st.text_area("Bio", prof.get("bio", ""), key="profile_bio")
    sb = st.checkbox("Show Bio", prof.get("show_bio", False), key="profile_show_bio")
    pic = st.file_uploader("Profile Picture", type=["png","jpg","jpeg"], key="profile_pic")
    if pic:
        st.image(pic, width=150)
    sp = st.checkbox("Show Picture", prof.get("show_pic", False), key="profile_show_pic")

    theme = st.selectbox("Theme", ["Light", "Dark"], key="theme_select")
    if theme == "Dark":
        st.markdown("<style>body {background-color: #333; color: #fff;}</style>", unsafe_allow_html=True)
    else:
        st.markdown("<style>body {background-color: #fff; color: #000;}</style>", unsafe_allow_html=True)

    if st.button("Save", key="profile_save"):
        pid = prof.get("pic")
        if pic:
            pid = store_file(io.BytesIO(pic.getvalue()), pic.name)
        new_prof = {"name": name, "bio": bio, "pic": pid, "show_bio": sb, "show_pic": sp}
        update_profile(u, new_prof, list(new_prof.keys()))
        if pwd:
            if len(pwd) < 6:
                st.error("Password must be at least 6 characters")
            else:
                update_password(u, pwd)
                st.success("Password updated")
        st.success("Profile updated")