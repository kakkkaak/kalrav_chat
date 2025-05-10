# pages/3d_chat.py
import streamlit as st
from database import (
    users_coll,
    groups_coll,
    create_message,
    get_private_conversation,
    get_group_conversation,
    store_file
)

st.set_page_config(page_title="3D Chat", layout="wide")

# Ensure user is logged in
if "username" not in st.session_state:
    st.error("Please log in first.")
    st.stop()

st.title("🌐 3D Chat Room")

# Show the sidebar based on the user's private and group chats
def get_user_sidebar(username):
    # Fetch and display personalized chat list (private & group)
    all_groups = groups_coll.find({"members": username})
    private_chats = [user["username"] for user in users_coll.find() if user["username"] != username]

    st.sidebar.header(f"Chats for {username}")
    for group in all_groups:
        st.sidebar.text(f"Group: {group['name']}")

    for private_chat in private_chats:
        st.sidebar.text(f"Private chat with: {private_chat}")
    
# Sidebar personalized for each user
get_user_sidebar(st.session_state.username)

# Choose whether private or group chat
mode = st.radio("Mode", ["Private Chat", "Group Chat"], horizontal=True)

# Private Chat Logic
if mode == "Private Chat":
    all_users = [u["username"] for u in users_coll.find()]
    others = [u for u in all_users if u != st.session_state.username]
    
    if not others:
        st.info("No other users available yet.")
    else:
        partner = st.selectbox("Chat with", others)
        for msg in get_private_conversation(st.session_state.username, partner):
            is_me = msg["sender"] == st.session_state.username
            with st.chat_message("user" if is_me else "assistant"):
                st.markdown(msg["content"])
                if msg.get("file"):
                    # Display the image or file
                    st.image(msg["file"])

        new = st.chat_input("Send a private message…")
        uploaded_file = st.file_uploader("Send a file", type=["jpg", "png", "jpeg", "pdf", "docx"], label="File (optional)")
        
        if new or uploaded_file:
            file_url = None
            if uploaded_file:
                file_url = store_file(uploaded_file, uploaded_file.name)
            
            create_message(
                sender=st.session_state.username,
                receiver=partner,
                content=new,
                file=file_url
            )

else:  # Group Chat Logic
    rooms = [g["name"] for g in list_rooms(st.session_state.username)]
    if not rooms:
        st.info("No chat rooms available yet.")
    else:
        room = st.selectbox("Select Room", rooms)
        for msg in get_group_conversation(room):
            is_me = msg["sender"] == st.session_state.username
            with st.chat_message("user" if is_me else "assistant"):
                st.markdown(msg["content"])
                if msg.get("file"):
                    st.image(msg["file"])
        
        new = st.chat_input(f"Send a message to #{room}…")
        uploaded_file = st.file_uploader("Send a file", type=["jpg", "png", "jpeg", "pdf", "docx"], label="File (optional)")
        
        if new or uploaded_file:
            file_url = None
            if uploaded_file:
                file_url = store_file(uploaded_file, uploaded_file.name)
            
            create_message(
                sender=st.session_state.username,
                group=room,
                content=new,
                file=file_url
            )
