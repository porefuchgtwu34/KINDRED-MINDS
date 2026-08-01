# Kindred Minds

A community platform about love, relationships, behaviour & psychology —
Flask + SQLite backend, hand-built HTML/CSS/JS frontend (no frameworks).

## Features

- **Accounts** — register/login with username *or* email + password (hashed with
  Werkzeug's `generate_password_hash`), sessions, logout.
- **Password reset** — forgot-password flow with time-limited tokens. Since this
  demo has no outbound email server, the reset link is displayed on-screen
  (clearly labelled "demo mode"); wire up Flask-Mail or an API like Postmark/SendGrid
  to actually email it in production.
- **Public community feed** — posts with categories (dating, breakups, family,
  self-growth, advice-wanted...), threaded public comments so people can advise
  each other, pagination (5 posts/page).
- **Private one-on-one messaging** — message any user by **username only** (no
  phone numbers / real names required). Near-real-time via lightweight polling
  (checks for new messages every 3 seconds) — no extra infrastructure needed.
  Want true push-based real-time? See "Upgrading to WebSockets" below.
- **Admin dashboard** — member stats, an inbox of everyone who has messaged the
  admin account (reply inline via the same chat UI), suspend/reinstate/delete
  users, delete any post, paginated member table.
- **Personal mood journal** — private per-user journal with a short rule-based
  psychological reflection per mood (not a diagnosis — just a nudge to think).
- **Attachment-style quiz** — 5 short questions, scored client-side-free (all
  server-side), maps to secure/anxious/avoidant with plain-language takeaways.
- **Quotes API** — `/api/quote` returns a random relationship/psychology quote (JSON).
- **Responsive design** — sidebar nav collapses to a top bar on mobile; chat,
  feed, and admin table all reflow down to small screens.

## Getting started

```bash
cd kindred
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000**. The SQLite database (`kindred.db`) is created
automatically on first run, along with a seeded admin account:

```
username: admin
password: admin123
```

**Change that password immediately** (register a new admin manually and demote/
delete the seed account, or use the reset-password flow) before deploying anywhere
public.

## Project structure

```
kindred/
├── app.py                  # Flask app: routes, models (raw SQL), auth, admin
├── requirements.txt
├── kindred.db               # created on first run
├── templates/
│   ├── base.html            # shell: sidebar nav (logged in) / header (public)
│   ├── index.html           # marketing landing page
│   ├── login.html / register.html
│   ├── forgot_password.html / reset_password.html
│   ├── feed.html / post.html          # public posts + comments
│   ├── messages.html / conversation.html  # private messaging
│   ├── journal.html         # private mood journal
│   ├── quiz.html / quiz_result.html   # attachment quiz
│   ├── profile.html / settings.html
│   ├── admin.html           # admin dashboard
│   ├── error.html           # 403/404/500
│   └── _flash.html / _pagination.html  # partials
└── static/
    ├── css/style.css        # full design system
    └── js/main.js           # polling chat + unread badge
```

## Security notes for production

- Set a real `KINDRED_SECRET_KEY` environment variable (never ship the dev default).
- Put this behind HTTPS; set `SESSION_COOKIE_SECURE = True` in `app.config`.
- Add rate limiting on `/login`, `/register`, and `/forgot-password` (e.g. Flask-Limiter)
  to slow down brute force / enumeration attempts.
- Move off SQLite to Postgres/MySQL if you expect concurrent write load.
- Add server-side content moderation / profanity filtering if opening this to the public.

## Upgrading to WebSockets (optional)

The chat currently polls every 3 seconds, which is simple, needs zero extra
infrastructure, and works everywhere. For instant push-based delivery instead:

```bash
pip install flask-socketio eventlet
```

Replace the `/api/messages/<username>/poll` + `setInterval` pattern in
`main.js` with a Socket.IO client that joins a room per conversation
(`f"dm_{min(id1,id2)}_{max(id1,id2)}"`) and emits/receives on message send.
Everything else (auth, database schema, templates) stays the same.
