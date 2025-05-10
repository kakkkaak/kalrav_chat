import os, io
from datetime import datetime
from pymongo import MongoClient
from passlib.hash import bcrypt
from bson import ObjectId

MONGO_URI     = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
client        = MongoClient(MONGO_URI)
db            = client[MONGO_DB_NAME]

users_coll    = db["users"]
msgs_coll     = db["messages"]
groups_coll   = db["groups"]
files_coll    = db["files"]
invites_coll  = db["invitations"]
notes_coll    = db["notifications"]

def init_db():
    users_coll.create_index("username", unique=True)
    groups_coll.create_index("name", unique=True)
    notes_coll.create_index([("user",1),("read",1)])
    # seed admin & default group if needed...

def create_user(username, password, name="", is_admin=False):
    pw = bcrypt.hash(password)
    users_coll.insert_one({
        "username":username,"password_hash":pw,
        "name":name or username,"is_admin":is_admin,
        "profile":{"bio":"","pic":None,"show_bio":False,"show_pic":False},
        "notif_check":datetime.utcnow(),"created_at":datetime.utcnow()
    })

def get_user(username):
    return users_coll.find_one({"username":username})

def check_password(h,p):
    return bcrypt.verify(p,h)

def update_user_profile(username, name, password, profile):
    upd = {"name":name}
    if password:
        upd["password_hash"]=bcrypt.hash(password)
    for k,v in profile.items():
        upd[f"profile.{k}"]=v
    users_coll.update_one({"username":username},{"$set":upd})

def store_file(buf: io.BytesIO, filename: str) -> str:
    res = files_coll.insert_one({"filename":filename,"content":buf.getvalue(),"ts":datetime.utcnow()})
    return str(res.inserted_id)

def get_file(file_id: str):
    return files_coll.find_one({"_id":ObjectId(file_id)})

def create_message(sender, receiver=None, group=None, content="", file=None):
    doc={"sender":sender,"content":content,"ts":datetime.utcnow(),"file":file}
    if group:
        doc["group"]=group
    else:
        doc["receiver"]=receiver
        # notification
        notes_coll.insert_one({"user":receiver,"read":False,"ts":datetime.utcnow(),"msg":doc})
    msgs_coll.insert_one(doc)

def get_private_conversation(u1,u2):
    return list(msgs_coll.find({
        "$or":[{"sender":u1,"receiver":u2},{"sender":u2,"receiver":u1}]
    }).sort("ts",1))

def get_group_conversation(group_name):
    return list(msgs_coll.find({"group":group_name}).sort("ts",1))

def get_user_private_list(username):
    return [u["username"] for u in users_coll.find({"username":{"$ne":username}})]

def get_user_groups(username):
    return list(groups_coll.find({"members":username}))

def create_group(name, creator, invitees):
    doc={"name":name,"creator":creator,"members":[creator]+invitees,"is_public":False,"ts":datetime.utcnow()}
    res=groups_coll.insert_one(doc)
    for u in invitees:
        invites_coll.insert_one({"user":u,"group_id":res.inserted_id,"status":"pending","ts":datetime.utcnow()})
    return str(res.inserted_id)

def list_rooms(username):
    return [g["name"] for g in get_user_groups(username)]

def get_notifications(username):
    return list(notes_coll.find({"user":username,"read":False}).sort("ts",1))

def mark_notifications_read(username):
    notes_coll.update_many({"user":username,"read":False},{"$set":{"read":True}})

# ─── Group helper: count non-public groups a user has created ───────────────
def user_group_count(username: str) -> int:
    return groups_coll.count_documents({
        "creator": username,
        "is_public": False
    })

# ─── Invitation helper ──────────────────────────────────────────────────────
def invite_user_to_group(group_name: str, invited_user: str):
    invites_coll.insert_one({
        "group": group_name,
        "invited_user": invited_user,
        "status": "pending",
        "ts": datetime.utcnow()
    })

# ─── Profile update helper ─────────────────────────────────────────────────
def update_profile(username: str, profile: dict, visible_fields: list):
    """
    Overwrite the 'profile' subdocument and 'visible_fields' list
    """
    users_coll.update_one(
        {"username": username},
        {"$set": {
            "profile": profile,
            "visible_fields": visible_fields
        }}
    )

