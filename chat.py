# chat.py

import streamlit as st
from database import (
    users_coll,
    groups_coll,
    create_message,
    get_private_conversation,
    get_group_conversation,
    user_group_count,
    create_group,
)
from datetime import datetime

def render_chat():
    # ─── Page Config ──────────────────────────────────
    st.set_page_config(page_title="Chat Hub", layout="wide")

    # ensure user is logged in
    if "username" not in st.session_state:
        st.error("Please log in first.")
        st.stop()

    username = st.session_state.username
    is_admin = st.session_state.is_admin

    # ─── Sidebar ───────────────────────────────────────
    with st.sidebar:
        st.header("🔎 Chat Navigation")

        mode = st.radio("Mode", ["Private Chat", "Group Chat"])

        # Private chat partner selector
        if mode == "Private Chat":
            all_users = [u["username"] for u in users_coll.find()]
            others    = [u for u in all_users if u != username]
            partner   = st.selectbox("Chat with", others or ["(no one yet)"])
        # Group chat room selector
        else:
            # fetch all public rooms + those you created
            room_docs = groups_coll.find({
                "$or": [
                    {"is_public": True},
                    {"creator": username}
                ]
            })
            rooms = [r["name"] for r in room_docs]
            room  = st.selectbox("Room", rooms or ["(no rooms)"])

        st.markdown("---")
        st.subheader("➕ Create Group")
        can_create = is_admin or (user_group_count(username) < 1)
        new_grp    = st.text_input("New Group Name", key="new_grp")
        if st.button("Create"):
            if not can_create:
                st.error("You already have one custom group.")
            elif not new_grp.strip():
                st.warning("Group name cannot be empty.")
            else:
                try:
                    create_group(new_grp.strip(), username)
                    st.success(f"Group '{new_grp}' created!")
                except Exception as e:
                    st.error(str(e))

        st.markdown("---")
        if st.button("🚪 Logout"):
            for k in ("username", "is_admin", "auth_mode"):
                st.session_state.pop(k, None)

    # ─── Main Area ────────────────────────────────────
    st.title("💬 Chat Hub")

    if mode == "Private Chat":
        if others:
            # display private history
            for msg in get_private_conversation(username, partner):
                is_me = msg["sender"] == username
                with st.chat_message("user" if is_me else "assistant"):
                    st.markdown(msg["content"])
            # send new private message
            text = st.chat_input("Send a private message…")
            if text:
                create_message(sender=username, receiver=partner, content=text)
        else:
            st.info("No other users to chat with yet.")

    else:
        if rooms:
            # display group history
            for msg in get_group_conversation(room):
                is_me = msg["sender"] == username
                with st.chat_message("user" if is_me else "assistant"):
                    st.markdown(msg["content"])
            # send new group message
            text = st.chat_input(f"Send message to #{room}…")
            if text:
                create_message(sender=username, group=room, content=text)
        else:
            st.info("No chat rooms available yet.")
