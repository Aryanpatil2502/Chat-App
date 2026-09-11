import sqlite3
import json

DB_PATH = "user.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()

    #Users table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
            )
        """)

    conn.commit()
    conn.close()

def add_user(username, password_hash):
    conn = get_db()
    conn.execute(
        """
        INSERT INTO users (username, password_hash)
        values (?,?)
        """,
        (username, password_hash)
    )
    conn.commit()
    conn.close()

def get_user(username):
    conn = get_db()

    user = conn.execute(
        """
        SELECT * FROM users
        WHERE username = ?
        """,
        (username,)
    ).fetchone()

    conn.close()

    return user

def delete_user(user_id):

    conn = get_db()

    conn.execute(
        "DELETE FROM users WHERE id = ?",
        (user_id,)
    )

    conn.commit()
    conn.close()
