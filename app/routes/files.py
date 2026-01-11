from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_from_directory
from flask_login import login_required, current_user
from app.models import FileRecord, FileTransaction
from app.forms import CheckoutFileForm, ReturnFileForm, UploadFileForm
from app import db, cache
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
        file = FileRecord.query.filter_by(file_number=form.file_number.data).first()
        if not file:
            flash("File not found", "danger")
            return redirect(url_for("files.dashboard"))
        # Find the active transaction for this file (any user, since admin can return any file)
        tx = FileTransaction.query.filter_by(
            file_id=file.id,
            return_time=None
        ).first()
        if not tx:
            flash("File is not currently checked out", "danger")
            return redirect(url_for("files.dashboard"))
        
        try:
            tx.return_time = datetime.utcnow()
            tx.comments = form.comments.data
            tx.condition = form.condition.data
            tx.return_signature = form.return_signature.data
            tx.returned_to_admin_id = current_user.id
            file.is_issued = False
            db.session.commit()
            flash("File returned", "success")
            
            # Clear any cached dashboard data
            cache.delete_memoized(dashboard)
            
            from app.chat_socket import emit_file_update
            emit_file_update(tx, "return")
            from app.utils.audit import log_action
            log_action(f"File {file.file_number} returned")
        except Exception as e:
            db.session.rollback()
            flash(f'Error returning file: {str(e)}', 'danger')
        
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", "danger")
    return redirect(url_for("files.dashboard"))

@bp.route("/checkout", methods=["POST"])
@login_required
def checkout():
    form = CheckoutFileForm()
    if form.validate_on_submit():
        file = FileRecord.query.filter_by(file_number=form.file_number.data).first()
        if not file:
            flash("File not found", "danger")
            return redirect(url_for("files.dashboard"))
        if file.is_issued:
            flash("File is already checked out", "error")
            return redirect(url_for("files.dashboard"))
        
        try:
            tx = FileTransaction(
                file_id=file.id,
                user_id=current_user.id,
                checkout_time=datetime.utcnow(),
                purpose=form.purpose.data,
                checkout_signature=form.checkout_signature.data
            )
            file.is_issued = True
            db.session.add(tx)
            db.session.commit()
            flash("File checked out", "success")
            
            # Clear any cached dashboard data
            cache.delete_memoized(dashboard)
            
            from app.chat_socket import emit_file_update
            emit_file_update(tx, "checkout")
            from app.utils.audit import log_action
            log_action(f"File {file.file_number} checked out by {current_user.name}")
        except Exception as e:
            db.session.rollback()
            flash(f'Error checking out file: {str(e)}', 'danger')
        
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", "danger")
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
        existing_file = FileRecord.query.filter_by(file_number=form.file_number.data).first()
        if existing_file:
            flash('File number already exists', 'danger')
            return redirect(url_for("files.dashboard"))
        
        file = form.file.data
        if file:
            try:
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

                # Clear any cached dashboard data
                cache.delete_memoized(dashboard)

                flash('File uploaded and recorded', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error uploading file: {str(e)}', 'danger')
        else:
            flash('No file selected', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", "danger")
    return redirect(url_for("files.dashboard"))

    flash('Upload failed', 'error')
    return redirect(url_for('files.dashboard'))