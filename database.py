# database.py
import os
from pymongo import MongoClient
from datetime import datetime
from passlib.hash import bcrypt
import streamlit as st

# Connection
MONGO_URI     = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
client        = MongoClient(MONGO_URI)
db            = client[MONGO_DB_NAME]

# Collections
users_coll    = db["users"]
messages_coll = db["messages"]
groups_coll   = db["groups"]

def init_db():
    # 1) Indexes
    users_coll.create_index("username", unique=True)
    groups_coll.create_index("creator", unique=False)
    groups_coll.create_index("name", unique=True)

    # 2) Seed admin accounts
    for admin_u in [
        ("admin",   "bigfatboss"),
        ("Kalrav",  "bigfatboss"),
        ("Ethan",   "bigfatboss")
    ]:
        u, pwd = admin_u
        if not users_coll.find_one({"username": u}):
            users_coll.insert_one({
                "username":      u,
                "password_hash": bcrypt.hash(pwd),
                "is_admin":      True
            })

    # 3) Seed default room "3D Chat"
    if not groups_coll.find_one({"name": "3D Chat"}):
        groups_coll.insert_one({
            "name":       "3D Chat",
            "creator":    "admin",
            "members":    [],        # optional: track who joined
            "is_public":  True,
            "created_at": datetime.utcnow()
        })

# User functions
def create_user(username: str, password: str):
    users_coll.insert_one({
        "username":      username,
        "password_hash": bcrypt.hash(password),
        "is_admin":      False
    })

def get_user(username: str):
    return users_coll.find_one({"username": username})

def check_password(stored_hash: str, password: str) -> bool:
    return bcrypt.verify(password, stored_hash)

# Message functions (private and group)
def create_message(sender: str, receiver: str=None, group: str=None, content: str=""):
    doc = {
        "sender":    sender,
        "content":   content,
        "timestamp": datetime.utcnow()
    }
    if group:
        doc["group"] = group
    else:
        doc["receiver"] = receiver
    messages_coll.insert_one(doc)

def get_private_conversation(u1: str, u2: str):
    return list(messages_coll.find({
        "$or": [
            {"sender": u1, "receiver": u2},
            {"sender": u2, "receiver": u1}
        ]
    }).sort("timestamp", 1))

def get_group_conversation(group_name: str):
    return list(messages_coll.find({
        "group": group_name
    }).sort("timestamp", 1))

# Group functions
def get_all_groups():
    return list(groups_coll.find({"$or": [
        {"is_public": True},
        {"creator":   st.session_state.username}
    ]}))

def user_group_count(username: str) -> int:
    return groups_coll.count_documents({"creator": username, "is_public": False})

def create_group(name: str, creator: str):
    if user_group_count(creator) >= 1:
        raise ValueError("User already has one custom group")
    groups_coll.insert_one({
        "name":       name,
        "creator":    creator,
        "members":    [creator],
        "is_public":  False,
        "created_at": datetime.utcnow()
    })

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")

if not MONGO_URI or not MONGO_DB_NAME:
    raise ValueError("MONGO_URI or MONGO_DB_NAME is not set in the environment variables.")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

