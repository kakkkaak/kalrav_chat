import streamlit as st
from database import get_user_groups, create_group, invite_user_to_group, user_group_count, get_user_invites, accept_invite, remove_member_from_group

def show_groups():
    u = st.session_state.username
    st.title("Groups")

    st.subheader("Your Memberships")
    for g in get_user_groups(u):
        st.write(f"• {g['name']}")

    st.header("Create New Group")
    name = st.text_input("Group Name", key="group_name_input")
    invitees = st.multiselect(
        "Invite Users",
        [usr["username"] for usr in __import__("database").users_coll.find({"username": {"$ne": u}})],
        key="group_invitees"
    )
    if st.button("Create", key="create_group_button"):
        if not name:
            st.error("Please enter a group name")
        elif not st.session_state.is_admin and user_group_count(u) >= 1:
            st.error("You can only create one custom group")
        else:
            try:
                create_group(name, u)
                for inv in invitees:
                    invite_user_to_group(name, inv)
                st.success("Group created & invites sent")
                st.rerun()
            except Exception as e:
                if "duplicate key error" in str(e).lower():
                    st.error(f"A group with name '{name}' already exists")
                else:
                    st.error(f"Error creating group: {e}")

    st.header("Group Invitations")
    invites = get_user_invites(u)
    if invites:
        for inv in invites:
            st.write(f"• Invitation to join **{inv['group']}**")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Accept", key=f"accept_invite_{str(inv['_id'])}"):
                    accept_invite(u, inv['group'])
                    st.success(f"Joined {inv['group']}")
                    st.rerun()
            with col2:
                if st.button("Decline", key=f"decline_invite_{str(inv['_id'])}"):
                    __import__("database").invites_coll.delete_one({"_id": inv['_id']})
                    st.success(f"Declined invitation to {inv['group']}")
                    st.rerun()
    else:
        st.write("No pending invitations.")

    st.header("Manage Groups")
    for g in get_user_groups(u):
        if g["creator"] == u:
            st.subheader(f"Manage {g['name']}")
            members = g["members"]
            for member in members:
                if member != u:
                    if st.button(f"Kick {member}", key=f"kick_{g['name']}_{member}"):
                        remove_member_from_group(g['name'], member)
                        st.success(f"Kicked {member} from {g['name']}")
                        st.rerun()