from flask_socketio import join_room
from flask_login import current_user
from app.models import ChatMessage, FileTransaction, FileRecord, ChatRoomMember, User
from app import db, socketio
import os

def update_notifications_for_room(room_id, sender_id):
    """Update notification badges for all room members except sender"""
    room_members = ChatRoomMember.query.filter_by(room_id=room_id).all()
    for member in room_members:
        if member.user_id != sender_id:
            # Calculate total unread count across all rooms for this member
            total_unread = 0
            user_memberships = ChatRoomMember.query.filter_by(user_id=member.user_id).all()
            
            for membership in user_memberships:
                unread_count = ChatMessage.query.filter(
                    ChatMessage.room_id == membership.room_id,
                    ChatMessage.timestamp > membership.last_read_at
                ).count()
                total_unread += unread_count

            # Emit notification update to this user
            socketio.emit("notification_update", {
                "total_unread": total_unread,
                "room_id": room_id
            }, room=f"user_{member.user_id}")

# Join chat room
@socketio.on("join")
def join(data):
    join_room(str(data["room_id"]))

# Join user-specific room for notifications
@socketio.on("join_user_room")
def join_user_room(data):
    join_room(f"user_{data['user_id']}")

# Send chat message
@socketio.on("send_message")
def send_message(data):
    msg = ChatMessage(
        room_id=data["room_id"],
        sender_id=current_user.id,
        message=data.get("message") if data.get("message") and data.get("message").strip() else None,
        image_filename=data.get("image_filename"),
        voice_filename=data.get("voice_filename")
    )
    db.session.add(msg)
    db.session.commit()

    # Emit to room with multimedia support
    emit_data = {
        "sender": current_user.name,
        "message": msg.message,
        "image_filename": msg.image_filename,
        "voice_filename": msg.voice_filename,
        "timestamp": msg.timestamp.strftime('%H:%M')
    }
    socketio.emit("receive_message", emit_data, room=str(data["room_id"]))

    # Emit to admin dashboard
    socketio.emit("admin_update", {
        "type": "chat",
        "room_id": data["room_id"],
        "sender": current_user.name,
        "message": msg.message or "[Media message]"
    }, broadcast=True)

    # Update notifications for room members
    update_notifications_for_room(data["room_id"], current_user.id)

# File checkout/return live update
def emit_file_update(tx, action):
    socketio.emit("admin_update", {
        "type": "file",
        "file_number": tx.file.file_number,
        "user": tx.user.name,
        "action": action,
        "timestamp": tx.checkout_time.isoformat() if action=="checkout" else tx.return_time.isoformat()
    })

@socketio.on('monitor_files')
def monitor_files():
    # Simple check for new files (in production, use watchdog library)
    files = os.listdir('uploads')
    emit('file_update', {'files': files})
