"""
auth/db.py
SQLite database layer for Car Lease Analyzer.
Creates and manages the users.db file in the project root.
No external packages required — sqlite3 is built into Python.

Data is stored in: users.db  (same folder as streamlit_app.py)
Table: users  (email, name, password_hash, created_at)
"""

import sqlite3
import hashlib
from pathlib import Path

# ── users.db sits at project root (parent of the auth/ folder) ───────────────
DB_PATH = Path(__file__).resolve().parent.parent / "users.db"


def _hash(pw: str) -> str:
    """SHA-256 hash — defined here to avoid circular imports with user_auth."""
    return hashlib.sha256(pw.encode()).hexdigest()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    return conn


def init_db():
    """
    Called once at app startup (from init_auth_session).
    - Creates users.db if it doesn't exist
    - Creates the users table if it doesn't exist
    - Seeds two demo accounts on a brand-new database
    """
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                email         TEXT PRIMARY KEY,
                name          TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at    TEXT NOT NULL
            )
        """)
        conn.commit()

        # Only seed when the table is completely empty
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if count == 0:
            demo_users = [
                ("akhil@test.com", "Akhilesh",  _hash("password123"), "2025-01-01"),
                ("demo@demo.com",   "Demo User", _hash("demo123"),      "2025-01-01"),
            ]
            conn.executemany(
                "INSERT OR IGNORE INTO users "
                "(email, name, password_hash, created_at) VALUES (?,?,?,?)",
                demo_users,
            )
            conn.commit()


# ── CRUD helpers ──────────────────────────────────────────────────────────────

def get_user(email: str) -> dict | None:
    """Return user row as dict, or None if not found."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
    return dict(row) if row else None


def email_exists(email: str) -> bool:
    """True if email is already registered."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM users WHERE email = ?", (email,)
        ).fetchone()
    return row is not None


def create_user(email: str, name: str, password_hash: str, created_at: str) -> bool:
    """Insert a new user. Returns True on success, False if email already taken."""
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT INTO users (email, name, password_hash, created_at) "
                "VALUES (?,?,?,?)",
                (email, name, password_hash, created_at),
            )
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
