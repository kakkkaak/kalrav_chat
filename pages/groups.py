# Groups.py
import streamlit as st
from database import get_user_groups, create_group

st.set_page_config(page_title="Groups",layout="wide")
if "username" not in st.session_state:
    st.error("Login first"); st.stop()

u=st.session_state.username
st.title("Your Groups")
for g in get_user_groups(u):
    st.write(f"- {g['name']}")

st.header("Create Group")
name=st.text_input("Group Name")
inv=st.multiselect("Invite", [u["username"] for u in __import__("database").users_coll.find() if u["username"]!=u])
if st.button("Create"):
    create_group(name,u,inv)
    st.success("Created"); st.experimental_rerun()
