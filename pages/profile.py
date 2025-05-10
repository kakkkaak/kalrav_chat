# pages/profile.py
import streamlit as st
from database import get_user, update_user_profile
from PIL import Image
import io

# Ensure the user is logged in
if "username" not in st.session_state:
    st.error("Please log in first.")
    st.stop()

username = st.session_state.username

st.title("👤 Profile Page")

# Fetch current user details
user = get_user(username)

# Fields for profile
name = st.text_input("Full Name", value=user.get("name", ""), max_chars=50)
password = st.text_input("New Password", type="password", max_chars=50)
bio = st.text_area("Bio", value=user.get("profile", {}).get("bio", ""))
show_bio = st.checkbox("Show bio to public", value=user.get("profile", {}).get("show_bio", False))

profile_picture = st.file_uploader("Upload Profile Picture", type=["png", "jpg", "jpeg"], help="Max size: 10MB")
show_picture = st.checkbox("Show picture to public", value=user.get("profile", {}).get("show_picture", False))

# Update the profile on submit
if st.button("Save Profile"):
    if name and password:
        updated_profile = {
            "name": name,
            "password": password,
            "profile": {
                "bio": bio,
                "show_bio": show_bio,
                "profile_picture": profile_picture,
                "show_picture": show_picture
            }
        }
        # Update the profile in the database
        update_user_profile(username, updated_profile)
        st.success("Profile updated successfully.")
    else:
        st.error("Name and password are required.")
