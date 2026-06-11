"""
view_users.py — list every registered user stored in game.db

Usage:
    python view_users.py
"""
from app import app, db, User

with app.app_context():
    db.create_all()  # ensure the table exists
    users = User.query.order_by(User.created_at).all()

    if not users:
        print("No users registered yet.")
    else:
        print(f"{len(users)} registered user(s):\n")
        for u in users:
            print(f"ID            : {u.id}")
            print(f"Username      : {u.username}")
            print(f"Email         : {u.email}")
            print(f"Role          : {'Admin' if u.is_admin else 'Player'}")
            print(f"Registered    : {u.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Games played  : {u.games_played}")
            print(f"Wins          : {u.wins}")
            print(f"Best score    : {u.best_score}")
            print(f"Total score   : {u.total_score}")
            print(f"Password hash : {u.password_hash}")   # one-way hash, NOT the real password
            print("-" * 60)
