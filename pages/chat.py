# pages/02_Create_Group.py

import streamlit as st
from database import create_group, user_group_count

st.set_page_config(page_title="Create Group", layout="centered")

# Ensure user is logged in
if "username" not in st.session_state:
    st.error("Please log in first on the main page.")
    st.stop()

st.title("➕ Create Your Own Group")

# Admins can create unlimited; others only one
limit_reached = (not st.session_state.is_admin) and (user_group_count(st.session_state.username) >= 1)
if limit_reached:
    st.info("You’ve already created your one custom group.")
else:
    name = st.text_input("Group Name", "")
    if st.button("Create Group"):
        if not name.strip():
            st.warning("Group name cannot be empty.")
        else:
            try:
                create_group(name.strip(), st.session_state.username)
                st.success(f"Group '{name}' created successfully!")
            except Exception as e:
                st.error(str(e))
