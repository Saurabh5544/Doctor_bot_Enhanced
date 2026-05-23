"""
Database module for Medical Chatbot.
Uses SQLite for user management and chat history persistence.
"""

import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "medical_chatbot.db")


def get_db():
    """Get a database connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initialize the database with required tables."""
    conn = get_db()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)

    # Chat history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_id TEXT NOT NULL,
            session_title TEXT DEFAULT 'New Chat',
            role TEXT NOT NULL CHECK(role IN ('user', 'bot')),
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # Index for faster lookups
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_chat_user_session 
        ON chat_history(user_id, session_id)
    """)

    conn.commit()
    conn.close()
    print(f"[OK] Database initialized at: {DB_PATH}")


# ─── User Management ───────────────────────────────────────────

def create_user(username, email, password):
    """Create a new user. Returns (success: bool, message: str)."""
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, generate_password_hash(password))
        )
        conn.commit()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError as e:
        if "username" in str(e):
            return False, "Username already taken."
        elif "email" in str(e):
            return False, "Email already registered."
        return False, "Registration failed."
    finally:
        conn.close()


def authenticate_user(email, password):
    """Authenticate user by email and password. Returns user dict or None."""
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()

    if user and check_password_hash(user["password_hash"], password):
        # Update last login
        conn = get_db()
        conn.execute(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (datetime.now(), user["id"])
        )
        conn.commit()
        conn.close()
        return dict(user)
    return None


def get_user_by_id(user_id):
    """Get user by ID. Returns user dict or None."""
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return dict(user) if user else None


# ─── Chat History Management ───────────────────────────────────

def save_message(user_id, session_id, role, message, session_title=None):
    """Save a chat message to the database."""
    conn = get_db()
    if session_title:
        conn.execute(
            "INSERT INTO chat_history (user_id, session_id, session_title, role, message) VALUES (?, ?, ?, ?, ?)",
            (user_id, session_id, session_title, role, message)
        )
    else:
        conn.execute(
            "INSERT INTO chat_history (user_id, session_id, role, message) VALUES (?, ?, ?, ?)",
            (user_id, session_id, role, message)
        )
    conn.commit()
    conn.close()


def get_chat_sessions(user_id):
    """Get all chat sessions for a user (most recent first)."""
    conn = get_db()
    sessions = conn.execute("""
        SELECT session_id, 
               MAX(session_title) as title,
               MIN(timestamp) as started_at,
               MAX(timestamp) as last_message_at,
               COUNT(*) as message_count
        FROM chat_history
        WHERE user_id = ?
        GROUP BY session_id
        ORDER BY last_message_at DESC
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(s) for s in sessions]


def get_session_messages(user_id, session_id):
    """Get all messages for a specific chat session."""
    conn = get_db()
    messages = conn.execute("""
        SELECT role, message, timestamp
        FROM chat_history
        WHERE user_id = ? AND session_id = ?
        ORDER BY timestamp ASC
    """, (user_id, session_id)).fetchall()
    conn.close()
    return [dict(m) for m in messages]


def delete_chat_session(user_id, session_id):
    """Delete a specific chat session."""
    conn = get_db()
    conn.execute(
        "DELETE FROM chat_history WHERE user_id = ? AND session_id = ?",
        (user_id, session_id)
    )
    conn.commit()
    conn.close()


def delete_all_chat_history(user_id):
    """Delete all chat history for a user."""
    conn = get_db()
    conn.execute(
        "DELETE FROM chat_history WHERE user_id = ?",
        (user_id,)
    )
    conn.commit()
    conn.close()


# Initialize DB on import
init_db()
