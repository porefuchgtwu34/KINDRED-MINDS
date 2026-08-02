import os
import sys

# Ensure the nested package path is available
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "kindred-minds"))

# Force /tmp for SQLite on Vercel before importing
os.environ.setdefault("VERCEL", "1")

# Monkey-patch DB path before the nested module defines it
import app as nested  # noqa: E402  -- this will load kindred-minds/app.py if path is set

# The nested app defines `app`
from app import app  # re-export

# Override DB after import if needed
if hasattr(nested, "DB_PATH"):
    nested.DB_PATH = "/tmp/kindred.db"
    if hasattr(nested, "init_db"):
        nested.init_db()
