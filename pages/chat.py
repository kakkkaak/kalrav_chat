import streamlit as st, io
from database import (
    get_private_conversation, get_group_conversation,
    create_message, store_file, get_file,
    get_user_groups
)

def show_chat():
    u = st.session_state.username
    st.title("Chat")

    with st.sidebar:
        st.subheader("Private")
        for other_doc in __import__("database").users_coll.find({"username": {"$ne": u}}):
            other = other_doc["username"]
            if st.button(other):
                st.session_state.chat_mode = "private"
                st.session_state.chat_partner = other

        st.subheader("Groups")
        for grp in get_user_groups(u):
            if st.button(grp["name"]):
                st.session_state.chat_mode = "group"
                st.session_state.chat_group = grp["name"]

    mode = st.session_state.get("chat_mode", "private")
    if mode == "private":
        p = st.session_state.chat_partner
        for m in get_private_conversation(u, p):
            with st.chat_message("user" if m["sender"] == u else "assistant"):
                st.write(m["content"])
                if m.get("file_id"):
                    fdoc = get_file(m["file_id"])
                    st.image(fdoc["content"])
        txt = st.chat_input("Send a private message…")
        up = st.file_uploader("Attachment", type=["png","jpg","jpeg"])
        if txt or up:
            fid = None
            if up:
                fid = store_file(io.BytesIO(up.getvalue()), up.name)
            create_message(u, receiver=p, content=txt, file_id=fid)
            st.experimental_rerun()

    else:
        g = st.session_state.chat_group
        for m in get_group_conversation(g):
            with st.chat_message("user" if m["sender"] == u else "assistant"):
                st.write(m["content"])
                if m.get("file_id"):
                    fdoc = get_file(m["file_id"])
                    st.image(fdoc["content"])
        txt = st.chat_input("Send a group message…")
        up = st.file_uploader("Attachment", type=["png","jpg","jpeg"])
        if txt or up:
            fid = None
            if up:
                fid = store_file(io.BytesIO(up.getvalue()), up.name)
            create_message(u, group=g, content=txt, file_id=fid)
            st.experimental_rerun()
