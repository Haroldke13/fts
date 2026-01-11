from flask import Blueprint, render_template
from flask_login import login_required
from app.models import FileRecord, ChatMessage, FileTransaction
from app import db
from app.utils.decorators import admin_required

bp = Blueprint("admin", __name__)

from flask import render_template
from app.models import ChatRoom, FileRecord, AuditLog

@bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    from app.models import User
    rooms = ChatRoom.query.all()
    files = FileRecord.query.all()
    audit_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()

    # Chart data
    departments = list(set(f.department for f in files))
    files_per_department = [sum(1 for f in files if f.department==d and f.is_issued) for d in departments]

    # Lifecycle timeline (example)
    lifecycle_dates = ["2026-01-01","2026-01-02","2026-01-03"]
    lifecycle_counts = [5, 8, 3]  # Replace with real data

    current_checkouts = FileTransaction.query.filter_by(return_time=None).all()

    return render_template(
        "admin/dashboard.html",
        rooms=rooms,
        files=files,
        audit_logs=audit_logs,
        departments=departments,
        files_per_department=files_per_department,
        lifecycle_dates=lifecycle_dates,
        lifecycle_counts=lifecycle_counts,
        user_count=User.query.count(),
        file_count=len(files),
        current_checkouts=current_checkouts
    )


@bp.route("/create_user", methods=["GET", "POST"])
@login_required
@admin_required
def create_user():
    from app.forms import CreateUserForm
    form = CreateUserForm()
    if form.validate_on_submit():
        from app.models import User
        from werkzeug.security import generate_password_hash
        user = User(
            name=form.name.data,
            designation=form.designation.data,
            email=form.email.data,
            password=generate_password_hash(form.password.data),
            role=form.role.data
        )
        db.session.add(user)
        db.session.commit()
        flash("User created successfully", "success")
        return redirect(url_for("admin.dashboard"))
    return render_template("admin/create_user.html", form=form)


@bp.route("/analytics")
@login_required
@admin_required
def analytics():
    from sqlalchemy import func
    from app.models import User
    
    total_files = FileRecord.query.count()
    issued_files = FileRecord.query.filter_by(is_issued=True).count()
    messages = ChatMessage.query.count()
    transactions = FileTransaction.query.count()
    
    # File transfers per user
    transfers_per_user = db.session.query(
        User.name, func.count(FileTransaction.id).label('transfer_count')
    ).join(User.transactions).group_by(User.id, User.name).all()
    
    transfers_labels = [user[0] for user in transfers_per_user]
    transfers_data = [user[1] for user in transfers_per_user]
    
    # Messages per user
    messages_per_user = db.session.query(
        User.name, func.count(ChatMessage.id)
    ).join(ChatMessage).group_by(User.id, User.name).all()
    
    messages_labels = [user[0] for user in messages_per_user]
    messages_data = [user[1] for user in messages_per_user]
    
    # Files per department
    files_per_dept = db.session.query(
        FileRecord.department, func.count(FileRecord.id)
    ).group_by(FileRecord.department).all()
    
    dept_labels = [dept[0] or 'No Department' for dept in files_per_dept]
    dept_data = [dept[1] for dept in files_per_dept]
    
    # Activity over time (last 7 days)
    from datetime import datetime, timedelta
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    activity_data = []
    for i in range(7):
        day = seven_days_ago + timedelta(days=i)
        next_day = day + timedelta(days=1)
        day_transactions = FileTransaction.query.filter(
            FileTransaction.checkout_time >= day,
            FileTransaction.checkout_time < next_day
        ).count()
        day_messages = ChatMessage.query.filter(
            ChatMessage.timestamp >= day,
            ChatMessage.timestamp < next_day
        ).count()
        activity_data.append({
            'date': day.strftime('%Y-%m-%d'),
            'transactions': day_transactions,
            'messages': day_messages
        })
    
    activity_labels = [d['date'] for d in activity_data]
    activity_transactions = [d['transactions'] for d in activity_data]
    activity_messages = [d['messages'] for d in activity_data]
    
    chart_data = {
        "labels": ["Total Files", "Issued Files", "Messages", "Transactions"],
        "datasets": [{
            "label": "Counts",
            "data": [total_files, issued_files, messages, transactions],
            "backgroundColor": ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0"]
        }]
    }
    
    transfers_chart = {
        "labels": transfers_labels,
        "datasets": [{
            "label": "File Transfers",
            "data": transfers_data,
            "backgroundColor": "#36A2EB"
        }]
    }
    
    messages_chart = {
        "labels": messages_labels,
        "datasets": [{
            "label": "Messages Sent",
            "data": messages_data,
            "backgroundColor": "#FFCE56"
        }]
    }
    
    dept_chart = {
        "labels": dept_labels,
        "datasets": [{
            "label": "Files",
            "data": dept_data,
            "backgroundColor": "#4BC0C0"
        }]
    }
    
    activity_chart = {
        "labels": activity_labels,
        "datasets": [
            {
                "label": "File Transactions",
                "data": activity_transactions,
                "borderColor": "#FF6384",
                "backgroundColor": "rgba(255, 99, 132, 0.2)"
            },
            {
                "label": "Messages",
                "data": activity_messages,
                "borderColor": "#36A2EB",
                "backgroundColor": "rgba(54, 162, 235, 0.2)"
            }
        ]
    }
    
    return render_template(
        "admin/analytics.html",
        total_files=total_files,
        issued_files=issued_files,
        messages=messages,
        transactions=transactions,
        chart_data=chart_data,
        transfers_chart=transfers_chart,
        messages_chart=messages_chart,
        dept_chart=dept_chart,
        activity_chart=activity_chart
    )


@bp.route("/live_monitor")
@login_required
@admin_required
def live_monitor():
    from app.models import User, FileRecord, ChatMessage, FileTransaction
    from datetime import datetime, date
    
    # Get today's date
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    
    # Active users - for now, all users (in production, track online status)
    active_users = User.query.all()
    
    # Total files
    total_files = FileRecord.query.all()
    
    # Messages today
    messages_today = ChatMessage.query.filter(ChatMessage.timestamp >= today_start).order_by(ChatMessage.timestamp.desc()).limit(10).all()
    
    # Active transactions
    active_transactions = FileTransaction.query.filter_by(return_time=None).all()
    
    return render_template("admin/live_monitor.html",
                         active_users=active_users,
                         total_files=total_files,
                         messages_today=messages_today,
                         active_transactions=active_transactions)
