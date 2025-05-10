import os, io
from datetime import datetime
from pymongo import MongoClient
from passlib.hash import bcrypt
from bson import ObjectId

# Load env
MONGO_URI     = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
client        = MongoClient(MONGO_URI)
db            = client[MONGO_DB_NAME]

# Collections
users_coll    = db["users"]
messages_coll = db["messages"]
groups_coll   = db["groups"]
invites_coll  = db["invitations"]
files_coll    = db["files"]
notes_coll    = db["notifications"]

def init_db():
    users_coll.create_index("username", unique=True)
    groups_coll.create_index("name", unique=True)
    notes_coll.create_index([("user", 1), ("read", 1)])
    messages_coll.create_index([("content", "text")])  # For search functionality

    admin_u = os.getenv("ADMIN_USERNAME")
    admin_p = os.getenv("ADMIN_PASSWORD")
    if not users_coll.find_one({"username": admin_u}):
        users_coll.insert_one({
            "username": admin_u,
            "password_hash": bcrypt.hash(admin_p),
            "is_admin": True,
            "profile": {"name": admin_u, "bio": "", "pic": None, "show_bio": False, "show_pic": False},
            "visible_fields": [],
            "created_at": datetime.utcnow()
        })

    if not groups_coll.find_one({"name": "3D Chat"}):
        groups_coll.insert_one({
            "name": "3D Chat",
            "creator": admin_u,
            "members": [admin_u],
            "is_public": True,
            "created_at": datetime.utcnow()
        })

# User management
def create_user(username, password, profile):
    pw = bcrypt.hash(password)
    users_coll.insert_one({
        "username": username,
        "password_hash": pw,
        "is_admin": False,
        "profile": profile,
        "visible_fields": list(profile.keys()),
        "created_at": datetime.utcnow()
    })

def get_user(username):
    return users_coll.find_one({"username": username})

def check_password(h, p):
    return bcrypt.verify(p, h)

def update_profile(username, profile, visible_fields):
    users_coll.update_one(
        {"username": username},
        {"$set": {"profile": profile, "visible_fields": visible_fields}}
    )

# File storage
def store_file(buf: io.BytesIO, name: str) -> str:
    res = files_coll.insert_one({"name": name, "content": buf.getvalue(), "ts": datetime.utcnow()})
    return str(res.inserted_id)

def get_file(file_id: str):
    return files_coll.find_one({"_id": ObjectId(file_id)})

# Messaging
def create_message(sender, receiver=None, group=None, content="", file_id=None):
    doc = {
        "sender": sender,
        "content": content,
        "timestamp": datetime.utcnow(),
        "file_id": file_id,
        "read": False  # Default for private messages
    }
    if receiver:
        doc["receiver"] = receiver
        notes_coll.insert_one({"user": receiver, "msg": doc, "read": False, "ts": datetime.utcnow()})
    if group:
        doc["group"] = group
    messages_coll.insert_one(doc)

def get_private_conversation(u1, u2, skip=0, limit=50):
    return list(messages_coll.find(
        {"$or": [{"sender": u1, "receiver": u2}, {"sender": u2, "receiver": u1}]}
    ).sort("timestamp", -1).skip(skip).limit(limit))[::-1]  # Reverse for chronological order

def get_group_conversation(group_name, skip=0, limit=50):
    return list(messages_coll.find({"group": group_name}).sort("timestamp", -1).skip(skip).limit(limit))[::-1]

def delete_message(message_id, sender):
    messages_coll.delete_one({"_id": ObjectId(message_id), "sender": sender})

def edit_message(message_id, sender, new_content):
    messages_coll.update_one(
        {"_id": ObjectId(message_id), "sender": sender},
        {"$set": {"content": new_content, "edited": True, "edited_at": datetime.utcnow()}}
    )

def mark_messages_read(username, partner):
    messages_coll.update_many(
        {"sender": partner, "receiver": username, "read": False},
        {"$set": {"read": True}}
    )

def search_messages(query, username, p=None, g=None):
    if p:
        return list(messages_coll.find(
            {
                "$or": [{"sender": username, "receiver": p}, {"sender": p, "receiver": username}],
                "$text": {"$search": query}
            }
        ).sort("timestamp", -1))
    elif g:
        return list(messages_coll.find(
            {"group": g, "$text": {"$search": query}}
        ).sort("timestamp", -1))
    return []

# Groups
def list_rooms(username):
    return list(groups_coll.find({
        "$or": [
            {"is_public": True},
            {"creator": username},
            {"members": username}
        ]
    }))

def get_user_groups(username):
    return list(groups_coll.find({"members": username}))

def user_group_count(username):
    """Count how many groups the user created"""
    return groups_coll.count_documents({"creator": username})

def create_group(name, creator):
    groups_coll.insert_one({
        "name": name,
        "creator": creator,
        "members": [creator],
        "is_public": False,
        "created_at": datetime.utcnow()
    })

def invite_user_to_group(group, user):
    invites_coll.insert_one({"group": group, "invited_user": user, "status": "pending", "ts": datetime.utcnow()})

def get_user_invites(username):
    return list(invites_coll.find({"invited_user": username}))

def accept_invite(username, group_name):
    groups_coll.update_one({"name": group_name}, {"$addToSet": {"members": username}})
    invites_coll.delete_one({"group": group_name, "invited_user": username})

# Notifications
def get_notifications(username):
    return list(notes_coll.find({"user": username, "read": False}))

def mark_notifications_read(username):
    notes_coll.update_many({"user": username, "read": False}, {"$set": {"read": True}})