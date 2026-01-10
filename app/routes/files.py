from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_from_directory
from flask_login import login_required, current_user
from app.models import FileRecord, FileTransaction
from app.forms import CheckoutFileForm, ReturnFileForm, UploadFileForm
from app import db
from datetime import datetime
import os
import shutil
from app.utils.decorators import admin_required

bp = Blueprint('files', __name__)

@bp.route('/dashboard')
@login_required
def dashboard():
    files = FileRecord.query.all()
    form = UploadFileForm()
    checkout_form = CheckoutFileForm()
    return_form = ReturnFileForm()
    return render_template('files/dashboard.html', files=files, form=form, checkout_form=checkout_form, return_form=return_form)


@bp.route("/return", methods=["POST"])
@login_required
@admin_required
def return_file():
    form = ReturnFileForm()
    if form.validate_on_submit():
        file = FileRecord.query.filter_by(file_number=form.file_number.data).first_or_404()
        # Find the active transaction for this file (any user, since admin can return any file)
        tx = FileTransaction.query.filter_by(
            file_id=file.id,
            return_time=None
        ).first_or_404()
        
        tx.return_time = datetime.utcnow()
        tx.comments = form.comments.data
        file.is_issued = False
        db.session.commit()
        flash("File returned", "success")
        
        from app.chat_socket import emit_file_update
        emit_file_update(tx, "return")
        from app.utils.audit import log_action
        log_action(f"File {file.file_number} returned")
        
    return redirect(url_for("files.dashboard"))

@bp.route("/checkout", methods=["POST"])
@login_required
def checkout():
    form = CheckoutFileForm()
    if form.validate_on_submit():
        file = FileRecord.query.filter_by(file_number=form.file_number.data).first_or_404()
        if file.is_issued:
            flash("File is already checked out", "error")
            return redirect(url_for("files.dashboard"))
        
        tx = FileTransaction(
            file_id=file.id,
            user_id=current_user.id,
            checkout_time=datetime.utcnow(),
            purpose=form.purpose.data
        )
        file.is_issued = True
        db.session.add(tx)
        db.session.commit()
        flash("File checked out", "success")
        
        from app.chat_socket import emit_file_update
        emit_file_update(tx, "checkout")
        from app.utils.audit import log_action
        log_action(f"File {file.file_number} checked out by {current_user.name}")
        
    return redirect(url_for("files.dashboard"))


@bp.route("/files/scan/<file_number>")
@login_required
def scan_file(file_number):
    file = FileRecord.query.filter_by(file_number=file_number).first_or_404()
    return redirect(url_for("files.view_file", file_id=file.id))


@bp.route("/files/<int:file_id>")
@login_required
def view_file(file_id):
    file = FileRecord.query.get_or_404(file_id)
    return render_template("files/view_file.html", file=file)





@bp.route("/files/<int:file_id>/timeline")
@login_required
def file_timeline(file_id):
    file = FileRecord.query.get_or_404(file_id)
    transactions = file.transactions
    return render_template("files/timeline.html", file=file, transactions=transactions)

@bp.route('/download/<filename>')
@login_required
def download_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@bp.route('/upload', methods=['POST'])
@login_required
def upload():
    form = UploadFileForm()
    if form.validate_on_submit():
        file = form.file.data
        if file:
            filename = file.filename
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Create FileRecord
            file_record = FileRecord(
                file_number=form.file_number.data,
                title=form.title.data,
                department=form.department.data
            )
            db.session.add(file_record)
            db.session.commit()

            # After saving file, create version
            version_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'versions', filename)
            os.makedirs(version_dir, exist_ok=True)
            version_path = os.path.join(version_dir, f"{datetime.now().isoformat()}_{filename}")
            shutil.copy(file_path, version_path)

            flash('File uploaded and recorded', 'success')
            return redirect(url_for('files.dashboard'))

    flash('Upload failed', 'error')
    return redirect(url_for('files.dashboard'))