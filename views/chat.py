import streamlit as st, io
from database import (
    get_private_conversation, get_group_conversation,
    create_message, store_file, get_file,
    get_user_groups, delete_message, edit_message,
    mark_messages_read, search_messages
)
import emoji
from datetime import datetime

def show_chat():
    u = st.session_state.username
    st.title("Chat 💬")

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

    # Secondary sidebar for chat selection
    with st.sidebar:
        st.subheader("Chats", divider=True)
        st.markdown("""
        <style>
            .chat-button {
                background: #007bff;
                color: white;
                border-radius: 5px;
                padding: 0.5rem;
                margin: 0.2rem 0;
                transition: all 0.3s;
                width: 100%;
                text-align: left;
            }
            .chat-button:hover {
                background: #0056b3;
                transform: translateX(5px);
            }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("**Private**")
        for other_doc in __import__("database").users_coll.find({"username": {"$ne": u}}):
            other = other_doc["username"]
            if st.button(other, key=f"chat_user_{other}", help=f"Chat with {other}", use_container_width=True):
                st.session_state.chat_mode = "private"
                st.session_state.chat_partner = other
                st.session_state.message_offset = 0
                st.session_state.editing_message_id = None
                st.rerun()

        st.markdown("**Groups**")
        for grp in get_user_groups(u):
            if st.button(grp["name"], key=f"chat_group_{grp['name']}", help=f"Join {grp['name']}", use_container_width=True):
                st.session_state.chat_mode = "group"
                st.session_state.chat_group = grp["name"]
                st.session_state.message_offset = 0
                st.session_state.editing_message_id = None
                st.rerun()

    mode = st.session_state.chat_mode

    if mode == "private":
        p = st.session_state.chat_partner
        if not p:
            st.info("Select a user from the sidebar to start chatting")
            return

        mark_messages_read(u, p)

        search_query = st.text_input("Search messages", key="search_input_private", placeholder="Type to search...")
        if search_query:
            messages = search_messages(search_query, u, p=p)
        else:
            messages = get_private_conversation(u, p, skip=st.session_state.message_offset, limit=50)

        for m in messages:
            with st.chat_message("user" if m["sender"] == u else "assistant"):
                if st.session_state.editing_message_id == str(m["_id"]):
                    # Editing mode
                    if m.get("file_id"):
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
                    new_content = st.text_input("Edit message", value=m["content"], key=f"edit_{m['_id']}")
                    if st.button("Save", key=f"save_{m['_id']}"):
                        edit_message(str(m["_id"]), u, new_content)
                        st.session_state.editing_message_id = None
                        st.rerun()
                else:
                    # Normal display
                    if m.get("edited", False):
                        st.markdown("*(Edited)*")
                    st.write(emoji.emojize(m["content"]))
                    st.markdown(f"<small>{m['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</small>", unsafe_allow_html=True)
                    if m.get("file_id"):
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
                    if m["sender"] == u:
                        status = "Read" if m.get("read", False) else "Sent"
                        st.markdown(f"<small>*{status}*</small>", unsafe_allow_html=True)
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Edit", key=f"edit_btn_{m['_id']}"):
                                st.session_state.editing_message_id = str(m["_id"])
                                st.rerun()
                        with col2:
                            if st.button("Delete", key=f"delete_btn_{m['_id']}"):
                                delete_message(str(m["_id"]), u)
                                st.rerun()

        if not search_query and len(messages) == 50:
            if st.button("Load More", key="load_more_private"):
                st.session_state.message_offset += 50
                st.rerun()

        txt = st.chat_input("Send a private message…")
        up = st.file_uploader("Attachment", type=["png","jpg","jpeg","pdf"], key="private_upload")
        if txt or up:
            fid = None
            if up:
                fid = store_file(io.BytesIO(up.getvalue()), up.name)
            create_message(u, receiver=p, content=txt if txt is not None else "", file_id=fid)
            st.rerun()

    else:  # Group mode
        g = st.session_state.chat_group
        if not g:
            st.info("Select a group from the sidebar to start chatting")
            return

        search_query = st.text_input("Search messages", key="search_input_group", placeholder="Type to search...")
        if search_query:
            messages = search_messages(search_query, u, g=g)
        else:
            messages = get_group_conversation(g, skip=st.session_state.message_offset, limit=50)

        for m in messages:
            with st.chat_message("user" if m["sender"] == u else "assistant"):
                if st.session_state.editing_message_id == str(m["_id"]):
                    # Editing mode
                    if m.get("file_id"):
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
                    new_content = st.text_input("Edit message", value=m["content"], key=f"edit_{m['_id']}")
                    if st.button("Save", key=f"save_{m['_id']}"):
                        edit_message(str(m["_id"]), u, new_content)
                        st.session_state.editing_message_id = None
                        st.rerun()
                else:
                    # Normal display
                    if m.get("edited", False):
                        st.markdown("*(Edited)*")
                    st.write(emoji.emojize(m["content"]))
                    st.markdown(f"<small>{m['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</small>", unsafe_allow_html=True)
                    if m.get("file_id"):
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
                    if m["sender"] == u:
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Edit", key=f"edit_btn_{m['_id']}"):
                                st.session_state.editing_message_id = str(m["_id"])
                                st.rerun()
                        with col2:
                            if st.button("Delete", key=f"delete_btn_{m['_id']}"):
                                delete_message(str(m["_id"]), u)
                                st.rerun()

        if not search_query and len(messages) == 50:
            if st.button("Load More", key="load_more_group"):
                st.session_state.message_offset += 50
                st.rerun()

        txt = st.chat_input("Send a group message…")
        up = st.file_uploader("Attachment", type=["png","jpg","jpeg","pdf"], key="group_upload")
        if txt or up:
            fid = None
            if up:
                fid = store_file(io.BytesIO(up.getvalue()), up.name)
            create_message(u, group=g, content=txt if txt is not None else "", file_id=fid)
            st.rerun()