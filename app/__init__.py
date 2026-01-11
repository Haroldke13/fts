from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager
from flask_compress import Compress
from flask_caching import Cache
import os

from .db import db
from .forms import UploadFileForm, CheckoutFileForm, ReturnFileForm
login_manager = LoginManager()
jwt = JWTManager()
socketio = SocketIO(cors_allowed_origins="*")
cache = None

def create_app():
    template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'templates')
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'static')
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

    app.config.from_object("app.config.Config")
    app.config["SECRET_KEY"] = os.environ.get('SECRET_KEY', 'default-secret-key')
    app.config["JWT_SECRET_KEY"] = "your-jwt-secret-key"
    app.config['WTF_CSRF_ENABLED'] = False

    Compress(app)
    global cache
    cache = Cache(app, config={"CACHE_TYPE": "SimpleCache"})

    db.init_app(app)
    login_manager.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app)

    from .models import User, FileRecord, FileTransaction, ChatRoom, ChatMessage, AuditLog

    with app.app_context():
        db.create_all()

    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Import and register blueprints
    from .routes.files import bp as files_bp
    from .routes.auth import bp as auth_bp
    from .routes.chat import bp as chat_bp
    from .routes.admin import bp as admin_bp
    from .api.auth import api_auth
    from .api.chat import api as chat_api

    app.register_blueprint(files_bp, url_prefix='/files')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_auth, url_prefix='/api/auth')
    app.register_blueprint(chat_api, url_prefix='/api')
    
    @app.context_processor
    def inject_chat_notifications():
        from flask_login import current_user
        from app.models import ChatRoom, ChatMessage, ChatRoomMember
        from app.routes.chat import can_access_chat
        
        if current_user.is_authenticated:
            # Get unread messages in rooms the user can access
            total_unread = 0
            user_memberships = ChatRoomMember.query.filter_by(user_id=current_user.id).all()
            
            for membership in user_memberships:
                # Count messages after last read time
                unread_count = ChatMessage.query.filter(
                    ChatMessage.room_id == membership.room_id,
                    ChatMessage.timestamp > membership.last_read_at
                ).count()
                total_unread += unread_count
        else:
            total_unread = 0
        
        return {'total_chat_messages': total_unread}

    @app.route('/')
    def index():
        files = []  # Placeholder
        form = UploadFileForm()
        checkout_form = CheckoutFileForm()
        return_form = ReturnFileForm()
        return render_template('files/dashboard.html', files=files, form=form, checkout_form=checkout_form, return_form=return_form)

    return app
