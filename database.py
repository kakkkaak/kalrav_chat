import os, io
from datetime import datetime
from pymongo import MongoClient
from passlib.hash import bcrypt
from bson import ObjectId
import logging

# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

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
    try:
        users_coll.create_index("username", unique=True)
        groups_coll.create_index("name", unique=True)
        notes_coll.create_index([("user", 1), ("read", 1)])
        messages_coll.create_index([("content", "text")])
        messages_coll.create_index([("timestamp", 1)])

        admin_u = os.getenv("ADMIN_USERNAME")
        admin_p = os.getenv("ADMIN_PASSWORD")
        if not users_coll.find_one({"username": admin_u}):
            users_coll.insert_one({
                "username": admin_u,
                "password_hash": bcrypt.hash(admin_p),
                "is_admin": True,
                "profile": {"name": admin_u, "bio": "", "pic": None, "show_bio": False, "show_pic": False, "display_name": admin_u, "avatar": "👑"},
                "visible_fields": [],
                "settings": {"theme": "light", "background_color": "#f0f0f0"},
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
    except Exception as e:
        logging.error(f"Error initializing database: {e}")
        raise

# User management
def create_user(username, password, profile):
    try:
        pw = bcrypt.hash(password)
        profile["display_name"] = profile.get("display_name", profile.get("name", username))
        profile["avatar"] = profile.get("avatar", "👤")
        users_coll.insert_one({
            "username": username,
            "password_hash": pw,
            "is_admin": False,
            "profile": profile,
            "visible_fields": list(profile.keys()),
            "settings": {"theme": "light", "background_color": "#f0f0f0"},
            "created_at": datetime.utcnow()
        })
    except Exception as e:
        logging.error(f"Error creating user {username}: {e}")
        raise

def get_user(username):
    try:
        return users_coll.find_one({"username": username})
    except Exception as e:
        logging.error(f"Error fetching user {username}: {e}")
        raise

def check_password(h, p):
    try:
        return bcrypt.verify(p, h)
    except Exception as e:
        logging.error(f"Error checking password: {e}")
        raise

def update_profile(username, profile, visible_fields):
    try:
        profile["display_name"] = profile.get("display_name", profile.get("name", username))
        profile["avatar"] = profile.get("avatar", "👤")
        users_coll.update_one(
            {"username": username},
            {"$set": {"profile": profile, "visible_fields": visible_fields}}
        )
    except Exception as e:
        logging.error(f"Error updating profile for {username}: {e}")
        raise

def update_settings(username, settings):
    try:
        users_coll.update_one(
            {"username": username},
            {"$set": {"settings": settings}}
        )
    except Exception as e:
        logging.error(f"Error updating settings for {username}: {e}")
        raise

def delete_user(username):
    try:
        # Prevent admin deletion
        user = users_coll.find_one({"username": username})
        if user.get("is_admin", False):
            return False
        # Delete user data
        users_coll.delete_one({"username": username})
        messages_coll.delete_many({"$or": [{"sender": username}, {"receiver": username}]})
        groups_coll.update_many({"members": username}, {"$pull": {"members": username}})
        groups_coll.delete_many({"creator": username})
        invites_coll.delete_many({"$or": [{"invited_user": username}, {"group": {"$in": groups_coll.distinct("name", {"creator": username})}}]})
        notes_coll.delete_many({"user": username})
        files_coll.delete_many({"_id": {"$in": messages_coll.distinct("file_id", {"sender": username})}})
        return True
    except Exception as e:
        logging.error(f"Error deleting user {username}: {e}")
        raise

# File storage
def store_file(buf: io.BytesIO, name: str) -> str:
    try:
        res = files_coll.insert_one({"name": name, "content": buf.getvalue(), "ts": datetime.utcnow()})
        return str(res.inserted_id)
    except Exception as e:
        logging.error(f"Error storing file {name}: {e}")
        raise

def get_file(file_id: str):
    try:
        return files_coll.find_one({"_id": ObjectId(file_id)})
    except Exception as e:
        logging.error(f"Error fetching file {file_id}: {e}")
        raise

# Messaging
def create_message(sender, receiver=None, group=None, content="", file_id=None):
    try:
        doc = {
            "sender": sender,
            "content": content,
            "timestamp": datetime.utcnow(),
            "file_id": file_id,
            "read": False,
            "reactions": {}
        }
        if receiver:
            doc["receiver"] = receiver
            notes_coll.insert_one({"user": receiver, "msg": doc, "read": False, "ts": doc["timestamp"]})
        if group:
            doc["group"] = group
            group_doc = groups_coll.find_one({"name": group})
            if group_doc:
                for member in group_doc["members"]:
                    if member != sender:
                        notes_coll.insert_one({"user": member, "msg": doc, "read": False, "ts": doc["timestamp"]})
            else:
                logging.error(f"Group {group} not found")
                raise ValueError(f"Group {group} not found")
        res = messages_coll.insert_one(doc)
        return str(res.inserted_id)
    except Exception as e:
        logging.error(f"Error creating message from {sender} to {receiver or group}: {e}")
        raise

def get_private_conversation(u1, u2, skip=0, limit=50):
    try:
        return list(messages_coll.find(
            {"$or": [{"sender": u1, "receiver": u2}, {"sender": u2, "receiver": u1}]}
        ).sort("timestamp", -1).skip(skip).limit(limit))[::-1]
    except Exception as e:
        logging.error(f"Error fetching private conversation between {u1} and {u2}: {e}")
        raise

def get_group_conversation(group_name, skip=0, limit=50):
    try:
        return list(messages_coll.find({"group": group_name}).sort("timestamp", -1).skip(skip).limit(limit))[::-1]
    except Exception as e:
        logging.error(f"Error fetching group conversation for {group_name}: {e}")
        raise

def get_new_private_messages(u1, u2, last_timestamp):
    try:
        return list(messages_coll.find({
            "$or": [{"sender": u1, "receiver": u2}, {"sender": u2, "receiver": u1}],
            "timestamp": {"$gt": last_timestamp}
        }).sort("timestamp", 1))
    except Exception as e:
        logging.error(f"Error fetching new private messages between {u1} and {u2}: {e}")
        raise

def get_new_group_messages(group_name, last_timestamp):
    try:
        return list(messages_coll.find({
            "group": group_name,
            "timestamp": {"$gt": last_timestamp}
        }).sort("timestamp", 1))
    except Exception as e:
        logging.error(f"Error fetching new group messages for {group_name}: {e}")
        raise

def delete_message(message_id, sender):
    try:
        messages_coll.delete_one({"_id": ObjectId(message_id), "sender": sender})
    except Exception as e:
        logging.error(f"Error deleting message {message_id} by {sender}: {e}")
        raise

def edit_message(message_id, sender, new_content):
    try:
        messages_coll.update_one(
            {"_id": ObjectId(message_id), "sender": sender},
            {"$set": {"content": new_content, "edited": True, "edited_at": datetime.utcnow()}}
        )
    except Exception as e:
        logging.error(f"Error editing message {message_id} by {sender}: {e}")
        raise

def mark_messages_read(username, partner):
    try:
        messages_coll.update_many(
            {"sender": partner, "receiver": username, "read": False},
            {"$set": {"read": True}}
        )
        notes_coll.update_many(
            {"user": username, "msg.sender": partner, "read": False},
            {"$set": {"read": True}}
        )
    except Exception as e:
        logging.error(f"Error marking messages read for {username} from {partner}: {e}")
        raise

def add_reaction(message_id, username, reaction):
    try:
        messages_coll.update_one(
            {"_id": ObjectId(message_id)},
            {"$inc": {f"reactions.{reaction}": 1}}
        )
    except Exception as e:
        logging.error(f"Error adding reaction to message {message_id} by {username}: {e}")
        raise

def search_messages(query, username, p=None, g=None):
    try:
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
    except Exception as e:
        logging.error(f"Error searching messages for {username}: {e}")
        raise

# Groups
def list_rooms(username):
    try:
        return list(groups_coll.find({
            "$or": [
                {"is_public": True},
                {"creator": username},
                {"members": username}
            ]
        }))
    except Exception as e:
        logging.error(f"Error listing rooms for {username}: {e}")
        raise

def get_user_groups(username):
    try:
        return list(groups_coll.find({"members": username}))
    except Exception as e:
        logging.error(f"Error fetching user groups for {username}: {e}")
        raise

def user_group_count(username):
    try:
        return groups_coll.count_documents({"creator": username})
    except Exception as e:
        logging.error(f"Error counting user groups for {username}: {e}")
        raise

def create_group(name, creator):
    try:
        groups_coll.insert_one({
            "name": name,
            "creator": creator,
            "members": [creator],
            "is_public": False,
            "created_at": datetime.utcnow()
        })
    except Exception as e:
        logging.error(f"Error creating group {name} by {creator}: {e}")
        raise

def invite_user_to_group(group, user):
    try:
        invites_coll.insert_one({"group": group, "invited_user": user, "status": "pending", "ts": datetime.utcnow()})
    except Exception as e:
        logging.error(f"Error inviting {user} to group {group}: {e}")
        raise

def get_user_invites(username):
    try:
        return list(invites_coll.find({"invited_user": username}))
    except Exception as e:
        logging.error(f"Error fetching invites for {username}: {e}")
        raise

def accept_invite(username, group_name):
    try:
        groups_coll.update_one({"name": group_name}, {"$addToSet": {"members": username}})
        invites_coll.delete_one({"group": group_name, "invited_user": username})
    except Exception as e:
        logging.error(f"Error accepting invite for {username} to {group_name}: {e}")
        raise

# Notifications
def get_notifications(username):
    try:
        return list(notes_coll.find({"user": username, "read": False}))
    except Exception as e:
        logging.error(f"Error fetching notifications for {username}: {e}")
        raise

def mark_notifications_read(username):
    try:
        notes_coll.update_many({"user": username, "read": False}, {"$set": {"read": True}})
    except Exception as e:
        logging.error(f"Error marking notifications read for {username}: {e}")
        raise