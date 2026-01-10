from flask import Blueprint, render_template
from flask_login import login_required
from app.models import FileRecord, ChatMessage, FileTransaction
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
    total_files = FileRecord.query.count()
    issued_files = FileRecord.query.filter_by(is_issued=True).count()
    messages = ChatMessage.query.count()
    transactions = FileTransaction.query.count()
    chart_data = {
        "labels": ["Total Files", "Issued Files", "Messages", "Transactions"],
        "datasets": [{
            "label": "Counts",
            "data": [total_files, issued_files, messages, transactions],
            "backgroundColor": ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0"]
        }]
    }
    return render_template(
        "admin/analytics.html",
        total_files=total_files,
        issued_files=issued_files,
        messages=messages,
        transactions=transactions,
        chart_data=chart_data
    )


@bp.route("/live_monitor")
@login_required
@admin_required
def live_monitor():
    return render_template("admin/live_monitor.html")
