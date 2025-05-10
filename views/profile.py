import streamlit as st
from database import get_user, update_profile

def show_profile():
    st.title("Profile Settings")
    username = st.session_state.username
    user = get_user(username)
    profile = user["profile"]
    visible_fields = user["visible_fields"]

    with st.form("profile_form"):
        display_name = st.text_input("Display Name", value=profile.get("display_name", profile["name"]))
        avatar = st.selectbox("Avatar", ["👤", "😎", "🚀", "🐱", "🦁"], index=["👤", "😎", "🚀", "🐱", "🦁"].index(profile.get("avatar", "👤")))
        name = st.text_input("Name", value=profile["name"])
        bio = st.text_area("Bio", value=profile["bio"])
        show_bio = st.checkbox("Show Bio", value=profile["show_bio"])
        show_pic = st.checkbox("Show Profile Picture", value=profile["show_pic"])
        
        visible = st.multiselect(
            "Visible Fields",
            options=["name", "bio", "display_name", "avatar"],
            default=visible_fields
        )
        
        submitted = st.form_submit_button("Save")
        if submitted:
            new_profile = {
                "name": name,
                "bio": bio,
                "pic": None,
                "show_bio": show_bio,
                "show_pic": show_pic,
                "display_name": display_name,
                "avatar": avatar
            }
            update_profile(username, new_profile, visible)
            st.session_state.display_name = display_name or name
            st.session_state.avatar = avatar
            st.success("Profile updated!")