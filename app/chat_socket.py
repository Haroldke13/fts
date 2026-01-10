from flask_socketio import join_room, emit
from flask_login import current_user
from app.models import ChatMessage, FileTransaction, FileRecord
from app import db, socketio
import os

# Join chat room
@socketio.on("join")
def join(data):
    join_room(str(data["room_id"]))

# Send chat message
@socketio.on("send_message")
def send_message(data):
    msg = ChatMessage(
        room_id=data["room_id"],
        sender_id=current_user.id,
        message=data.get("message") if data.get("message") and data.get("message").strip() else None,
        image_filename=data.get("image_filename"),
        voice_filename=data.get("voice_filename"),
        video_filename=data.get("video_filename")
    )
    db.session.add(msg)
    db.session.commit()

    # Emit to room with multimedia support
    emit_data = {
        "sender": current_user.name,
        "message": msg.message,
        "image_filename": msg.image_filename,
        "voice_filename": msg.voice_filename,
        "video_filename": msg.video_filename,
        "timestamp": msg.timestamp.strftime('%H:%M')
    }
    emit("receive_message", emit_data, room=str(data["room_id"]))

    # Emit to admin dashboard
    emit("admin_update", {
        "type": "chat",
        "room_id": data["room_id"],
        "sender": current_user.name,
        "message": msg.message or "[Media message]"
    }, broadcast=True)

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
