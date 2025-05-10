import streamlit as st, io
from database import get_user, update_profile, store_file

def show_profile():
    u = st.session_state.username
    user = get_user(u)
    st.title("Profile Settings")
    prof = user["profile"]
    name = st.text_input("Display Name", prof.get("name", u))
    pwd  = st.text_input("New Password", "", type="password")
    bio  = st.text_area("Bio", prof.get("bio",""))
    sb   = st.checkbox("Show Bio", prof.get("show_bio", False))
    pic  = st.file_uploader("Profile Picture", type=["png","jpg","jpeg"])
    sp   = st.checkbox("Show Picture", prof.get("show_pic", False))
    if st.button("Save"):
        pid = prof.get("pic")
        if pic:
            pid = store_file(io.BytesIO(pic.getvalue()), pic.name)
        new_prof = {"name": name, "bio": bio, "pic": pid, "show_bio": sb, "show_pic": sp}
        update_profile(u, new_prof, [k for k,v in new_prof.items() if v])
        st.success("Profile updated")
