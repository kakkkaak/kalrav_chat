import streamlit as st, io
from database import (
    get_private_conversation, get_group_conversation,
    create_message, store_file, get_file,
    get_user_groups, delete_message, edit_message,
    mark_messages_read, search_messages, add_reaction, get_user,
    get_new_private_messages, get_new_group_messages
)
import emoji
from datetime import datetime
import time
import logging

# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

def show_chat():
    u = st.session_state.username
    display_name = st.session_state.display_name or u
    avatar = st.session_state.avatar or "👤"
    st.title(f"{avatar} Chat 💬")

    # Initialize session state
    if "chat_mode" not in st.session_state:
        st.session_state.chat_mode = "private"
    if "chat_partner" not in st.session_state:
        st.session_state.chat_partner = None
    if "chat_group" not in st.session_state:
        st.session_state.chat_group = None
    if "message_offset" not in st.session_state:
        st.session_state.message_offset = 0
    if "editing_message_id" not in st.session_state:
        st.session_state.editing_message_id = None
    if "all_users" not in st.session_state:
        try:
            st.session_state.all_users = [doc["username"] for doc in __import__("database").users_coll.find({"username": {"$ne": u}})]
        except Exception as e:
            logging.error(f"Error fetching users: {e}")
            st.error(f"Error fetching users: {e}")
            st.session_state.all_users = []
    if "chatted_users" not in st.session_state:
        st.session_state.chatted_users = set()
        try:
            messages = __import__("database").messages_coll.find({
                "$or": [{"sender": u}, {"receiver": u}]
            })
            for msg in messages:
                if msg["sender"] != u:
                    st.session_state.chatted_users.add(msg["sender"])
                if msg.get("receiver") and msg["receiver"] != u:
                    st.session_state.chatted_users.add(msg["receiver"])
        except Exception as e:
            logging.error(f"Error fetching chatted users: {e}")
            st.error(f"Error fetching chatted users: {e}")
    if "last_message_time" not in st.session_state:
        st.session_state.last_message_time = datetime.utcnow()
    if "cached_messages" not in st.session_state:
        st.session_state.cached_messages = []
    if "auto_refresh" not in st.session_state:
        st.session_state.auto_refresh = True
    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = time.time()
    if "is_sending" not in st.session_state:
        st.session_state.is_sending = False

    # Secondary sidebar for chat selection
    with st.sidebar:
        st.subheader("Chats", divider=True)
        st.markdown("""
        <style>
            .chat-button {
                background: linear-gradient(90deg, #007bff, #00d4ff);
                color: white !important;
                border-radius: 8px;
                padding: 0.6rem !important;
                margin: 0.3rem 0;
                transition: all 0.3s ease;
                width: 100%;
                text-align: left;
                border: none;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }
            .chat-button:hover {
                background: linear-gradient(90deg, #0056b3, #00aaff);
                transform: translateX(5px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            }
            .dark .chat-button {
                background: linear-gradient(90deg, #444, #666);
            }
            .dark .chat-button:hover {
                background: linear-gradient(90deg, #333, #555);
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Show users with existing chats
        st.markdown("**Private**")
        for other in sorted(st.session_state.chatted_users):
            if st.button(other, key=f"chat_user_{other}", help=f"Chat with {other}", use_container_width=True):
                st.session_state.chat_mode = "private"
                st.session_state.chat_partner = other
                st.session_state.message_offset = 0
                st.session_state.editing_message_id = None
                st.session_state.cached_messages = []
                st.session_state.last_message_time = datetime.utcnow()
                st.session_state.is_sending = False
                st.rerun()

        # Dropdown for new chats with confirmation button
        st.markdown("**Start New Chat**")
        new_users = [user for user in st.session_state.all_users if user not in st.session_state.chatted_users]
        if not new_users:
            st.info("No new users to chat with.")
        else:
            new_user = st.selectbox("Select user", [""] + new_users, key="new_chat_user")
            if new_user and st.button("Start Chat", key="start_new_chat"):
                st.session_state.chat_mode = "private"
                st.session_state.chat_partner = new_user
                st.session_state.message_offset = 0
                st.session_state.editing_message_id = None
                st.session_state.cached_messages = []
                st.session_state.last_message_time = datetime.utcnow()
                st.session_state.chatted_users.add(new_user)
                st.session_state.is_sending = False
                st.rerun()

        # Group chats
        st.markdown("**Groups**")
        try:
            for grp in get_user_groups(u):
                if st.button(grp["name"], key=f"chat_group_{grp['name']}", help=f"Join {grp['name']}", use_container_width=True):
                    st.session_state.chat_mode = "group"
                    st.session_state.chat_group = grp["name"]
                    st.session_state.message_offset = 0
                    st.session_state.editing_message_id = None
                    st.session_state.cached_messages = []
                    st.session_state.last_message_time = datetime.utcnow()
                    st.session_state.is_sending = False
                    st.rerun()
        except Exception as e:
            logging.error(f"Error fetching groups: {e}")
            st.error(f"Error fetching groups: {e}")

    mode = st.session_state.chat_mode

    # Auto-refresh logic (paused during sending)
    st.checkbox("Enable Auto-Refresh", value=st.session_state.auto_refresh, key="auto_refresh_toggle")
    st.session_state.auto_refresh = st.session_state.auto_refresh_toggle
    if (st.session_state.auto_refresh and 
        not st.session_state.is_sending and 
        time.time() - st.session_state.last_refresh >= 5):
        st.session_state.last_refresh = time.time()
        st.rerun()

    if mode == "private":
        p = st.session_state.chat_partner
        if not p:
            st.info("Select a user from the sidebar or dropdown to start chatting")
            return

        try:
            mark_messages_read(u, p)
        except Exception as e:
            logging.error(f"Error marking messages read: {e}")
            st.error(f"Error marking messages read: {e}")

        # Refresh button
        if st.button("Refresh Chat", key="refresh_private_chat"):
            st.session_state.cached_messages = []
            st.session_state.last_message_time = datetime.utcnow()
            st.session_state.is_sending = False
            st.rerun()

        search_query = st.text_input("Search messages", key="search_input_private", placeholder="🔍 Type to search...")
        try:
            if search_query:
                messages = search_messages(search_query, u, p=p)
                st.session_state.cached_messages = messages
                st.session_state.last_message_time = datetime.utcnow() if not messages else max(m["timestamp"] for m in messages)
            else:
                # Fetch new messages since last timestamp
                new_messages = get_new_private_messages(u, p, st.session_state.last_message_time)
                if new_messages:
                    st.session_state.cached_messages.extend(new_messages)
                    st.session_state.last_message_time = max(m["timestamp"] for m in new_messages)
                # Fetch initial messages if cache is empty
                if not st.session_state.cached_messages:
                    st.session_state.cached_messages = get_private_conversation(u, p, skip=st.session_state.message_offset, limit=50)
                    if st.session_state.cached_messages:
                        st.session_state.last_message_time = max(m["timestamp"] for m in st.session_state.cached_messages)
                messages = st.session_state.cached_messages
        except Exception as e:
            logging.error(f"Error fetching messages: {e}")
            st.error(f"Error fetching messages: {e}")
            messages = []

        if not messages:
            st.info(f"Start your conversation with {p}!")
        else:
            for m in messages:
                with st.chat_message("user" if m["sender"] == u else "assistant"):
                    try:
                        sender_display = get_user(m["sender"])["profile"].get("display_name", m["sender"])
                    except Exception as e:
                        logging.error(f"Error fetching user: {e}")
                        st.error(f"Error fetching user: {e}")
                        sender_display = m["sender"]
                    st.markdown(f"**{sender_display}**")
                    if st.session_state.editing_message_id == str(m["_id"]):
                        # Editing mode
                        if m.get("file_id"):
                            try:
                                fdoc = get_file(m["file_id"])
                                if fdoc["name"].lower().endswith(".pdf"):
                                    st.write("📄 PDF Attachment")
                                    st.download_button(
                                        label="Download PDF",
                                        data=fdoc["content"],
                                        file_name=fdoc["name"],
                                        mime="application/pdf"
                                    )
                                else:
                                    st.image(fdoc["content"])
                                    st.download_button(
                                        label="Download Image",
                                        data=fdoc["content"],
                                        file_name=fdoc["name"],
                                        mime="image/jpeg"
                                    )
                            except Exception as e:
                                logging.error(f"Error fetching file: {e}")
                                st.error(f"Error fetching file: {e}")
                        new_content = st.text_input("Edit message", value=m["content"], key=f"edit_{m['_id']}")
                        if st.button("Save", key=f"save_{m['_id']}"):
                            try:
                                edit_message(str(m["_id"]), u, new_content)
                                st.session_state.editing_message_id = None
                                st.session_state.cached_messages = []
                                st.rerun()
                            except Exception as e:
                                logging.error(f"Error editing message: {e}")
                                st.error(f"Error editing message: {e}")
                    else:
                        # Normal display
                        if m.get("edited", False):
                            st.markdown("*(Edited)*")
                        st.write(emoji.emojize(m["content"]))
                        st.markdown(f"<small>{m['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</small>", unsafe_allow_html=True)
                        if m.get("file_id"):
                            try:
                                fdoc = get_file(m["file_id"])
                                if fdoc["name"].lower().endswith(".pdf"):
                                    st.write("📄 PDF Attachment")
                                    st.download_button(
                                        label="Download PDF",
                                        data=fdoc["content"],
                                        file_name=fdoc["name"],
                                        mime="application/pdf"
                                    )
                                else:
                                    st.image(fdoc["content"])
                                    st.download_button(
                                        label="Download Image",
                                        data=fdoc["content"],
                                        file_name=fdoc["name"],
                                        mime="image/jpeg"
                                    )
                            except Exception as e:
                                logging.error(f"Error fetching file: {e}")
                                st.error(f"Error fetching file: {e}")
                        if m.get("reactions"):
                            st.markdown(" ".join(f"{r} {c}" for r, c in m["reactions"].items()))
                        if m["sender"] == u:
                            status = "Read" if m.get("read", False) else "Sent"
                            st.markdown(f"<small>*{status}*</small>", unsafe_allow_html=True)
                            col1, col2, col3 = st.columns([1, 1, 2])
                            with col1:
                                if st.button("Edit", key=f"edit_btn_{m['_id']}"):
                                    st.session_state.editing_message_id = str(m["_id"])
                                    st.rerun()
                            with col2:
                                if st.button("Delete", key=f"delete_btn_{m['_id']}"):
                                    try:
                                        delete_message(str(m["_id"]), u)
                                        st.session_state.cached_messages = []
                                        st.rerun()
                                    except Exception as e:
                                        logging.error(f"Error deleting message: {e}")
                                        st.error(f"Error deleting message: {e}")
                            with col3:
                                reaction = st.selectbox("React", ["", "👍", "❤️", "😂"], key=f"react_{m['_id']}")
                                if reaction:
                                    try:
                                        add_reaction(str(m["_id"]), u, reaction)
                                        st.session_state.cached_messages = []
                                        st.rerun()
                                    except Exception as e:
                                        logging.error(f"Error adding reaction: {e}")
                                        st.error(f"Error adding reaction: {e}")

        if not search_query and len(messages) == 50:
            if st.button("Load More", key="load_more_private"):
                st.session_state.message_offset += 50
                st.session_state.cached_messages = []
                st.rerun()

        txt = st.chat_input("Send a private message…")
        up = st.file_uploader("Attachment", type=["png","jpg","jpeg","pdf"], key="private_upload")
        if txt or up:
            try:
                st.session_state.is_sending = True
                fid = None
                if up:
                    fid = store_file(io.BytesIO(up.getvalue()), up.name)
                # Create message
                create_message(u, receiver=p, content=txt if txt is not None else "", file_id=fid)
                # Append new message to cache
                new_msg = {
                    "sender": u,
                    "receiver": p,
                    "content": txt if txt is not None else "",
                    "timestamp": datetime.utcnow(),
                    "file_id": fid,
                    "read": False,
                    "reactions": {}
                }
                st.session_state.cached_messages.append(new_msg)
                st.session_state.last_message_time = new_msg["timestamp"]
                if p not in st.session_state.chatted_users:
                    st.session_state.chatted_users.add(p)
                st.session_state.is_sending = False
                st.rerun()
            except Exception as e:
                st.session_state.is_sending = False
                logging.error(f"Error sending message: {e}")
                st.error(f"Failed to send message: {e}")

    else:  # Group mode
        g = st.session_state.chat_group
        if not g:
            st.info("Select a group from the sidebar to start chatting")
            return

        # Refresh button
        if st.button("Refresh Chat", key="refresh_group_chat"):
            st.session_state.cached_messages = []
            st.session_state.last_message_time = datetime.utcnow()
            st.session_state.is_sending = False
            st.rerun()

        search_query = st.text_input("Search messages", key="search_input_group", placeholder="🔍 Type to search...")
        try:
            if search_query:
                messages = search_messages(search_query, u, g=g)
                st.session_state.cached_messages = messages
                st.session_state.last_message_time = datetime.utcnow() if not messages else max(m["timestamp"] for m in messages)
            else:
                # Fetch new messages since last timestamp
                new_messages = get_new_group_messages(g, st.session_state.last_message_time)
                if new_messages:
                    st.session_state.cached_messages.extend(new_messages)
                    st.session_state.last_message_time = max(m["timestamp"] for m in new_messages)
                # Fetch initial messages if cache is empty
                if not st.session_state.cached_messages:
                    st.session_state.cached_messages = get_group_conversation(g, skip=st.session_state.message_offset, limit=50)
                    if st.session_state.cached_messages:
                        st.session_state.last_message_time = max(m["timestamp"] for m in st.session_state.cached_messages)
                messages = st.session_state.cached_messages
        except Exception as e:
            logging.error(f"Error fetching messages: {e}")
            st.error(f"Error fetching messages: {e}")
            messages = []

        for m in messages:
            with st.chat_message("user" if m["sender"] == u else "assistant"):
                try:
                    sender_display = get_user(m["sender"])["profile"].get("display_name", m["sender"])
                except Exception as e:
                    logging.error(f"Error fetching user: {e}")
                    st.error(f"Error fetching user: {e}")
                    sender_display = m["sender"]
                st.markdown(f"**{sender_display}**")
                if st.session_state.editing_message_id == str(m["_id"]):
                    # Editing mode
                    if m.get("file_id"):
                        try:
                            fdoc = get_file(m["file_id"])
                            if fdoc["name"].lower().endswith(".pdf"):
                                st.write("📄 PDF Attachment")
                                st.download_button(
                                    label="Download PDF",
                                    data=fdoc["content"],
                                    file_name=fdoc["name"],
                                    mime="application/pdf"
                                )
                            else:
                                st.image(fdoc["content"])
                                st.download_button(
                                    label="Download Image",
                                    data=fdoc["content"],
                                    file_name=fdoc["name"],
                                    mime="image/jpeg"
                                )
                        except Exception as e:
                            logging.error(f"Error fetching file: {e}")
                            st.error(f"Error fetching file: {e}")
                    new_content = st.text_input("Edit message", value=m["content"], key=f"edit_{m['_id']}")
                    if st.button("Save", key=f"save_{m['_id']}"):
                        try:
                            edit_message(str(m["_id"]), u, new_content)
                            st.session_state.editing_message_id = None
                            st.session_state.cached_messages = []
                            st.rerun()
                        except Exception as e:
                            logging.error(f"Error editing message: {e}")
                            st.error(f"Error editing message: {e}")
                else:
                    # Normal display
                    if m.get("edited", False):
                        st.markdown("*(Edited)*")
                    st.write(emoji.emojize(m["content"]))
                    st.markdown(f"<small>{m['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</small>", unsafe_allow_html=True)
                    if m.get("file_id"):
                        try:
                            fdoc = get_file(m["file_id"])
                            if fdoc["name"].lower().endswith(".pdf"):
                                st.write("📄 PDF Attachment")
                                st.download_button(
                                    label="Download PDF",
                                    data=fdoc["content"],
                                    file_name=fdoc["name"],
                                    mime="application/pdf"
                                )
                            else:
                                st.image(fdoc["content"])
                                st.download_button(
                                    label="Download Image",
                                    data=fdoc["content"],
                                    file_name=fdoc["name"],
                                    mime="image/jpeg"
                                )
                        except Exception as e:
                            logging.error(f"Error fetching file: {e}")
                            st.error(f"Error fetching file: {e}")
                    if m.get("reactions"):
                        st.markdown(" ".join(f"{r} {c}" for r, c in m["reactions"].items()))
                    if m["sender"] == u:
                        col1, col2, col3 = st.columns([1, 1, 2])
                        with col1:
                            if st.button("Edit", key=f"edit_btn_{m['_id']}"):
                                st.session_state.editing_message_id = str(m["_id"])
                                st.rerun()
                        with col2:
                            if st.button("Delete", key=f"delete_btn_{m['_id']}"):
                                try:
                                    delete_message(str(m["_id"]), u)
                                    st.session_state.cached_messages = []
                                    st.rerun()
                                except Exception as e:
                                    logging.error(f"Error deleting message: {e}")
                                    st.error(f"Error deleting message: {e}")
                        with col3:
                            reaction = st.selectbox("React", ["", "👍", "❤️", "😂"], key=f"react_{m['_id']}")
                            if reaction:
                                try:
                                    add_reaction(str(m["_id"]), u, reaction)
                                    st.session_state.cached_messages = []
                                    st.rerun()
                                except Exception as e:
                                    logging.error(f"Error adding reaction: {e}")
                                    st.error(f"Error adding reaction: {e}")

        if not search_query and len(messages) == 50:
            if st.button("Load More", key="load_more_group"):
                st.session_state.message_offset += 50
                st.session_state.cached_messages = []
                st.rerun()

        txt = st.chat_input("Send a group message…")
        up = st.file_uploader("Attachment", type=["png","jpg","jpeg","pdf"], key="group_upload")
        if txt or up:
            try:
                st.session_state.is_sending = True
                fid = None
                if up:
                    fid = store_file(io.BytesIO(up.getvalue()), up.name)
                # Create message
                create_message(u, group=g, content=txt if txt is not None else "", file_id=fid)
                # Append new message to cache
                new_msg = {
                    "sender": u,
                    "group": g,
                    "content": txt if txt is not None else "",
                    "timestamp": datetime.utcnow(),
                    "file_id": fid,
                    "read": False,
                    "reactions": {}
                }
                st.session_state.cached_messages.append(new_msg)
                st.session_state.last_message_time = new_msg["timestamp"]
                st.session_state.is_sending = False
                st.rerun()
            except Exception as e:
                st.session_state.is_sending = False
                logging.error(f"Error sending group message: {e}")
                st.error(f"Failed to send group message: {e}")