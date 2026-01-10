from app import db
from app.models import AuditLog
from flask_login import current_user

def log_action(action):
    log = AuditLog(
        action=action,
        user_id=current_user.id if current_user.is_authenticated else None
    )
    db.session.add(log)
    db.session.commit()
