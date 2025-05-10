import streamlit as st
from database import list_rooms, create_group, invite_user_to_group, get_user_invites, accept_invite

def show_groups():
    st.title("Groups")
    username = st.session_state.username
    
    st.subheader("Your Groups")
    for room in list_rooms(username):
        st.write(f"{room['name']} {'(Public)' if room['is_public'] else ''}")
    
    st.subheader("Create Group")
    with st.form("create_group"):
        name = st.text_input("Group Name")
        submitted = st.form_submit_button("Create")
        if submitted and name:
            create_group(name, username)
            st.success(f"Group {name} created!")
            st.rerun()
    
    st.subheader("Invite User")
    with st.form("invite_user"):
        group = st.text_input("Group Name")
        user = st.text_input("Username to Invite")
        submitted = st.form_submit_button("Invite")
        if submitted and group and user:
            invite_user_to_group(group, user)
            st.success(f"Invited {user} to {group}!")
    
    st.subheader("Pending Invites")
    for invite in get_user_invites(username):
        if st.button(f"Accept invite to {invite['group']}", key=f"accept_{invite['_id']}"):
            accept_invite(username, invite["group"])
            st.success(f"Joined {invite['group']}!")
            st.rerun()