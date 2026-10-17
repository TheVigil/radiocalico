import os
import sqlite3
from datetime import datetime, timezone

from flask import Flask, g, jsonify, request

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "radiocalico.db"))

app = Flask(__name__)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS song_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT NOT NULL,
            artist TEXT NOT NULL,
            title TEXT NOT NULL,
            album TEXT NOT NULL,
            rating TEXT NOT NULL CHECK (rating IN ('up', 'down')),
            created_at TEXT NOT NULL,
            UNIQUE (client_id, artist, title, album)
        )
        """
    )
    conn.commit()
    conn.close()


@app.get("/api/health")
def health():
    return jsonify({"ok": True})


@app.get("/api/items")
def list_items():
    db = get_db()
    rows = db.execute("SELECT * FROM items ORDER BY id DESC").fetchall()
    return jsonify([dict(row) for row in rows])


@app.post("/api/items")
def create_item():
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    if not name or not isinstance(name, str):
        return jsonify({"error": "name is required"}), 400
    db = get_db()
    cur = db.execute(
        "INSERT INTO items (name, created_at) VALUES (?, ?)",
        (name, datetime.now(timezone.utc).isoformat()),
    )
    db.commit()
    row = db.execute("SELECT * FROM items WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201


@app.get("/api/ratings")
def get_rating():
    client_id = request.args.get("client_id")
    artist = request.args.get("artist")
    title = request.args.get("title")
    album = request.args.get("album")
    if not all([client_id, artist, title, album]):
        return jsonify({"error": "client_id, artist, title, and album are required"}), 400

    db = get_db()
    row = db.execute(
        "SELECT rating FROM song_ratings WHERE client_id = ? AND artist = ? AND title = ? AND album = ?",
        (client_id, artist, title, album),
    ).fetchone()
    return jsonify({"rating": row["rating"] if row else None})


@app.post("/api/ratings")
def create_rating():
    data = request.get_json(silent=True) or {}
    client_id = data.get("client_id")
    artist = data.get("artist")
    title = data.get("title")
    album = data.get("album")
    rating = data.get("rating")

    if not all(isinstance(v, str) and v for v in [client_id, artist, title, album]):
        return jsonify({"error": "client_id, artist, title, and album are required"}), 400
    if rating not in ("up", "down"):
        return jsonify({"error": "rating must be 'up' or 'down'"}), 400

    db = get_db()
    try:
        db.execute(
            "INSERT INTO song_ratings (client_id, artist, title, album, rating, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (client_id, artist, title, album, rating, datetime.now(timezone.utc).isoformat()),
        )
        db.commit()
    except sqlite3.IntegrityError:
        existing = db.execute(
            "SELECT rating FROM song_ratings WHERE client_id = ? AND artist = ? AND title = ? AND album = ?",
            (client_id, artist, title, album),
        ).fetchone()
        return jsonify({"error": "already rated", "rating": existing["rating"] if existing else None}), 409

    return jsonify({"rating": rating}), 201


init_db()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=True)
