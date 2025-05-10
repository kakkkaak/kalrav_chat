# pages/groups.py
import streamlit as st
from database import groups_coll, users_coll, create_group, send_group_invitation

st.set_page_config(page_title="Create Group", layout="wide")

# Ensure user is logged in
if "username" not in st.session_state:
    st.error("Please log in first.")
    st.stop()

st.title("🌐 Create New Group")

group_name = st.text_input("Group Name", max_chars=50)
invitees = st.multiselect("Invite Users", [u["username"] for u in users_coll.find() if u["username"] != st.session_state.username])

if st.button("Create Group"):
    try:
        create_group(st.session_state.username, group_name, invitees)
        st.success(f"Group '{group_name}' created and invitations sent.")
    except ValueError as e:
        st.error(str(e))
