import streamlit as st
import io
from database import (
    get_user_private_list,
    get_user_groups,
    get_private_conversation,
    get_group_conversation,
    create_message,
    store_file,
    get_file
)

def show_chat():
    u = st.session_state.username
    st.title("Chat")
    # Sidebar dynamic
    with st.sidebar:
        st.title("Chat")
        st.subheader("Private")
        for other in get_user_private_list(u):
            if st.button(other):
                st.session_state.chat_mode = "private"
                st.session_state.chat_partner = other
        st.subheader("Groups")
        for g in get_user_groups(u):
            if st.button(g["name"]):
                st.session_state.chat_mode = "group"
                st.session_state.chat_group = g["name"]

    mode = st.session_state.get("chat_mode", "private")
    if mode=="private":
        other = st.session_state.chat_partner
        for m in get_private_conversation(u, other):
            with st.chat_message("user" if m["sender"]==u else "assistant"):
                st.write(m["content"])
                if m.get("file"):
                    doc = get_file(m["file"])
                    st.image(doc["content"])
        txt = st.chat_input("Message…")
        up  = st.file_uploader("File?", type=["png","jpg","jpeg"])
        if txt or up:
            fid = None
            if up:
                fid = store_file(io.BytesIO(up.getvalue()), up.name)
            create_message(u, receiver=other, content=txt, file=fid)
            st.experimental_rerun()
    else:
        grp = st.session_state.chat_group
        for m in get_group_conversation(grp):
            with st.chat_message("user" if m["sender"]==u else "assistant"):
                st.write(m["content"])
                if m.get("file"):
                    doc = get_file(m["file"])
                    st.image(doc["content"])
        txt = st.chat_input("Message…")
        up  = st.file_uploader("File?", type=["png","jpg","jpeg"])
        if txt or up:
            fid = None
            if up:
                fid = store_file(io.BytesIO(up.getvalue()), up.name)
            create_message(u, group=grp, content=txt, file=fid)
            st.experimental_rerun()
