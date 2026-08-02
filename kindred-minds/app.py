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

# Minimal stub to restore deployability - full routes restored in next step if needed
@app.route("/")
def home():
    return "Kindred Minds is deploying. Full app restoring..."

if os.environ.get("VERCEL"):
    pass

if __name__ == "__main__":
    app.run(debug=True, port=5000)
