# app.py
import streamlit as st
from dotenv import load_dotenv
from database import init_db
from auth import login
from chat import render_chat

load_dotenv()
init_db()

if "username" not in st.session_state:
    login()
else:
    render_chat()
