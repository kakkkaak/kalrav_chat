import os, io
from datetime import datetime
from pymongo import MongoClient
from passlib.hash import bcrypt
from bson import ObjectId
import bleach

# Load environment variables
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

# Collections
users_coll = db["users"]
messages_coll = db["messages"]
groups_coll = db["groups"]
invites_coll = db["invitations"]
files_coll = db["files"]
notes_coll = db["notifications"]

def init_db():
    # Create indexes for efficient querying
    users_coll.create_index("username", unique=True)
    groups_coll.create_index("name", unique=True)
    notes_coll.create_index([("user", 1), ("read", 1)])
    messages_coll.create_index([("sender", 1), ("receiver", 1)])
    messages_coll.create_index([("group", 1)])
    groups_coll.create_index([("members", 1)])
    messages_coll.create_index([("content", "text")])  # For text search

    # Create admin user if not exists
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

    # Create default public group if not exists
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
        "username": bleach.clean(username),
        "password_hash": pw,
        "is_admin": False,
        "profile": {k: bleach.clean(v) if isinstance(v, str) else v for k, v in profile.items()},
        "visible_fields": list(profile.keys()),
        "created_at": datetime.utcnow()
    })

def get_user(username):
    return users_coll.find_one({"username": username})

def check_password(h, p):
    return bcrypt.verify(p, h)

def update_profile(username, profile, visible_fields):
    profile = {k: bleach.clean(v) if isinstance(v, str) else v for k, v in profile.items()}
    users_coll.update_one(
        {"username": username},
        {"$set": {"profile": profile, "visible_fields": visible_fields}}
    )

def update_password(username, new_password):
    hashed = bcrypt.hash(new_password)
    users_coll.update_one({"username": username}, {"$set": {"password_hash": hashed}})

# File storage with validation
def store_file(buf: io.BytesIO, name: str) -> str:
    if not name.lower().endswith(('.png', '.jpg', '.jpeg', '.pdf')):
        raise ValueError("Only PNG, JPG, JPEG, and PDF files are allowed")
    if buf.getbuffer().nbytes > 5 * 1024 * 1024:  # 5MB limit
        raise ValueError("File size exceeds 5MB limit")
    res = files_coll.insert_one({"name": name, "content": buf.getvalue(), "ts": datetime.utcnow()})
    return str(res.inserted_id)

def get_file(file_id: str):
    return files_coll.find_one({"_id": ObjectId(file_id)})

# Messaging with sanitization and read status
def create_message(sender, receiver=None, group=None, content="", file_id=None):
    content = bleach.clean(content)
    doc = {"sender": sender, "content": content, "timestamp": datetime.utcnow(), "file_id": file_id, "read": False if receiver else True}
    if receiver:
        doc["receiver"] = receiver
        notes_coll.insert_one({"user": receiver, "msg": doc, "read": False, "ts": datetime.utcnow()})
    if group:
        doc["group"] = group
    messages_coll.insert_one(doc)

def get_private_conversation(u1, u2, skip=0, limit=50, since=None):
    query = {"$or": [{"sender": u1, "receiver": u2}, {"sender": u2, "receiver": u1}]}
    if since:
        query["timestamp"] = {"$gt": since}
    return list(messages_coll.find(query).sort("timestamp", 1).skip(skip).limit(limit))

def get_group_conversation(group_name, skip=0, limit=50):
    return list(messages_coll.find({"group": group_name}).sort("timestamp", 1).skip(skip).limit(limit))

def delete_message(message_id):
    messages_coll.delete_one({"_id": ObjectId(message_id)})

def edit_message(message_id, new_content):
    message = messages_coll.find_one({"_id": ObjectId(message_id)})
    if message:
        sent_time = message["timestamp"]
        if (datetime.utcnow() - sent_time).total_seconds() > 300:  # 5 minutes
            raise ValueError("Message edit time limit exceeded")
        messages_coll.update_one(
            {"_id": ObjectId(message_id)},
            {"$set": {"content": bleach.clean(new_content), "edited": True}}
        )
    else:
        raise ValueError("Message not found")

def mark_messages_read(u, p):
    messages_coll.update_many(
        {"sender": p, "receiver": u, "read": False},
        {"$set": {"read": True}}
    )

def search_messages(query, u, p=None, g=None):
    if p:
        return list(messages_coll.find(
            {"$or": [{"sender": u, "receiver": p}, {"sender": p, "receiver": u}], "$text": {"$search": query}}
        ).sort([("score", {"$meta": "textScore"})]))
    elif g:
        return list(messages_coll.find({"group": g, "$text": {"$search": query}}).sort([("score", {"$meta": "textScore"})]))

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
    return groups_coll.count_documents({"creator": username})

def create_group(name, creator):
    name = bleach.clean(name)
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

def remove_member_from_group(group_name, member):
    groups_coll.update_one({"name": group_name}, {"$pull": {"members": member}})

# Notifications
def get_notifications(username):
    return list(notes_coll.find({"user": username, "read": False}))

def mark_notifications_read(username):
    notes_coll.update_many({"user": username, "read": False}, {"$set": {"read": True}})