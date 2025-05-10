# database.py
import os
import io
from datetime import datetime
from pymongo import MongoClient
from passlib.hash import bcrypt
from bson import ObjectId
import streamlit as st

# ─── MongoDB Connection ─────────────────────────────────────────────────────────
MONGO_URI     = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
if not MONGO_URI or not MONGO_DB_NAME:
    raise ValueError("MONGO_URI and MONGO_DB_NAME must be set in environment")

client = MongoClient(MONGO_URI)
db     = client[MONGO_DB_NAME]

# ─── Collections ────────────────────────────────────────────────────────────────
users_coll    = db["users"]
messages_coll = db["messages"]
groups_coll   = db["groups"]
files_coll    = db["files"]
invites_coll  = db["invitations"]

# ─── Initialization ─────────────────────────────────────────────────────────────
def init_db():
    """Create indexes and seed default admin & room."""
    users_coll.create_index("username", unique=True)
    groups_coll.create_index("name", unique=True)
    invites_coll.create_index([("user", 1), ("group_id", 1)], unique=True)

    # Seed admin accounts
    for admin_u, pwd in [
        ("admin",   "bigfatboss"),
        ("Kalrav",  "bigfatboss"),
        ("Ethan",   "bigfatboss")
    ]:
        if not users_coll.find_one({"username": admin_u}):
            users_coll.insert_one({
                "username":      admin_u,
                "password_hash": bcrypt.hash(pwd),
                "name":          admin_u,
                "is_admin":      True,
                "profile": {
                    "bio": "",
                    "profile_picture": None,
                    "show_bio": False,
                    "show_picture": False
                },
                "created_at": datetime.utcnow()
            })

    # Seed default group
    if not groups_coll.find_one({"name": "3D Chat"}):
        groups_coll.insert_one({
            "name":       "3D Chat",
            "creator":    "admin",
            "members":    ["admin"],
            "is_public":  True,
            "created_at": datetime.utcnow()
        })

# ─── User CRUD ─────────────────────────────────────────────────────────────────
def create_user(username: str, password: str, name: str = "", bio: str = "", profile_picture: str = None, is_admin: bool = False):
    """Insert a new user with hashed password and blank profile."""
    pw_hash = bcrypt.hash(password)
    users_coll.insert_one({
        "username":      username,
        "password_hash": pw_hash,
        "name":          name or username,
        "is_admin":      is_admin,
        "profile": {
            "bio": bio,
            "profile_picture": profile_picture,
            "show_bio": False,
            "show_picture": False
        },
        "created_at": datetime.utcnow()
    })

def get_user(username: str):
    """Return the user document for `username` or None."""
    return users_coll.find_one({"username": username})

def check_password(stored_hash: str, password: str) -> bool:
    """Verify a plaintext password against stored bcrypt hash."""
    return bcrypt.verify(password, stored_hash)

def update_user_profile(username: str, updated_data: dict):
    """Update name, password, and profile visibility fields."""
    update_fields = {
        "name": updated_data["name"],
        "password_hash": bcrypt.hash(updated_data["password"])
    }
    # Merge profile subdocument
    update_fields.update({f"profile.{k}": v for k, v in updated_data["profile"].items()})
    users_coll.update_one({"username": username}, {"$set": update_fields})

# ─── File Storage ───────────────────────────────────────────────────────────────
def store_file(file_data: io.BytesIO, file_name: str) -> str:
    """Save raw bytes to files_coll, return stringified ObjectId."""
    res = files_coll.insert_one({
        "filename":    file_name,
        "content":     file_data.getvalue(),
        "upload_time": datetime.utcnow()
    })
    return str(res.inserted_id)

def get_file(file_id: str):
    """Retrieve a file document by its ObjectId string."""
    doc = files_coll.find_one({"_id": ObjectId(file_id)})
    return doc

# ─── Messaging ─────────────────────────────────────────────────────────────────
def create_message(sender: str, receiver: str = None, group: str = None, content: str = "", file: str = None):
    """Insert a message into messages_coll, private or group."""
    doc = {
        "sender":    sender,
        "content":   content,
        "timestamp": datetime.utcnow(),
        "file":      file  # file_id string or None
    }
    if group:
        doc["group"] = group
    else:
        doc["receiver"] = receiver
    messages_coll.insert_one(doc)

def get_private_conversation(u1: str, u2: str):
    """Return sorted list of private messages between u1 and u2."""
    return list(messages_coll.find({
        "$or": [
            {"sender": u1, "receiver": u2},
            {"sender": u2, "receiver": u1}
        ]
    }).sort("timestamp", 1))

def get_group_conversation(group_name: str):
    """Return sorted list of messages for a given group."""
    return list(messages_coll.find({"group": group_name}).sort("timestamp", 1))

# ─── Group Management ───────────────────────────────────────────────────────────
def list_rooms(username: str) -> list:
    """Return list of group names the user belongs to."""
    return [g["name"] for g in groups_coll.find({"members": username})]

def user_group_count(username: str) -> int:
    """Count how many non-public groups the user has created."""
    return groups_coll.count_documents({"creator": username, "is_public": False})

def create_group(name: str, creator: str, invitees: list = None):
    """Create a new group, add creator + invitees to members, send invites."""
    invitees = invitees or []
    if user_group_count(creator) >= 1 and not st.session_state.get("is_admin", False):
        raise ValueError("You can only create one custom group")
    group_doc = {
        "name":       name,
        "creator":    creator,
        "members":    [creator] + invitees,
        "is_public":  False,
        "created_at": datetime.utcnow()
    }
    res = groups_coll.insert_one(group_doc)
    # Send invitations
    for u in invitees:
        send_group_invitation(u, res.inserted_id)
    return str(res.inserted_id)

def send_group_invitation(user: str, group_id: ObjectId):
    """Insert an invitation record; status pending."""
    invites_coll.insert_one({
        "user":     user,
        "group_id": group_id,
        "status":   "pending",
        "sent_at":  datetime.utcnow()
    })

# ─── Sidebar Helpers ───────────────────────────────────────────────────────────
def get_user_groups(username: str):
    """Return cursor of groups the user belongs to."""
    return groups_coll.find({"members": username})

def get_user_private_chats(username: str) -> list:
    """Return list of other usernames for private chats."""
    return [u["username"] for u in users_coll.find() if u["username"] != username]
