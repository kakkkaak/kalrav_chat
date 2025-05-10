# Profile.py
import streamlit as st, io
from database import get_user, update_user_profile, store_file

if "username" not in st.session_state:
    st.error("Login first"); st.stop()

u=st.session_state.username
user=get_user(u)
st.title("Profile")

name=st.text_input("Display Name",user["name"])
pwd=st.text_input("New Password","",type="password")
bio=st.text_area("Bio",user["profile"]["bio"])
show_bio=st.checkbox("Show Bio",user["profile"]["show_bio"])
pic=st.file_uploader("Profile Picture",type=["png","jpg","jpeg"])
show_pic=st.checkbox("Show Picture",user["profile"]["show_pic"])

if st.button("Save"):
    pic_id=user["profile"]["profile_picture"]
    if pic:
        pic_id=store_file(io.BytesIO(pic.getvalue()),pic.name)
    update_user_profile(u,{"name":name,"password":pwd or "ignore","profile":{"bio":bio,"profile_picture":pic_id,"show_bio":show_bio,"show_picture":show_pic}})
    st.success("Saved")
