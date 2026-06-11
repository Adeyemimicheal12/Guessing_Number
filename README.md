# NumberQuest — Number Guessing Game (eProject)

A Python/Flask web application where users guess a randomly generated number
within a defined range, with hints, scoring, levels and a leaderboard.

## Features

| Requirement | Implemented |
|-------------|-------------|
| Home page with game info | ✅ `/` |
| User registration & authentication | ✅ hashed passwords (Werkzeug) + session login |
| Gameplay with form | ✅ `/play`, `/game` |
| Hint system (Too High / Too Low + attempts) | ✅ |
| Game mechanics (random number, attempt limit) | ✅ uses `secrets` for secure RNG |
| 3 difficulty levels (Low/Moderate/Expert) | ✅ ranges 0-99 / 0-999 / 0-9999 |
| Scoring & leaderboard | ✅ `/leaderboard` |
| User profile (games, wins, best score) | ✅ `/profile` |
| Security (encrypted passwords, secure login) | ✅ password hashing + server-side sessions |
| Admin panel (manage users, feedback) | ✅ `/admin` |
| Contact Us | ✅ `/contact` |
| Submit Feedback | ✅ `/feedback` |
| Input validation | ✅ on every form |

## Setup

```bash
cd number_guessing_game
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000>

## Default Admin Account

Created automatically on first run:

- **Username:** `admin`
- **Password:** `admin123`

(Change this password after first login in a real deployment.)

## Tech Stack

- **Python 3** + **Flask** — web framework
- **Flask-SQLAlchemy** + **SQLite** — database (`game.db`, auto-created)
- **Werkzeug** — password hashing
- **HTML / CSS** — responsive UI (no external dependencies)

## Project Structure

```
number_guessing_game/
├── app.py              # routes, models, game logic
├── requirements.txt
├── README.md
├── game.db             # SQLite DB (auto-created on first run)
├── templates/          # Jinja2 HTML templates
└── static/css/style.css
```
