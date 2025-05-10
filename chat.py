# pages/chat.py
import streamlit as st
import io
from database import (
    get_private_conversation,
    get_group_conversation,
    create_message,
    store_file,
    get_file,
    get_user_groups
)

def show_chat():
    # Ensure logged in
    if "username" not in st.session_state:
        st.error("Please log in first.")
        st.stop()

    u = st.session_state.username
    st.title("💬 Chat")

    # Sidebar: list private contacts and group chats
    with st.sidebar:
        st.subheader("Private Chats")
        # List all other users
        for user_doc in __import__("database").users_coll.find({"username": {"$ne": u}}):
            other = user_doc["username"]
            if st.button(other, key=f"p_{other}"):
                st.session_state.chat_mode = "private"
                st.session_state.chat_partner = other

        st.markdown("---")
        st.subheader("Group Chats")
        for grp in get_user_groups(u):
            name = grp["name"]
            if st.button(name, key=f"g_{name}"):
                st.session_state.chat_mode = "group"
                st.session_state.chat_group = name

    # Determine mode
    mode = st.session_state.get("chat_mode", "private")

    if mode == "private":
        partner = st.session_state.get("chat_partner")
        if not partner:
            st.info("Select a user from the sidebar to start a private chat.")
            return

        # Display private history
        for msg in get_private_conversation(u, partner):
            is_me = msg["sender"] == u
            with st.chat_message("user" if is_me else "assistant"):
                st.write(msg["content"])
                if msg.get("file_id"):
                    fdoc = get_file(msg["file_id"])
                    st.image(fdoc["content"])

        # Input new message
        text = st.chat_input("Send a private message…")
        uploaded = st.file_uploader("Attach image (jpg/png, ≤10MB)", type=["jpg","jpeg","png"], key="pu")
        if text or uploaded:
            fid = None
            if uploaded:
                # Ensure file size ≤ 10MB
                if uploaded.size > 10 * 1024 * 1024:
                    st.error("File exceeds 10MB limit.")
                else:
                    fid = store_file(io.BytesIO(uploaded.getvalue()), uploaded.name)
            create_message(sender=u, receiver=partner, content=text or "", file_id=fid)
            st.experimental_rerun()

    else:  # group mode
        group = st.session_state.get("chat_group")
        if not group:
            st.info("Select a group from the sidebar to start chatting.")
            return

        # Display group history
        for msg in get_group_conversation(group):
            is_me = msg["sender"] == u
            with st.chat_message("user" if is_me else "assistant"):
                st.write(msg["content"])
                if msg.get("file_id"):
                    fdoc = get_file(msg["file_id"])
                    st.image(fdoc["content"])

        # Input new group message
        text = st.chat_input(f"Send a message to #{group}…")
        uploaded = st.file_uploader("Attach image (jpg/png, ≤10MB)", type=["jpg","jpeg","png"], key="gu")
        if text or uploaded:
            fid = None
            if uploaded:
                if uploaded.size > 10 * 1024 * 1024:
                    st.error("File exceeds 10MB limit.")
                else:
                    fid = store_file(io.BytesIO(uploaded.getvalue()), uploaded.name)
            create_message(sender=u, group=group, content=text or "", file_id=fid)
            st.experimental_rerun()
