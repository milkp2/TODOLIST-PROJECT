from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)
from datetime import datetime

app = Flask(__name__)

# =========================
# CONFIG
# =========================
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todo.db"
app.config["SECRET_KEY"] = "secretkey"

db = SQLAlchemy(app)

# =========================
# LOGIN MANAGER
# =========================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# =========================
# MODELS
# =========================
class User(db.Model, UserMixin):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )


class Task(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(255),
        nullable=False
    )

    completed = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )


# =========================
# LOAD USER
# =========================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# =========================
# REGISTER
# =========================
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        existing_user = User.query.filter_by(
            username=username
        ).first()

        if existing_user:
            return "Username already exists"

        hashed_password = generate_password_hash(password)

        user = User(
            username=username,
            password=hashed_password
        )

        db.session.add(user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")


# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(
            username=username
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            login_user(user)

            return redirect(
                url_for("home")
            )

        return "Login failed"

    return render_template("login.html")


# =========================
# HOME
# =========================
@app.route("/")
@login_required
def home():

    tasks = Task.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Task.created_at.desc()
    ).all()

    total = len(tasks)

    completed = len([
        task for task in tasks
        if task.completed
    ])

    progress = 0

    if total > 0:
        progress = int(
            (completed / total) * 100
        )

    return render_template(
        "index.html",
        tasks=tasks,
        total=total,
        completed=completed,
        progress=progress
    )


# =========================
# ADD TASK
# =========================
@app.route("/add", methods=["POST"])
@login_required
def add():

    title = request.form["title"]

    task = Task(
        title=title,
        user_id=current_user.id
    )

    db.session.add(task)
    db.session.commit()

    return redirect(url_for("home"))


# =========================
# COMPLETE TASK
# =========================
@app.route("/complete/<int:id>")
@login_required
def complete(id):

    task = Task.query.get_or_404(id)

    if task.user_id != current_user.id:
        return "Unauthorized"

    task.completed = not task.completed

    db.session.commit()

    return redirect(url_for("home"))


# =========================
# DELETE TASK
# =========================
@app.route("/delete/<int:id>")
@login_required
def delete(id):

    task = Task.query.get_or_404(id)

    if task.user_id != current_user.id:
        return "Unauthorized"

    db.session.delete(task)
    db.session.commit()

    return redirect(url_for("home"))


# =========================
# LOGOUT
# =========================
@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(
        url_for("login")
    )


# =========================
# CREATE DATABASE
# =========================
with app.app_context():
    db.create_all()


# =========================
# RUN
# =========================
if __name__ == "__main__":

    app.run(
        debug=True,
        use_reloader=False
    )