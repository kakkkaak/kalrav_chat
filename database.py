import os
from pymongo import MongoClient
from datetime import datetime
from passlib.hash import bcrypt
from bson import ObjectId
import streamlit as st
from PIL import Image
import io

# Database configuration (Replace with actual MongoDB URI)
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

# MongoDB collections
users_coll = db["users"]
messages_coll = db["messages"]
groups_coll = db["groups"]
files_coll = db["files"]

# User functions
def get_user(username: str):
    user = users_coll.find_one({"username": username})
    return user

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

def create_user(username: str, password: str, name: str, bio: str = "", profile_picture: str = None):
    # Create a new user with hashed password
    password_hash = bcrypt.hash(password)
    user = {
        "username": username,
        "password_hash": password_hash,
        "name": name,
        "profile": {
            "bio": bio,
            "profile_picture": profile_picture,
            "show_bio": False,
            "show_picture": False
        },
        "created_at": datetime.utcnow()
    }
    users_coll.insert_one(user)

# File upload handling
def store_file(file_data: io.BytesIO, file_name: str):
    # Store files in MongoDB (could be changed to AWS S3 or another cloud storage solution)
    file_id = files_coll.insert_one({
        "filename": file_name,
        "content": file_data.getvalue(),
        "upload_time": datetime.utcnow()
    }).inserted_id
    return str(file_id)

def get_file(file_id: str):
    file = files_coll.find_one({"_id": ObjectId(file_id)})
    if file:
        return file
    return None

# Message functions
def create_message(sender: str, receiver: str = None, group: str = None, content: str = "", file: str = None):
    message_data = {
        "sender": sender,
        "content": content,
        "timestamp": datetime.utcnow(),
        "file": file  # Store file ID if any
    }
    if group:
        message_data["group"] = group
    else:
        message_data["receiver"] = receiver
    messages_coll.insert_one(message_data)

def get_private_conversation(user1: str, user2: str):
    # Fetch messages between two users
    return list(messages_coll.find({
        "$or": [
            {"sender": user1, "receiver": user2},
            {"sender": user2, "receiver": user1}
        ]
    }).sort("timestamp", 1))

def get_group_conversation(group: str):
    # Fetch all messages in a group
    return list(messages_coll.find({"group": group}).sort("timestamp", 1))

# Group management functions
def create_group(creator: str, group_name: str, invitees: list):
    group_data = {
        "name": group_name,
        "creator": creator,
        "members": [creator] + invitees,
        "created_at": datetime.utcnow()
    }
    group_id = groups_coll.insert_one(group_data).inserted_id
    
    # Send invitations to invitees (We can implement email or in-app notifications here)
    for invitee in invitees:
        send_group_invitation(invitee, group_id)
    
    return str(group_id)

def send_group_invitation(user: str, group_id: ObjectId):
    # This function would send an invitation to a user to join the group
    invitation_data = {
        "user": user,
        "group_id": group_id,
        "status": "pending",  # Default status is pending
        "sent_at": datetime.utcnow()
    }
    db["invitations"].insert_one(invitation_data)

def list_rooms(username: str):
    # Get all the groups that the user is a member of
    groups = groups_coll.find({"members": username})
    return [group["name"] for group in groups]

def get_user_groups(username: str):
    # Get all groups of a user
    groups = groups_coll.find({"members": username})
    return groups

def get_user_private_chats(username: str):
    # Get private chat partners for the user
    all_users = [user["username"] for user in users_coll.find()]
    private_chats = [u for u in all_users if u != username]
    return private_chats
