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

    #Rooms table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_code TEXT UNIQUE NOT NULL,
        created_by INTEGER NOT NULL,
        room_name TEXT NOT NULL,
        FOREIGN KEY (created_by) REFERENCES users(id)
        )
    """)

    #Room membership table 
    conn.execute("""
        CREATE TABLE IF NOT EXISTS room_members (
        room_code TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        PRIMARY KEY (room_code, user_id),
        FOREIGN KEY (room_code) REFERENCES rooms(room_code),
        FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    #Messages table 
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_code TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        content TEXT NOT NULL,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (room_code) REFERENCES rooms(room_code),
        FOREIGN KEY (user_id) REFERENCES users(id)
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

def add_room(room_code, room_name, user_id):
    conn = get_db()

    conn.execute(
        """
        INSERT INTO rooms
        (room_code, room_name, created_by)
        VALUES (?,?,?)
        """,
        (room_code, room_name, user_id)
    )

    conn.commit()
    conn.close()

def get_room(room_code):
    conn = get_db()

    room = conn.execute(
        """
        SELECT * FROM rooms
        WHERE room_code = ?
        """,
        (room_code,)
    ).fetchone()

    conn.close()

    return room


def get_all_rooms():
    conn = get_db()

    rooms = conn.execute(
        """
        SELECT * FROM rooms
        ORDER BY id DESC
        """
    ).fetchall()

    conn.close()

    return rooms


def add_member(room_code, user_id):
    conn = get_db()

    conn.execute(
        """
        INSERT OR IGNORE INTO room_members (room_code, user_id)
        VALUES (?, ?)
        """,
        (room_code, user_id)
    )

    conn.commit()
    conn.close()


def get_hosted_rooms(user_id):
    conn = get_db()

    rooms = conn.execute(
        """
        SELECT * FROM rooms
        WHERE created_by = ?
        ORDER BY id DESC
        """,
        (user_id,)
    ).fetchall()

    conn.close()

    return rooms


def get_joined_rooms(user_id):
    conn = get_db()

    rooms = conn.execute(
        """
        SELECT r.* FROM rooms r
        JOIN room_members m ON r.room_code = m.room_code
        WHERE m.user_id = ? AND r.created_by != ?
        ORDER BY r.id DESC
        """,
        (user_id, user_id)
    ).fetchall()

    conn.close()

    return rooms


def add_message(room_code, user_id, username, content):
    conn = get_db()

    conn.execute(
        """
        INSERT INTO messages (room_code, user_id, username, content)
        VALUES (?, ?, ?, ?)
        """,
        (room_code, user_id, username, content)
    )

    conn.commit()
    conn.close()


def get_messages(room_code):
    conn = get_db()

    messages = conn.execute(
        """
        SELECT * FROM messages
        WHERE room_code = ?
        ORDER BY id ASC
        """,
        (room_code,)
    ).fetchall()

    conn.close()

    return messages


def delete_room(room_code, user_id):
   
    conn = get_db()
 
    room = conn.execute(
        "SELECT * FROM rooms WHERE room_code = ?",
        (room_code,)
    ).fetchone()
 
    if room is None or room["created_by"] != user_id:
        conn.close()
        return False
 
    conn.execute("DELETE FROM messages WHERE room_code = ?", (room_code,))
    conn.execute("DELETE FROM room_members WHERE room_code = ?", (room_code,))
    conn.execute("DELETE FROM rooms WHERE room_code = ?", (room_code,))
 
    conn.commit()
    conn.close()
 
    return True