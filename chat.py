# Chat.py
import streamlit as st
from database import get_user_private_chats, get_user_groups, get_private_conversation, get_group_conversation, create_message, store_file

st.set_page_config(page_title="Chat",layout="wide")
if "username" not in st.session_state:
    st.error("Login first"); st.stop()

u=st.session_state.username
st.sidebar.title("Chat")
# Private chats
st.sidebar.subheader("Private")
for other in get_user_private_chats(u):
    if st.sidebar.button(other):
        st.session_state.chat_mode="private"; st.session_state.chat_partner=other
# Group chats
st.sidebar.subheader("Groups")
for g in get_user_groups(u):
    if st.sidebar.button(g["name"]):
        st.session_state.chat_mode="group"; st.session_state.chat_group=g["name"]

# Render selected chat
if st.session_state.get("chat_mode")=="private":
    other=st.session_state.chat_partner
    st.header(f"Chat with {other}")
    for msg in get_private_conversation(u,other):
        with st.chat_message("assistant" if msg["sender"]!=u else "user"):
            st.write(msg["content"])
            if msg.get("file"):
                fdoc=store_file;pass
    txt=st.chat_input("Message...")
    up=st.file_uploader("File?",type=["png","jpg","jpeg"],label="")
    if txt or up:
        fid=None
        if up:
            fid=store_file(io.BytesIO(up.getvalue()),up.name)
        create_message(u,receiver=other,content=txt,file=fid)
        st.experimental_rerun()

elif st.session_state.get("chat_mode")=="group":
    gr=st.session_state.chat_group
    st.header(f"Group: {gr}")
    for msg in get_group_conversation(gr):
        with st.chat_message("assistant" if msg["sender"]!=u else "user"):
            st.write(msg["content"])
            if msg.get("file"):
                fdoc=get_file(msg["file"])
                st.image(fdoc["content"])
    txt=st.chat_input("Message...")
    up=st.file_uploader("File?",type=["png","jpg","jpeg"],label="")
    if txt or up:
        fid=None
        if up:
            fid=store_file(io.BytesIO(up.getvalue()),up.name)
        create_message(u,group=gr,content=txt,file=fid)
        st.experimental_rerun()
