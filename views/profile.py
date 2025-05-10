import streamlit as st
from database import get_user, update_profile, delete_user
from auth import logout

def show_profile():
    st.title("Profile Settings")
    username = st.session_state.username
    user = get_user(username)
    profile = user["profile"]
    visible_fields = user["visible_fields"]

    # Filter visible_fields to valid options
    valid_options = ["name", "bio", "display_name", "avatar"]
    filtered_visible_fields = [f for f in visible_fields if f in valid_options]

    with st.form("profile_form"):
        display_name = st.text_input("Display Name", value=profile.get("display_name", profile["name"]))
        avatar = st.selectbox("Avatar", ["👤", "😎", "🚀", "🐱", "🦁"], index=["👤", "😎", "🚀", "🐱", "🦁"].index(profile.get("avatar", "👤")))
        name = st.text_input("Name", value=profile["name"])
        bio = st.text_area("Bio", value=profile["bio"])
        show_bio = st.checkbox("Show Bio", value=profile["show_bio"])
        show_pic = st.checkbox("Show Profile Picture", value=profile["show_pic"])
        
        visible = st.multiselect(
            "Visible Fields",
            options=valid_options,
            default=filtered_visible_fields
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

    # Account deletion
    st.markdown("---")
    st.subheader("Delete Account")
    st.warning("This action is permanent and will delete all your data (messages, groups, etc.).")
    if st.checkbox("I understand, show delete option"):
        with st.form("delete_account_form"):
            confirm = st.text_input("Type your username to confirm", type="password")
            delete_btn = st.form_submit_button("Delete Account")
            if delete_btn and confirm == username:
                if delete_user(username):
                    logout()
                    st.success("Account deleted. You have been logged out.")
                    st.rerun()
                else:
                    st.error("Cannot delete admin account.")
            elif delete_btn:
                st.error("Username does not match.")