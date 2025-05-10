# database.py
import os
from pymongo import MongoClient
from datetime import datetime
from passlib.hash import bcrypt
from bson import ObjectId
import streamlit as st
from PIL import Image
import io

# Connection and collections setup as before...

# User functions
def update_user_profile(username: str, updated_data: dict):
    # Update the user's details, including the profile section
    user = get_user(username)
    if user:
        user_data = { 
            "name": updated_data["name"],
            "password_hash": bcrypt.hash(updated_data["password"]),
            "profile": updated_data["profile"]
        }
        users_coll.update_one({"username": username}, {"$set": user_data})
    else:
        raise ValueError("User not found.")

def store_file(file_data: io.BytesIO, file_name: str):
    # Store files in MongoDB or AWS S3, etc.
    file_collection = db["files"]
    file_id = file_collection.insert_one({
        "filename": file_name,
        "content": file_data.getvalue(),
        "upload_time": datetime.utcnow()
    }).inserted_id
    return str(file_id)

# Message functions (including file support)
def create_message(sender: str, receiver: str = None, group: str = None, content: str = "", file: str = None):
    doc = {
        "sender":    sender,
        "content":   content,
        "timestamp": datetime.utcnow(),
        "file":      file  # Store file ID if any
    }
    if group:
        doc["group"] = group
    else:
        doc["receiver"] = receiver
    messages_coll.insert_one(doc)

# Helper functions for getting conversations remain the same...
