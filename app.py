"""
Number Guessing Game - Flask Web Application
=============================================
An eProject implementing a web-based Number Guessing Game.

Features
--------
* Home page with game information
* User registration & secure (hashed) authentication
* Gameplay with 3 difficulty levels (Low / Moderate / Expert)
* Hint system ("Too high" / "Too low") with attempt tracking
* Scoring & leaderboard
* User profile with statistics (games played, wins, best score)
* Admin panel to manage users, feedback and game settings
* Contact Us page
* Feedback form
* Input validation throughout

Run:
    pip install -r requirements.txt
    python app.py
Then open http://127.0.0.1:5000
"""

import os
import secrets
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, abort,
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

# --------------------------------------------------------------------------- #
# Application setup
# --------------------------------------------------------------------------- #
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", secrets.token_hex(16))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "game.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Difficulty levels: name -> (max_number, allowed_attempts, base_points)
LEVELS = {
    "low":      {"label": "Low",      "max": 99,   "attempts": 10, "base": 100},
    "moderate": {"label": "Moderate", "max": 999,  "attempts": 15, "base": 300},
    "expert":   {"label": "Expert",   "max": 9999, "attempts": 20, "base": 900},
}


# --------------------------------------------------------------------------- #
# Database models
# --------------------------------------------------------------------------- #
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    games_played = db.Column(db.Integer, default=0)
    wins = db.Column(db.Integer, default=0)
    best_score = db.Column(db.Integer, default=0)
    total_score = db.Column(db.Integer, default=0)

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)


class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    level = db.Column(db.String(20))
    points = db.Column(db.Integer)
    attempts = db.Column(db.Integer)
    won = db.Column(db.Boolean)
    played_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="scores")


class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    email = db.Column(db.String(120))
    message = db.Column(db.Text, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def current_user():
    uid = session.get("user_id")
    return db.session.get(User, uid) if uid else None


@app.context_processor
def inject_user():
    return {"current_user": current_user(), "year": datetime.utcnow().year}


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user or not user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def secure_random_int(maximum):
    """Cryptographically secure random number in [0, maximum]."""
    return secrets.randbelow(maximum + 1)


# --------------------------------------------------------------------------- #
# Public pages
# --------------------------------------------------------------------------- #
@app.route("/")
def index():
    return render_template("index.html", levels=LEVELS)


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()
        if not message:
            flash("Feedback message cannot be empty.", "danger")
        else:
            db.session.add(Feedback(name=name, email=email, message=message))
            db.session.commit()
            flash("Thank you! Your feedback has been submitted.", "success")
            return redirect(url_for("feedback"))
    return render_template("feedback.html")


# --------------------------------------------------------------------------- #
# Authentication
# --------------------------------------------------------------------------- #
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        errors = []
        if len(username) < 3:
            errors.append("Username must be at least 3 characters.")
        if "@" not in email or "." not in email:
            errors.append("Please enter a valid email address.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")
        if User.query.filter_by(username=username).first():
            errors.append("Username already taken.")
        if User.query.filter_by(email=email).first():
            errors.append("Email already registered.")

        if errors:
            for e in errors:
                flash(e, "danger")
        else:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session.clear()
            session["user_id"] = user.id
            flash(f"Welcome back, {user.username}!", "success")
            nxt = request.args.get("next")
            return redirect(nxt or url_for("index"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


# --------------------------------------------------------------------------- #
# Gameplay
# --------------------------------------------------------------------------- #
@app.route("/play")
@login_required
def play():
    return render_template("play.html", levels=LEVELS)


@app.route("/game/start/<level>")
@login_required
def start_game(level):
    if level not in LEVELS:
        flash("Unknown difficulty level.", "danger")
        return redirect(url_for("play"))
    cfg = LEVELS[level]
    session["game"] = {
        "level": level,
        "target": secure_random_int(cfg["max"]),
        "attempts": 0,
        "max_attempts": cfg["attempts"],
        "finished": False,
        "history": [],
    }
    return redirect(url_for("game"))


@app.route("/game", methods=["GET", "POST"])
@login_required
def game():
    g = session.get("game")
    if not g:
        flash("Choose a difficulty level to start playing.", "info")
        return redirect(url_for("play"))

    cfg = LEVELS[g["level"]]
    message = None
    message_type = "info"

    if request.method == "POST" and not g["finished"]:
        raw = request.form.get("guess", "").strip()
        if not raw.lstrip("-").isdigit():
            message, message_type = "Please enter a valid whole number.", "warning"
        else:
            guess = int(raw)
            if guess < 0 or guess > cfg["max"]:
                message = f"Guess must be between 0 and {cfg['max']}."
                message_type = "warning"
            else:
                g["attempts"] += 1
                if guess == g["target"]:
                    g["finished"] = True
                    points = max(cfg["base"] - (g["attempts"] - 1) * (cfg["base"] // cfg["attempts"]), 10)
                    _record_result(g["level"], points, g["attempts"], won=True)
                    message = f"Correct! You guessed it in {g['attempts']} attempt(s) and earned {points} points."
                    message_type = "success"
                    g["history"].append((guess, "correct"))
                else:
                    hint = "Too low" if guess < g["target"] else "Too high"
                    g["history"].append((guess, hint))
                    if g["attempts"] >= g["max_attempts"]:
                        g["finished"] = True
                        _record_result(g["level"], 0, g["attempts"], won=False)
                        message = f"Out of attempts! The number was {g['target']}."
                        message_type = "danger"
                    else:
                        message = f"{hint}! Try again."
                        message_type = "warning" if hint == "Too high" else "info"
        session["game"] = g

    return render_template(
        "game.html", g=g, cfg=cfg, message=message,
        message_type=message_type, remaining=g["max_attempts"] - g["attempts"],
    )


def _record_result(level, points, attempts, won):
    user = current_user()
    if not user:
        return
    db.session.add(Score(user_id=user.id, level=level, points=points,
                         attempts=attempts, won=won))
    user.games_played += 1
    user.total_score += points
    if won:
        user.wins += 1
    if points > user.best_score:
        user.best_score = points
    db.session.commit()


# --------------------------------------------------------------------------- #
# Leaderboard & profile
# --------------------------------------------------------------------------- #
@app.route("/leaderboard")
def leaderboard():
    top = User.query.filter(User.games_played > 0) \
        .order_by(User.best_score.desc(), User.wins.desc()).limit(20).all()
    return render_template("leaderboard.html", players=top)


@app.route("/profile")
@login_required
def profile():
    user = current_user()
    recent = Score.query.filter_by(user_id=user.id) \
        .order_by(Score.played_at.desc()).limit(10).all()
    return render_template("profile.html", user=user, recent=recent)


# --------------------------------------------------------------------------- #
# Admin panel
# --------------------------------------------------------------------------- #
@app.route("/admin", methods=["GET", "POST"])
def admin():
    user = current_user()

    # If not logged in as an admin, show the Django-style admin login page.
    if not user or not user.is_admin:
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            candidate = User.query.filter_by(username=username).first()
            if candidate and candidate.check_password(password) and candidate.is_admin:
                session.clear()
                session["user_id"] = candidate.id
                return redirect(url_for("admin"))
            return render_template("admin_login.html",
                                   error="Please enter the correct username and password "
                                         "for a staff account. Note that both fields may be "
                                         "case-sensitive.")
        return render_template("admin_login.html", error=None)

    users = User.query.order_by(User.created_at.desc()).all()
    feedbacks = Feedback.query.order_by(Feedback.submitted_at.desc()).all()

    total_games = Score.query.count()
    total_wins = Score.query.filter_by(won=True).count()
    total_points = db.session.query(db.func.coalesce(db.func.sum(Score.points), 0)).scalar()
    win_rate = round(total_wins / total_games * 100) if total_games else 0
    admin_count = sum(1 for u in users if u.is_admin)

    # Games played per difficulty level
    level_rows = db.session.query(Score.level, db.func.count(Score.id)) \
        .group_by(Score.level).all()
    level_counts = {key: 0 for key in LEVELS}
    for lvl, count in level_rows:
        if lvl in level_counts:
            level_counts[lvl] = count

    # Top players by best score
    top_players = User.query.filter(User.games_played > 0) \
        .order_by(User.best_score.desc(), User.wins.desc()).limit(5).all()

    # Most recent games across all players
    recent_scores = Score.query.order_by(Score.played_at.desc()).limit(8).all()

    return render_template(
        "admin.html",
        users=users,
        feedbacks=feedbacks,
        levels=LEVELS,
        total_games=total_games,
        total_wins=total_wins,
        total_points=total_points,
        win_rate=win_rate,
        admin_count=admin_count,
        player_count=len(users) - admin_count,
        level_counts=level_counts,
        top_players=top_players,
        recent_scores=recent_scores,
    )


@app.route("/admin/user/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if user and not user.is_admin:
        Score.query.filter_by(user_id=user.id).delete()
        db.session.delete(user)
        db.session.commit()
        flash("User deleted.", "success")
    else:
        flash("Cannot delete this user.", "danger")
    return redirect(url_for("admin"))


@app.route("/admin/feedback/<int:fid>/delete", methods=["POST"])
@admin_required
def delete_feedback(fid):
    fb = db.session.get(Feedback, fid)
    if fb:
        db.session.delete(fb)
        db.session.commit()
        flash("Feedback removed.", "success")
    return redirect(url_for("admin"))


# --------------------------------------------------------------------------- #
# Error handlers
# --------------------------------------------------------------------------- #
@app.errorhandler(403)
def forbidden(e):
    return render_template("error.html", code=403,
                           message="You do not have permission to view this page."), 403


@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404,
                           message="Page not found."), 404


# --------------------------------------------------------------------------- #
# Database initialisation
# --------------------------------------------------------------------------- #
def init_db():
    """Create tables and a default admin account on first run."""
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username="admin").first():
            admin_user = User(username="admin", email="admin@numbergame.com", is_admin=True)
            admin_user.set_password("admin123")
            db.session.add(admin_user)
            db.session.commit()
            print(">> Default admin created  ->  username: admin  password: admin123")


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
