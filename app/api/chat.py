from flask import Blueprint, jsonify, request, abort
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask_login import current_user, login_required
from app.models import ChatRoom, ChatMessage, User
from app import db

api = Blueprint("chat_api", __name__)

# Helper decorator
def admin_required():
    claims = get_jwt()
    if claims.get("role") != "admin":
        abort(403)

# GET all messages in a room
@api.route("/chat/<int:room_id>/messages", methods=["GET"])
def api_get_messages(room_id):
    if not current_user.is_authenticated:
        return jsonify({"error": "Authentication required"}), 401
        
    # Check if user can access this room
    room = ChatRoom.query.get_or_404(room_id)
    from app.routes.chat import can_access_chat
    if not can_access_chat(current_user, room):
        return jsonify({"error": "Access denied"}), 403
        
    messages = ChatMessage.query.filter_by(room_id=room_id).all()
    return jsonify([
        {
            "id": m.id,
            "sender": m.sender.name,
            "message": m.message,
            "image_filename": m.image_filename,
            "voice_filename": m.voice_filename,
            "video_filename": m.video_filename,
            "timestamp": m.timestamp.isoformat()
        } for m in messages
    ])

# POST message in a chat room
@api.route("/chat/<int:room_id>/messages", methods=["POST"])
@jwt_required()
def api_post_message(room_id):
    data = request.json
    user_id = get_jwt_identity()
    room = ChatRoom.query.get_or_404(room_id)

    msg = ChatMessage(
        room_id=room.id,
        sender_id=user_id,
        message=data.get("message", "")
    )
    db.session.add(msg)
    db.session.commit()

    return {"status": "sent", "message_id": msg.id}, 201

# GET all rooms (admin-only)
@api.route("/chat/rooms", methods=["GET"])
@jwt_required()
def api_get_rooms():
    admin_required()
    rooms = ChatRoom.query.all()
    return jsonify([
        {
            "id": r.id,
            "name": r.name,
            "file_id": r.file_id
        } for r in rooms
    ])
