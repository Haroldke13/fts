from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app.forms import LoginForm, CreateUserForm
from app.models import User
from app import db

bp = Blueprint("auth", __name__)

@bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for("files.dashboard"))
        flash("Invalid credentials", "danger")
    return render_template("auth/login.html", form=form)

@bp.route("/signup", methods=["GET", "POST"])
def signup():
    form = CreateUserForm()
    if form.validate_on_submit():
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
        return redirect(url_for("auth.login"))
    return render_template("auth/signup.html", form=form)

@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
