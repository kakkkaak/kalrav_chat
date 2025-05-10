import streamlit as st, io
from database import get_user, update_profile, store_file

def show_profile():
    u = st.session_state.username
    user = get_user(u)
    st.title("Profile Settings")

    prof = user["profile"]
    name = st.text_input("Display Name", prof.get("name", u), key="profile_name")
    pwd  = st.text_input("New Password", "", type="password", key="profile_password")
    bio  = st.text_area("Bio", prof.get("bio", ""), key="profile_bio")
    sb   = st.checkbox("Show Bio", prof.get("show_bio", False), key="profile_show_bio")
    pic  = st.file_uploader("Profile Picture", type=["png","jpg","jpeg"], key="profile_pic")
    sp   = st.checkbox("Show Picture", prof.get("show_pic", False), key="profile_show_pic")

    if st.button("Save", key="profile_save"):
        pid = prof.get("pic")
        if pic:
            pid = store_file(io.BytesIO(pic.getvalue()), pic.name)
        new_prof = {"name": name, "bio": bio, "pic": pid, "show_bio": sb, "show_pic": sp}
        # Include all fields in visible_fields
        update_profile(u, new_prof, list(new_prof.keys()))
        st.success("Profile updated")
        
        # Handle password change if provided
        if pwd:
            # You need to implement password change functionality
            # For now, just inform the user
            st.info("Password change functionality not implemented yet")