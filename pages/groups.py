import streamlit as st
from database import get_user_groups, create_group

def show_groups():
    u = st.session_state.username
    st.title("Groups")
    for g in get_user_groups(u):
        st.write(f"• {g['name']}")

    st.header("Create New Group")
    name = st.text_input("Group Name")
    invitees = st.multiselect("Invite users", [u["username"] for u in __import__("database").users_coll.find() if u["username"]!=u])
    if st.button("Create"):
        create_group(name, u, invitees)
        st.success("Group created and invitations sent.")
        st.experimental_rerun()
