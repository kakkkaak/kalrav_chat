# Home.py
import streamlit as st
from database import init_db, get_user, get_notifications, mark_notifications_read

init_db()
st.set_page_config(page_title="Home",layout="wide")

if "username" not in st.session_state:
    st.error("Please log in."); st.stop()

u = st.session_state.username
st.title(f"Welcome to Big Boss Chat, {u}!")

# Notification bell
notif = get_notifications(u)
cols=st.columns([None,1])
with cols[1]:
    if st.button(f"🔔 {len(notif)}"):
        for n in notif:
            st.write(f"🔔 Message from {n['msg_id']['sender']} at {n['ts']}")
        mark_notifications_read(u)

st.header("Activity")
# Show notifications summary
if notif:
    st.subheader("New messages")
    for n in notif:
        st.write(f"From **{n['msg_id']['sender']}** at {n['ts']}")
else:
    st.write("No new activity.")

# Profile summary
user = get_user(u)
st.subheader("Your Profile")
st.write(f"**Name:** {user['name']}")
if user["profile"]["show_bio"]:
    st.write(f"**Bio:** {user['profile']['bio']}")
if user["profile"]["show_pic"] and user["profile"]["profile_picture"]:
    import io,streamlit as st
    from database import get_file
    fdoc=get_file(user["profile"]["profile_picture"])
    st.image(fdoc["content"],width=150)
