
from datetime import datetime
from flask_login import UserMixin
from .db import db


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    # Username of staff
    name = db.Column(db.String(120), nullable=False)
    # Designation: clerk, officer, records assistant, admin etc
    designation = db.Column(db.String(120), nullable=False)
    # Login credentials
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    # Role: "admin" or "staff"
    role = db.Column(db.String(20), default="staff", nullable=False)
    transactions = db.relationship("FileTransaction", backref="user", lazy=True, foreign_keys="FileTransaction.user_id")
    
    def is_admin(self):
        return self.role == "admin"
    
    
class FileRecord(db.Model):
    __tablename__ = "files"
    id = db.Column(db.Integer, primary_key=True)
    # Identifier used in government institutions
    file_number = db.Column(db.String(100), unique=True, nullable=False)
    # Optional description
    title = db.Column(db.String(200), nullable=True)
    department = db.Column(db.String(120), nullable=True)
    # File status
    is_issued = db.Column(db.Boolean, default=False)
    # Relationship to movement records
    transactions = db.relationship("FileTransaction", backref="file", lazy=True)
    
    
    
class FileTransaction(db.Model):

    __tablename__ = "file_transactions"
    id = db.Column(db.Integer, primary_key=True)
    # Link file
    file_id = db.Column(db.Integer, db.ForeignKey("files.id"), nullable=False)
    # Person taking the file
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    # Time of taking
    checkout_time = db.Column(db.DateTime, default=datetime.utcnow,  nullable=False)
    # Time of returning
    return_time = db.Column(db.DateTime, nullable=True)
    # Admin authorization fields
    issued_by_admin_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    returned_to_admin_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    # Remarks
    purpose = db.Column(db.String(250))
    comments = db.Column(db.String(250))

    issued_by = db.relationship("User", foreign_keys=[issued_by_admin_id])
    returned_to = db.relationship("User", foreign_keys=[returned_to_admin_id])


class ChatRoom(db.Model):
    __tablename__ = "chat_rooms"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)

    # Optional: link chatroom to a file
    file_id = db.Column(db.Integer, db.ForeignKey("files.id"), nullable=True)

    is_private = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    messages = db.relationship("ChatMessage", backref="room", lazy=True)
    members = db.relationship("ChatRoomMember", backref="room", lazy=True)

    file = db.relationship("FileRecord")


class ChatRoomMember(db.Model):
    __tablename__ = "chat_room_members"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("chat_rooms.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    added_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_read_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", foreign_keys=[user_id])
    added_by = db.relationship("User", foreign_keys=[added_by_id])


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"

    id = db.Column(db.Integer, primary_key=True)

    room_id = db.Column(db.Integer, db.ForeignKey("chat_rooms.id"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    message = db.Column(db.Text)  # Made nullable for media-only messages
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Media file fields
    image_filename = db.Column(db.String(255))
    voice_filename = db.Column(db.String(255))
    video_filename = db.Column(db.String(255))

    sender = db.relationship("User")


"""
Log:

File movements

Chat deletions

Admin overrides"""

class AuditLog(db.Model):
    __tablename__ = "audit_log"
    
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(200))
    user_id = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
