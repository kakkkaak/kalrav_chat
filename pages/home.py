import streamlit as st
from database import get_user, get_notifications, mark_notifications_read, get_file, list_rooms

def show_home():
    u = st.session_state.username
    st.title(f"Welcome to Big Boss Chat, {u}!")
    nots = get_notifications(u)
    c1, c2 = st.columns([9,1])
    with c2:
        if st.button(f"🔔 {len(nots)}"):
            for n in nots:
                st.write(f"From **{n['msg']['sender']}** at {n['ts']}")
            mark_notifications_read(u)
    st.header("Activity")
    if nots:
        for n in nots:
            st.write(f"• **{n['msg']['sender']}**: {n['msg']['msg']['content']}")
    else:
        st.write("No new activity.")
    st.header("Your Rooms")
    rooms = list_rooms(u)
    if rooms:
        for r in rooms:
            st.write(f"• {r['name']}")
    else:
        st.write("You’re not in any rooms yet.")
    st.header("Profile Summary")
    user = get_user(u)
    prof = user["profile"]
    st.write(f"**Name:** {prof.get('name', u)}")
    if prof.get("show_bio"):
        st.write(f"**Bio:** {prof.get('bio','')}")
    if prof.get("show_pic") and prof.get("pic"):
        f = get_file(prof["pic"])
        st.image(f["content"], width=150)
