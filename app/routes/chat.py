from flask import Blueprint, render_template, redirect, url_for, abort, flash, request, current_app
from flask_login import login_required, current_user
from app.models import ChatRoom, ChatMessage, FileTransaction, ChatRoomMember, User
from app.forms import ChatMessageForm, CreateChatRoomForm, DeleteChatRoomForm
from app import db, socketio, cache
from datetime import datetime
import os

bp = Blueprint('chat', __name__)

def can_access_chat(user, room):
    # Admins can access all rooms
    if user.is_admin():
        return True

    # Check if user is a member of the room
    member = ChatRoomMember.query.filter_by(room_id=room.id, user_id=user.id).first()
    if member:
        return True

    # If room is linked to a file, check if user has that file checked out
    if room.file:
        return FileTransaction.query.filter_by(
            file_id=room.file.id,
            user_id=user.id,
            return_time=None
        ).first() is not None

    return False

@bp.route("/rooms")
@login_required
@cache.cached(False)
def rooms():
    rooms = ChatRoom.query.all()
    form = CreateChatRoomForm()
    
    # Calculate unread messages for each room
    room_unread_counts = {}
    for room in rooms:
        if can_access_chat(current_user, room):
            membership = ChatRoomMember.query.filter_by(room_id=room.id, user_id=current_user.id).first()
            if membership:
                unread_count = ChatMessage.query.filter(
                    ChatMessage.room_id == room.id,
                    ChatMessage.timestamp > membership.last_read_at
                ).count()
                room_unread_counts[room.id] = unread_count
            else:
                # If user can access but no membership record, show all messages as unread
                room_unread_counts[room.id] = len(room.messages)
        else:
            room_unread_counts[room.id] = 0
    
    return render_template("chat/rooms.html", rooms=rooms, form=form, room_unread_counts=room_unread_counts)

@bp.route("/create_room", methods=["GET", "POST"])
@login_required
def create_room():
    form = CreateChatRoomForm()
    if form.validate_on_submit():
        room = ChatRoom(name=form.name.data)
        db.session.add(room)
        db.session.commit()

        # Add creator as first member
        member = ChatRoomMember(
            room_id=room.id,
            user_id=current_user.id,
            added_by_id=current_user.id
        )
        db.session.add(member)
        db.session.commit()

        flash("Chat room created", "success")
        return redirect(url_for("chat.chat_room", room_id=room.id))
    return render_template("chat/create_room.html", form=form)

@bp.route("/delete_room/<int:room_id>", methods=["GET", "POST"])
@login_required
def delete_room(room_id):
    room = ChatRoom.query.get_or_404(room_id)
    
    # Only admins can delete rooms
    if not current_user.is_admin():
        abort(403)
    
    form = DeleteChatRoomForm()
    if form.validate_on_submit():
        if form.confirm_delete.data:
            # Delete all messages, members, and the room
            ChatMessage.query.filter_by(room_id=room.id).delete()
            ChatRoomMember.query.filter_by(room_id=room.id).delete()
            db.session.delete(room)
            db.session.commit()
            
            flash("Chat room deleted successfully", "success")
            return redirect(url_for("chat.rooms"))
        else:
            flash("Please confirm deletion", "warning")
    
    return render_template("chat/delete_room.html", room=room, form=form)

@bp.route("/<int:room_id>", methods=["GET", "POST"])
@login_required
def chat_room(room_id):
    room = ChatRoom.query.get_or_404(room_id)

    if not can_access_chat(current_user, room):
        abort(403)

    form = ChatMessageForm()
    if form.validate_on_submit():
        # Check if at least one field is provided (message or media)
        has_content = (form.message.data and form.message.data.strip()) or form.image.data or form.voice_note.data
        
        if not has_content:
            flash("Please provide a message or upload media", "error")
            return redirect(url_for("chat.chat_room", room_id=room.id))
        
        msg = ChatMessage(
            room_id=room.id,
            sender_id=current_user.id,
            message=form.message.data if form.message.data and form.message.data.strip() else None
        )
        
        # Handle file uploads
        upload_folder = current_app.config['UPLOAD_FOLDER']
        chat_uploads = os.path.join(upload_folder, 'chat')
        os.makedirs(chat_uploads, exist_ok=True)
        
        if form.image.data:
            filename = f"img_{room.id}_{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{form.image.data.filename}"
            filepath = os.path.join(chat_uploads, filename)
            form.image.data.save(filepath)
            msg.image_filename = filename
            
        if form.voice_note.data:
            filename = f"voice_{room.id}_{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{form.voice_note.data.filename}"
            filepath = os.path.join(chat_uploads, filename)
            form.voice_note.data.save(filepath)
            msg.voice_filename = filename
        
        db.session.add(msg)
        db.session.commit()
        
        # Emit real-time message to room
        socketio.emit('receive_message', {
            "sender": current_user.name,
            "message": msg.message,
            "image_filename": msg.image_filename,
            "voice_filename": msg.voice_filename,
            "timestamp": msg.timestamp.strftime('%H:%M')
        }, room=str(room.id))
        
        # Update notifications for room members
        from app.chat_socket import update_notifications_for_room
        update_notifications_for_room(room.id, current_user.id)
        
        return redirect(url_for("chat.chat_room", room_id=room.id))

    messages = ChatMessage.query.filter_by(room_id=room.id).order_by(ChatMessage.timestamp.desc()).limit(50).all()
    messages.reverse()  # Show oldest messages first
    members = ChatRoomMember.query.filter_by(room_id=room.id).all()
    
    # Mark room as read for current user
    member = ChatRoomMember.query.filter_by(room_id=room_id, user_id=current_user.id).first()
    if member:
        member.last_read_at = datetime.utcnow()
        db.session.commit()
    
    # Get available users (not already in the room)
    member_user_ids = [member.user_id for member in members]
    available_users = User.query.filter(~User.id.in_(member_user_ids)).all()
    
    return render_template("chat/chat_room.html", room=room, messages=messages, form=form, members=members, available_users=available_users)

@bp.route("/<int:room_id>/add_user", methods=["POST"])
@login_required
def add_user_to_room(room_id):
    if not current_user.is_admin():
        abort(403)

    room = ChatRoom.query.get_or_404(room_id)
    username = request.form.get('username')

    if not username:
        flash("Username is required", "error")
        return redirect(url_for("chat.chat_room", room_id=room_id))

    user = User.query.filter_by(name=username).first()
    if not user:
        flash("User not found", "error")
        return redirect(url_for("chat.chat_room", room_id=room_id))

    # Check if user is already a member
    existing_member = ChatRoomMember.query.filter_by(room_id=room_id, user_id=user.id).first()
    if existing_member:
        flash("User is already a member of this room", "warning")
        return redirect(url_for("chat.chat_room", room_id=room_id))

    # Add user to room
    member = ChatRoomMember(
        room_id=room_id,
        user_id=user.id,
        added_by_id=current_user.id
    )
    db.session.add(member)
    db.session.commit()

    flash(f"Added {user.name} to the chat room", "success")
    return redirect(url_for("chat.chat_room", room_id=room_id))

@bp.route("/<int:room_id>/remove_user/<int:user_id>", methods=["POST"])
@login_required
def remove_user_from_room(room_id, user_id):
    if not current_user.is_admin():
        abort(403)

    room = ChatRoom.query.get_or_404(room_id)
    member = ChatRoomMember.query.filter_by(room_id=room_id, user_id=user_id).first_or_404()

    if member.user_id == current_user.id:
        flash("You cannot remove yourself from the room", "error")
        return redirect(url_for("chat.chat_room", room_id=room_id))

    # Get user name before deleting the member
    user_name = member.user.name
    
    db.session.delete(member)
    db.session.commit()

    flash(f"Removed {user_name} from the chat room", "success")
    return redirect(url_for("chat.chat_room", room_id=room_id))
