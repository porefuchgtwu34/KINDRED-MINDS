"""
Kindred Minds — a community about love, relationships & psychology
--------------------------------------------------------------------
Flask + SQLite backend.
"""

import os
import re
import sqlite3
import secrets
import random
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, g, abort
)
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if os.environ.get("VERCEL"):
    DB_PATH = "/tmp/kindred.db"
else:
    DB_PATH = os.path.join(BASE_DIR, "kindred.db")

app = Flask(__name__)
app.secret_key = os.environ.get("KINDRED_SECRET_KEY", "dev-secret-change-me-in-prod")

POSTS_PER_PAGE = 5
MESSAGES_PER_PAGE = 20
USERS_PER_PAGE = 10

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,20}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

QUOTES = [
    ("Intimacy is not about being perfect. It's about being real with someone.", "Dr. Sue Johnson"),
    ("We are wired for connection. It's why we're here.", "Brené Brown"),
    ("The quality of your life is the quality of your relationships.", "Esther Perel"),
    ("Attachment is not a weakness, it's survival wired into love.", "Amir Levine"),
    ("Love is a verb, not just a feeling — it shows up in small repeated acts.", "Gary Chapman"),
    ("You can't pour from a healthy cup if you never learned to fill it.", "Kindred Minds"),
    ("Every argument is really two people asking, 'Can I count on you?'", "Dr. Sue Johnson"),
    ("Boundaries are the distance at which I can love you and me simultaneously.", "Prentis Hemphill"),
    ("The opposite of connection is not conflict, it's disconnection.", "Kindred Minds"),
    ("People don't need advice. They need someone to believe in them.", "Kindred Minds"),
]

QUIZ_QUESTIONS = [
    {
        "q": "When your partner is upset, you usually...",
        "options": [
            ("Move closer and ask what's wrong right away", "secure"),
            ("Give them space, worried you'll make it worse", "avoidant"),
            ("Feel anxious until the tension is resolved", "anxious"),
            ("Try to fix it immediately, even before understanding it", "anxious"),
        ],
    },
    {
        "q": "In a new relationship, you tend to...",
        "options": [
            ("Trust gradually, at a comfortable pace", "secure"),
            ("Keep some emotional distance at first", "avoidant"),
            ("Want frequent reassurance that things are okay", "anxious"),
            ("Overthink every text message", "anxious"),
        ],
    },
    {
        "q": "Conflict in a relationship feels like...",
        "options": [
            ("A normal part of getting closer", "secure"),
            ("Something to avoid or shut down quickly", "avoidant"),
            ("A sign the relationship might be ending", "anxious"),
            ("An opportunity to talk things through calmly", "secure"),
        ],
    },
    {
        "q": "Your ideal amount of togetherness is...",
        "options": [
            ("A healthy balance of together time and independence", "secure"),
            ("Mostly independent, with love shown through actions", "avoidant"),
            ("As much closeness as possible, often", "anxious"),
            ("It depends, but I need to feel secure either way", "secure"),
        ],
    },
    {
        "q": "When you don't hear back from someone quickly, you...",
        "options": [
            ("Assume they're busy and carry on with your day", "secure"),
            ("Don't think much of it at all", "avoidant"),
            ("Start imagining worst-case scenarios", "anxious"),
            ("Feel a little uneasy but distract yourself", "anxious"),
        ],
    },
]

QUIZ_RESULTS = {
    "secure": {
        "title": "Secure Attachment",
        "text": "You tend to feel comfortable with closeness and independence alike. You communicate needs directly, trust reasonably, and see conflict as workable rather than threatening. Keep nurturing relationships where that security is met in kind.",
    },
    "anxious": {
        "title": "Anxious Attachment",
        "text": "You care deeply and crave closeness, sometimes worrying about where you stand. Reassurance helps, but the sturdiest relationships grow when you also build self-soothing habits so your peace isn't only borrowed from someone else's reply.",
    },
    "avoidant": {
        "title": "Avoidant Attachment",
        "text": "You value independence and may pull back when things get intense. That's not coldness, it's a strategy that once kept you safe. Practising small moments of vulnerability, on your own timeline, can deepen connection without it feeling like losing yourself.",
    },
}

MOOD_INSIGHTS = {
    "joyful": "Joy is worth naming, not just feeling. Write down what led here so you can return to it on harder days.",
    "content": "Contentment is a quiet signal that your needs are being met. Notice what's contributing to that.",
    "anxious": "Anxiety often points to an unmet need for certainty. Ask yourself: what's one small thing you can control right now?",
    "sad": "Sadness deserves space, not fixing. Let yourself feel it fully before deciding what, if anything, needs to change.",
    "angry": "Anger is frequently a bodyguard for a softer feeling underneath, like hurt or fear. What might be underneath it?",
    "lonely": "Loneliness is a signal to reach toward connection, even in a small way. Is there one person you could message today?",
    "hopeful": "Hope is fuel. Consider what specifically is making you feel it, so you can find more of it on purpose.",
    "overwhelmed": "Overwhelm often means too many things feel urgent at once. Try naming just the next single step, not the whole picture.",
}


def get_db():
    if "db" not in g:
        need_init = not os.path.exists(DB_PATH)
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        if need_init:
            init_db()
            g.db = sqlite3.connect(DB_PATH)
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            bio TEXT DEFAULT '',
            is_admin INTEGER DEFAULT 0,
            is_banned INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mood TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TEXT NOT NULL,
            used INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    )
    db.commit()
    existing = db.execute("SELECT id FROM users WHERE is_admin = 1").fetchone()
    if not existing:
        db.execute(
            "INSERT INTO users (username, email, password_hash, bio, is_admin, created_at) VALUES (?,?,?,?,1,?)",
            ("admin", "admin@kindredminds.local", generate_password_hash("admin123"), "Community steward.", datetime.utcnow().isoformat()),
        )
        db.commit()
    db.close()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login", next=request.path))
        user = get_db().execute(
            "SELECT id FROM users WHERE id = ?", (session["user_id"],)
        ).fetchone()
        if user is None:
            session.clear()
            flash("Your session expired. Please log in again.", "warning")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        if not session.get("is_admin"):
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def current_user():
    if "user_id" not in session:
        return None
    return get_db().execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()


@app.context_processor
def inject_user():
    return {"current_user": current_user(), "current_year": datetime.utcnow().year}


@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("feed"))
    quote = random.choice(QUOTES)
    return render_template("index.html", quote=quote)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        errors = []
        if not USERNAME_RE.match(username):
            errors.append("Username must be 3-20 characters: letters, numbers, underscores only.")
        if not EMAIL_RE.match(email):
            errors.append("Please enter a valid email address.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")
        db = get_db()
        if not errors:
            if db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone():
                errors.append("That username is already taken.")
            if db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone():
                errors.append("An account with that email already exists.")
        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("register.html", username=username, email=email)
        db.execute(
            "INSERT INTO users (username, email, password_hash, created_at) VALUES (?,?,?,?)",
            (username, email, generate_password_hash(password), datetime.utcnow().isoformat()),
        )
        db.commit()
        flash("Welcome to Kindred Minds! Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html", username="", email="")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip().lower()
        password = request.form.get("password", "")
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE lower(username) = ? OR lower(email) = ?",
            (identifier, identifier),
        ).fetchone()
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Incorrect username/email or password.", "error")
            return render_template("login.html", identifier=identifier)
        if user["is_banned"]:
            flash("This account has been suspended. Contact admin for details.", "error")
            return render_template("login.html", identifier=identifier)
        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["is_admin"] = bool(user["is_admin"])
        flash(f"Welcome back, {user['username']}!", "success")
        next_url = request.args.get("next")
        return redirect(next_url or url_for("feed"))
    return render_template("login.html", identifier="")


@app.route("/logout")
def logout():
    session.clear()
    flash("You've been logged out. See you soon.", "success")
    return redirect(url_for("home"))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        reset_link = None
        if user:
            token = secrets.token_urlsafe(32)
            expires = (datetime.utcnow() + timedelta(hours=1)).isoformat()
            db.execute(
                "INSERT INTO reset_tokens (user_id, token, expires_at) VALUES (?,?,?)",
                (user["id"], token, expires),
            )
            db.commit()
            reset_link = url_for("reset_password", token=token, _external=True)
        flash("If that email is registered, a reset link has been generated below.", "success")
        return render_template("forgot_password.html", reset_link=reset_link)
    return render_template("forgot_password.html", reset_link=None)


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    db = get_db()
    row = db.execute("SELECT * FROM reset_tokens WHERE token = ? AND used = 0", (token,)).fetchone()
    if not row or row["expires_at"] < datetime.utcnow().isoformat():
        flash("This reset link is invalid or has expired.", "error")
        return redirect(url_for("forgot_password"))
    if request.method == "POST":
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("reset_password.html", token=token)
        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("reset_password.html", token=token)
        db.execute("UPDATE users SET password_hash = ? WHERE id = ?", (generate_password_hash(password), row["user_id"]))
        db.execute("UPDATE reset_tokens SET used = 1 WHERE id = ?", (row["id"],))
        db.commit()
        flash("Password updated. Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("reset_password.html", token=token)


@app.route("/feed")
@login_required
def feed():
    db = get_db()
    page = max(int(request.args.get("page", 1)), 1)
    category = request.args.get("category", "all")
    where = ""
    params = []
    if category != "all":
        where = "WHERE p.category = ?"
        params.append(category)
    total = db.execute(f"SELECT COUNT(*) c FROM posts p {where}", params).fetchone()["c"]
    total_pages = max((total + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE, 1)
    page = min(page, total_pages)
    offset = (page - 1) * POSTS_PER_PAGE
    posts = db.execute(
        f"""SELECT p.*, u.username, u.is_admin as author_is_admin,
                   (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id) as comment_count
            FROM posts p JOIN users u ON p.user_id = u.id
            {where}
            ORDER BY p.created_at DESC
            LIMIT ? OFFSET ?""",
        params + [POSTS_PER_PAGE, offset],
    ).fetchall()
    return render_template("feed.html", posts=posts, page=page, total_pages=total_pages, category=category)


@app.route("/post/new", methods=["POST"])
@login_required
def new_post():
    content = request.form.get("content", "").strip()
    category = request.form.get("category", "general")
    if not content:
        flash("Your post can't be empty.", "error")
    elif len(content) > 2000:
        flash("Posts are limited to 2000 characters.", "error")
    else:
        db = get_db()
        db.execute(
            "INSERT INTO posts (user_id, content, category, created_at) VALUES (?,?,?,?)",
            (session["user_id"], content, category, datetime.utcnow().isoformat()),
        )
        db.commit()
        flash("Your post is live.", "success")
    return redirect(url_for("feed"))


@app.route("/post/<int:post_id>")
@login_required
def view_post(post_id):
    db = get_db()
    post = db.execute(
        """SELECT p.*, u.username, u.is_admin as author_is_admin
           FROM posts p JOIN users u ON p.user_id = u.id WHERE p.id = ?""",
        (post_id,),
    ).fetchone()
    if not post:
        abort(404)
    comments = db.execute(
        """SELECT c.*, u.username, u.is_admin as author_is_admin
           FROM comments c JOIN users u ON c.user_id = u.id
           WHERE c.post_id = ? ORDER BY c.created_at ASC""",
        (post_id,),
    ).fetchall()
    return render_template("post.html", post=post, comments=comments)


@app.route("/post/<int:post_id>/comment", methods=["POST"])
@login_required
def new_comment(post_id):
    content = request.form.get("content", "").strip()
    db = get_db()
    post = db.execute("SELECT id FROM posts WHERE id = ?", (post_id,)).fetchone()
    if not post:
        abort(404)
    if not content:
        flash("Comment can't be empty.", "error")
    else:
        db.execute(
            "INSERT INTO comments (post_id, user_id, content, created_at) VALUES (?,?,?,?)",
            (post_id, session["user_id"], content, datetime.utcnow().isoformat()),
        )
        db.commit()
        flash("Comment added.", "success")
    return redirect(url_for("view_post", post_id=post_id))


@app.route("/post/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    db = get_db()
    post = db.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    if not post:
        abort(404)
    if post["user_id"] != session["user_id"] and not session.get("is_admin"):
        abort(403)
    db.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    db.commit()
    flash("Post removed.", "success")
    return redirect(request.referrer or url_for("feed"))


@app.route("/messages")
@login_required
def messages_inbox():
    db = get_db()
    uid = session["user_id"]
    partners = db.execute(
        """
        SELECT u.id, u.username,
               (SELECT content FROM messages m2
                WHERE (m2.sender_id = u.id AND m2.receiver_id = :uid)
                   OR (m2.sender_id = :uid AND m2.receiver_id = u.id)
                ORDER BY m2.created_at DESC LIMIT 1) as last_message,
               (SELECT created_at FROM messages m3
                WHERE (m3.sender_id = u.id AND m3.receiver_id = :uid)
                   OR (m3.sender_id = :uid AND m3.receiver_id = u.id)
                ORDER BY m3.created_at DESC LIMIT 1) as last_time,
               (SELECT COUNT(*) FROM messages m4
                WHERE m4.sender_id = u.id AND m4.receiver_id = :uid AND m4.is_read = 0) as unread
        FROM users u
        WHERE u.id != :uid AND u.id IN (
            SELECT sender_id FROM messages WHERE receiver_id = :uid
            UNION
            SELECT receiver_id FROM messages WHERE sender_id = :uid
        )
        ORDER BY last_time DESC
        """,
        {"uid": uid},
    ).fetchall()
    all_users = db.execute(
        "SELECT id, username FROM users WHERE id != ? AND is_banned = 0 ORDER BY username",
        (uid,),
    ).fetchall()
    return render_template("messages.html", partners=partners, all_users=all_users)


@app.route("/messages/<username>")
@login_required
def conversation(username):
    db = get_db()
    other = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if not other:
        abort(404)
    uid = session["user_id"]
    db.execute("UPDATE messages SET is_read = 1 WHERE sender_id = ? AND receiver_id = ?", (other["id"], uid))
    db.commit()
    msgs = db.execute(
        """SELECT m.*, u.username as sender_name FROM messages m
           JOIN users u ON m.sender_id = u.id
           WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)
           ORDER BY m.created_at ASC LIMIT ?""",
        (uid, other["id"], other["id"], uid, MESSAGES_PER_PAGE * 5),
    ).fetchall()
    return render_template("conversation.html", other=other, messages=msgs)


@app.route("/api/messages/<username>/send", methods=["POST"])
@login_required
def send_message(username):
    db = get_db()
    other = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if not other:
        return jsonify({"error": "User not found"}), 404
    content = (request.json or {}).get("content", "").strip()
    if not content:
        return jsonify({"error": "Message can't be empty"}), 400
    if len(content) > 1000:
        return jsonify({"error": "Message too long"}), 400
    now = datetime.utcnow().isoformat()
    cur = db.execute(
        "INSERT INTO messages (sender_id, receiver_id, content, created_at) VALUES (?,?,?,?)",
        (session["user_id"], other["id"], content, now),
    )
    db.commit()
    return jsonify({
        "id": cur.lastrowid,
        "sender_id": session["user_id"],
        "sender_name": session["username"],
        "content": content,
        "created_at": now,
    })


@app.route("/api/messages/<username>/poll")
@login_required
def poll_messages(username):
    db = get_db()
    other = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if not other:
        return jsonify({"error": "User not found"}), 404
    since = request.args.get("since", "1970-01-01T00:00:00")
    uid = session["user_id"]
    db.execute("UPDATE messages SET is_read = 1 WHERE sender_id = ? AND receiver_id = ?", (other["id"], uid))
    db.commit()
    rows = db.execute(
        """SELECT m.*, u.username as sender_name FROM messages m
           JOIN users u ON m.sender_id = u.id
           WHERE ((sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?))
                 AND m.created_at > ?
           ORDER BY m.created_at ASC""",
        (uid, other["id"], other["id"], uid, since),
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/unread-count")
@login_required
def unread_count():
    db = get_db()
    count = db.execute(
        "SELECT COUNT(*) c FROM messages WHERE receiver_id = ? AND is_read = 0",
        (session["user_id"],),
    ).fetchone()["c"]
    return jsonify({"unread": count})


@app.route("/journal", methods=["GET", "POST"])
@login_required
def journal():
    db = get_db()
    if request.method == "POST":
        mood = request.form.get("mood", "content")
        content = request.form.get("content", "").strip()
        if content:
            db.execute(
                "INSERT INTO journal_entries (user_id, mood, content, created_at) VALUES (?,?,?,?)",
                (session["user_id"], mood, content, datetime.utcnow().isoformat()),
            )
            db.commit()
            flash("Journal entry saved — visible only to you.", "success")
        return redirect(url_for("journal"))
    entries = db.execute(
        "SELECT * FROM journal_entries WHERE user_id = ? ORDER BY created_at DESC LIMIT 30",
        (session["user_id"],),
    ).fetchall()
    return render_template("journal.html", entries=entries, insights=MOOD_INSIGHTS)


@app.route("/quiz", methods=["GET", "POST"])
@login_required
def quiz():
    if request.method == "POST":
        tally = {"secure": 0, "anxious": 0, "avoidant": 0}
        for i in range(len(QUIZ_QUESTIONS)):
            answer = request.form.get(f"q{i}")
            if answer in tally:
                tally[answer] += 1
        winner = max(tally, key=tally.get)
        return render_template("quiz_result.html", result=QUIZ_RESULTS[winner], tally=tally)
    return render_template("quiz.html", questions=QUIZ_QUESTIONS)


@app.route("/api/quote")
def api_quote():
    text, author = random.choice(QUOTES)
    return jsonify({"text": text, "author": author})


@app.route("/u/<username>")
@login_required
def profile(username):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if not user:
        abort(404)
    posts = db.execute(
        "SELECT * FROM posts WHERE user_id = ? ORDER BY created_at DESC LIMIT 10",
        (user["id"],),
    ).fetchall()
    return render_template("profile.html", profile_user=user, posts=posts)


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    db = get_db()
    if request.method == "POST":
        bio = request.form.get("bio", "").strip()[:280]
        db.execute("UPDATE users SET bio = ? WHERE id = ?", (bio, session["user_id"]))
        db.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("settings"))
    user = current_user()
    return render_template("settings.html", user=user)


@app.route("/admin")
@admin_required
def admin_dashboard():
    db = get_db()
    page = max(int(request.args.get("page", 1)), 1)
    stats = {
        "users": db.execute("SELECT COUNT(*) c FROM users").fetchone()["c"],
        "posts": db.execute("SELECT COUNT(*) c FROM posts").fetchone()["c"],
        "comments": db.execute("SELECT COUNT(*) c FROM comments").fetchone()["c"],
        "messages_to_admin": db.execute(
            "SELECT COUNT(*) c FROM messages WHERE receiver_id = ?", (session["user_id"],)
        ).fetchone()["c"],
    }
    total_users = stats["users"]
    total_pages = max((total_users + USERS_PER_PAGE - 1) // USERS_PER_PAGE, 1)
    page = min(page, total_pages)
    offset = (page - 1) * USERS_PER_PAGE
    users = db.execute(
        """SELECT u.*, (SELECT COUNT(*) FROM posts p WHERE p.user_id = u.id) as post_count
           FROM users u ORDER BY u.created_at DESC LIMIT ? OFFSET ?""",
        (USERS_PER_PAGE, offset),
    ).fetchall()
    inbox_partners = db.execute(
        """
        SELECT u.id, u.username,
               (SELECT content FROM messages m2 WHERE m2.sender_id = u.id AND m2.receiver_id = :aid
                ORDER BY m2.created_at DESC LIMIT 1) as last_message,
               (SELECT created_at FROM messages m3 WHERE m3.sender_id = u.id AND m3.receiver_id = :aid
                ORDER BY m3.created_at DESC LIMIT 1) as last_time,
               (SELECT COUNT(*) FROM messages m4 WHERE m4.sender_id = u.id AND m4.receiver_id = :aid AND m4.is_read = 0) as unread
        FROM users u
        WHERE u.id IN (SELECT sender_id FROM messages WHERE receiver_id = :aid)
        ORDER BY last_time DESC
        """,
        {"aid": session["user_id"]},
    ).fetchall()
    recent_posts = db.execute(
        """SELECT p.*, u.username FROM posts p JOIN users u ON p.user_id = u.id
           ORDER BY p.created_at DESC LIMIT 10"""
    ).fetchall()
    return render_template(
        "admin.html", stats=stats, users=users, page=page, total_pages=total_pages,
        inbox_partners=inbox_partners, recent_posts=recent_posts,
    )


@app.route("/admin/user/<int:user_id>/ban", methods=["POST"])
@admin_required
def admin_ban_user(user_id):
    db = get_db()
    target = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not target:
        abort(404)
    if target["is_admin"]:
        flash("You can't ban another admin.", "error")
        return redirect(url_for("admin_dashboard"))
    new_state = 0 if target["is_banned"] else 1
    db.execute("UPDATE users SET is_banned = ? WHERE id = ?", (new_state, user_id))
    db.commit()
    flash(f"{target['username']} has been {'suspended' if new_state else 'reinstated'}.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/user/<int:user_id>/delete", methods=["POST"])
@admin_required
def admin_delete_user(user_id):
    db = get_db()
    target = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not target:
        abort(404)
    if target["is_admin"]:
        flash("You can't delete another admin.", "error")
        return redirect(url_for("admin_dashboard"))
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    flash(f"{target['username']} and all their content was deleted.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/post/<int:post_id>/delete", methods=["POST"])
@admin_required
def admin_delete_post(post_id):
    db = get_db()
    db.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    db.commit()
    flash("Post removed by admin.", "success")
    return redirect(url_for("admin_dashboard"))


@app.errorhandler(403)
def forbidden(e):
    return render_template("error.html", code=403, message="You don't have access to that."), 403


@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404, message="That page doesn't exist."), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", code=500, message="Something went wrong on our end."), 500


if os.environ.get("VERCEL"):
    try:
        init_db()
    except Exception:
        pass

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
