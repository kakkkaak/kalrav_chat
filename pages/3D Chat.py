# pages/01_3D_Chat.py

import streamlit as st
from database import (
    users_coll,
    groups_coll,
    create_message,
    get_private_conversation,
    get_group_conversation,
    list_rooms
)

st.set_page_config(page_title="3D Chat", layout="wide")

# Ensure user is logged in
if "username" not in st.session_state:
    st.error("Please log in first on the main page.")
    st.stop()

st.title("🌐 3D Chat Room")

mode = st.radio("Mode", ["Private Chat", "Group Chat"], horizontal=True)

if mode == "Private Chat":
    # Fetch all other users
    all_users = [u["username"] for u in users_coll.find()]
    others    = [u for u in all_users if u != st.session_state.username]
    if not others:
        st.info("No other users available yet.")
    else:
        partner = st.selectbox("Chat with", others)
        # Display conversation
        for msg in get_private_conversation(st.session_state.username, partner):
            is_me = msg["sender"] == st.session_state.username
            with st.chat_message("user" if is_me else "assistant"):
                st.markdown(msg["content"])
        # Send new message
        new = st.chat_input("Send a private message…")
        if new:
            create_message(
                sender=st.session_state.username,
                receiver=partner,
                content=new
            )

else:  # Group Chat
    rooms = [g["name"] for g in list_rooms(st.session_state.username)]
    if not rooms:
        st.info("No chat rooms available yet.")
    else:
        room = st.selectbox("Select Room", rooms)
        for msg in get_group_conversation(room):
            is_me = msg["sender"] == st.session_state.username
            with st.chat_message("user" if is_me else "assistant"):
                st.markdown(msg["content"])
        new = st.chat_input(f"Send a message to #{room}…")
        if new:
            create_message(
                sender=st.session_state.username,
                group=room,
                content=new
            )
