import streamlit as st
from database import get_user_groups, create_group, invite_user_to_group

def show_groups():
    u = st.session_state.username
    st.title("Groups")
    for g in get_user_groups(u):
        st.write(f"• {g['name']}")
    st.header("Create New Group")
    name = st.text_input("Group Name")
    invitees = st.multiselect(
        "Invite Users",
        [usr["username"] for usr in __import__("database").users_coll.find({"username":{"$ne":u}})]
    )
    if st.button("Create"):
        create_group(name, u)
        for inv in invitees:
            invite_user_to_group(name, inv)
        st.success("Group created & invites sent")
        st.experimental_rerun()
