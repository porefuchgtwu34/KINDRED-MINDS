# Kindred Minds

A community about love, relationships & psychology.

[![Deployed on Vercel](https://vercelbadge.vercel.app/api/porefuchgtwu34/KINDRED-MINDS)](https://kindred-minds.vercel.app)

**Live:** [https://kindred-minds.vercel.app](https://kindred-minds.vercel.app)

**Deployments / status:** [Vercel Dashboard](https://vercel.com/dashboard)

---

## Stack

- Flask 3 + SQLite
- Deployed on Vercel (Python serverless)

## Local run

```bash
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

Default admin (change immediately):

```
username: admin
password: admin123
```

## Production notes

- Set `KINDRED_SECRET_KEY` in Vercel environment variables.
- SQLite on Vercel uses `/tmp` and is **ephemeral** (fine for demos).
