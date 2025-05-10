# database.py
import os, io
from datetime import datetime
from pymongo import MongoClient
from passlib.hash import bcrypt
from bson import ObjectId

# ── Connection ────────────────────────────────────────────────────────────────
MONGO_URI     = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
if not MONGO_URI or not MONGO_DB_NAME:
    raise ValueError("MONGO_URI and MONGO_DB_NAME must be set in .env")

client      = MongoClient(MONGO_URI)
db          = client[MONGO_DB_NAME]
users_coll  = db["users"]
msgs_coll   = db["messages"]
groups_coll = db["groups"]
files_coll  = db["files"]
invites_coll= db["invitations"]
notes_coll  = db["notifications"]

def init_db():
    users_coll.create_index("username", unique=True)
    groups_coll.create_index("name", unique=True)
    notes_coll.create_index([("user",1),("read",1)])
    # seed default admin & room...
    # (left as before)

# ── User CRUD & Auth ──────────────────────────────────────────────────────────
def create_user(username, password, name="", is_admin=False):
    pw = bcrypt.hash(password)
    users_coll.insert_one({
        "username": username,
        "password_hash": pw,
        "name": name or username,
        "is_admin": is_admin,
        "profile": {"bio":"", "pic":None, "show_bio":False, "show_pic":False},
        "notif_check": datetime.utcnow(),
        "created_at": datetime.utcnow()
    })

def get_user(username):
    return users_coll.find_one({"username":username})

def check_password(hash_, pwd):
    return bcrypt.verify(pwd, hash_)

def update_user_profile(username, data):
    # data keys: name, password, profile dict
    upd = {"name":data["name"], "password_hash":bcrypt.hash(data["password"])}
    for k,v in data["profile"].items():
        upd[f"profile.{k}"]=v
    users_coll.update_one({"username":username},{"$set":upd})

# ── File Storage ───────────────────────────────────────────────────────────────
def store_file(fbuf: io.BytesIO, fname: str) -> str:
    iid = files_coll.insert_one({"filename":fname,"content":fbuf.getvalue(),"ts":datetime.utcnow()}).inserted_id
    return str(iid)

def get_file(fid: str):
    return files_coll.find_one({"_id":ObjectId(fid)})

# ── Messaging ─────────────────────────────────────────────────────────────────
def create_message(sender, receiver=None, group=None, content="", file=None):
    doc={"sender":sender,"content":content,"ts":datetime.utcnow(),"file":file}
    if group: doc["group"]=group
    else:     doc["receiver"]=receiver
    msgs_coll.insert_one(doc)
    if receiver:
        # add notification
        notes_coll.insert_one({"user":receiver,"msg_id":doc, "read":False,"ts":datetime.utcnow()})

def get_private_conversation(u1,u2):
    return list(msgs_coll.find({"$or":[{"sender":u1,"receiver":u2},{"sender":u2,"receiver":u1}]}).sort("ts",1))

def get_group_conversation(g):
    return list(msgs_coll.find({"group":g}).sort("ts",1))

# ── Group Management ───────────────────────────────────────────────────────────
def list_rooms(username):
    return [g["name"] for g in groups_coll.find({"members":username})]

def get_user_groups(username):
    return list(groups_coll.find({"members":username}))

def create_group(name,creator,invitees):
    doc={"name":name,"creator":creator,"members":[creator]+invitees,"ts":datetime.utcnow()}
    gid=groups_coll.insert_one(doc).inserted_id
    for u in invitees:
        invites_coll.insert_one({"user":u,"group_id":gid,"status":"pending","ts":datetime.utcnow()})
    return str(gid)

# ── Invitations & Notifications ───────────────────────────────────────────────
def get_invitations(username):
    return list(invites_coll.find({"user":username,"status":"pending"}))

def accept_invite(username, group_id):
    invites_coll.update_one({"user":username,"group_id":ObjectId(group_id)},{"$set":{"status":"accepted"}})
    groups_coll.update_one({"_id":ObjectId(group_id)},{"$push":{"members":username}})

def get_notifications(username):
    notes = list(notes_coll.find({"user":username,"read":False}).sort("ts",1))
    return notes

def mark_notifications_read(username):
    notes_coll.update_many({"user":username,"read":False},{"$set":{"read":True}})
