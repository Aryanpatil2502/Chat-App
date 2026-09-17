import sqlite3


DB_PATH = "/app/data/user.db"


def get_db():

    conn = sqlite3.connect(DB_PATH)

    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA foreign_keys = ON")

    return conn


def init_db():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            deleted_at TIMESTAMP DEFAULT NULL
        )
    """)

    existing_columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(users)").fetchall()
    }

    if "deleted_at" not in existing_columns:

        conn.execute(
            "ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP DEFAULT NULL"
        )

    conn.execute("""
        CREATE TABLE IF NOT EXISTS rooms(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_code TEXT UNIQUE NOT NULL,
            created_by INTEGER NOT NULL,
            room_name TEXT NOT NULL,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS room_members(
            room_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            PRIMARY KEY (room_id, user_id),
            FOREIGN KEY (room_id) REFERENCES rooms(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS room_requests(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            UNIQUE(room_id, user_id),
            FOREIGN KEY (room_id) REFERENCES rooms(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_id) REFERENCES rooms(id),
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
        VALUES (?, ?)
        """,
        (username, password_hash)
    )

    conn.commit()

    conn.close()


def get_user(username):

    conn = get_db()

    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE username = ?
        AND deleted_at IS NULL
        """,
        (username,)
    ).fetchone()

    conn.close()

    return user


def delete_user(user_id):

    conn = get_db()

    conn.execute(
        """
        UPDATE users

        SET username = 'deleted_user_' || id,
            password_hash = '',
            deleted_at = CURRENT_TIMESTAMP

        WHERE id = ?
        """,
        (user_id,)
    )

    conn.execute(
        """
        DELETE FROM room_members
        WHERE user_id = ?
        """,
        (user_id,)
    )

    conn.execute(
        """
        DELETE FROM room_requests
        WHERE user_id = ?
        """,
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
        VALUES (?, ?, ?)
        """,
        (room_code, room_name, user_id)
    )

    conn.commit()

    conn.close()


def get_room(room_code):

    conn = get_db()

    room = conn.execute(
        """
        SELECT *
        FROM rooms
        WHERE room_code = ?
        """,
        (room_code,)
    ).fetchone()

    conn.close()

    return room


def delete_room(room_code):

    conn = get_db()

    room = conn.execute(
        """
        SELECT id
        FROM rooms
        WHERE room_code = ?
        """,
        (room_code,)
    ).fetchone()

    if room is None:

        conn.close()

        return False

    room_id = room["id"]

    conn.execute(
        """
        DELETE FROM messages
        WHERE room_id = ?
        """,
        (room_id,)
    )

    conn.execute(
        """
        DELETE FROM room_members
        WHERE room_id = ?
        """,
        (room_id,)
    )

    conn.execute(
        """
        DELETE FROM room_requests
        WHERE room_id = ?
        """,
        (room_id,)
    )

    conn.execute(
        """
        DELETE FROM rooms
        WHERE id = ?
        """,
        (room_id,)
    )

    conn.commit()

    conn.close()

    return True


def add_room_member(room_code, user_id):

    conn = get_db()

    conn.execute(
        """
        INSERT OR IGNORE INTO room_members
        (room_id, user_id)

        SELECT id, ?
        FROM rooms
        WHERE room_code = ?
        """,
        (user_id, room_code)
    )

    conn.commit()

    conn.close()


def remove_room_member(room_code, user_id):

    conn = get_db()

    conn.execute(
        """
        DELETE FROM room_members

        WHERE room_id = (
            SELECT id
            FROM rooms
            WHERE room_code = ?
        )

        AND user_id = ?
        """,
        (room_code, user_id)
    )

    conn.commit()

    conn.close()


def get_room_members(room_code):

    conn = get_db()

    members = conn.execute(
        """
        SELECT
            users.id,
            CASE
                WHEN users.deleted_at IS NOT NULL THEN '[deleted user]'
                ELSE users.username
            END AS username

        FROM room_members

        JOIN rooms
        ON room_members.room_id = rooms.id

        JOIN users
        ON room_members.user_id = users.id

        WHERE rooms.room_code = ?
        """,
        (room_code,)
    ).fetchall()

    conn.close()

    return members


def get_user_rooms(user_id):

    conn = get_db()

    rooms = conn.execute(
        """
        SELECT
            rooms.id,
            rooms.room_code,
            rooms.room_name,
            rooms.created_by

        FROM rooms

        JOIN room_members
        ON rooms.id = room_members.room_id

        WHERE room_members.user_id = ?
        """,
        (user_id,)
    ).fetchall()

    conn.close()

    return rooms


def is_room_member(room_code, user_id):

    conn = get_db()

    member = conn.execute(
        """
        SELECT room_members.user_id

        FROM room_members

        JOIN rooms
        ON room_members.room_id = rooms.id

        WHERE rooms.room_code = ?
        AND room_members.user_id = ?
        """,
        (room_code, user_id)
    ).fetchone()

    conn.close()

    return member is not None


def add_message(room_code, user_id, message):

    conn = get_db()

    conn.execute(
        """
        INSERT INTO messages
        (room_id, user_id, message)

        SELECT id, ?, ?

        FROM rooms
        WHERE room_code = ?
        """,
        (user_id, message, room_code)
    )

    conn.commit()

    conn.close()


def get_messages(room_code):

    conn = get_db()

    messages = conn.execute(
        """
        SELECT
            CASE
                WHEN users.deleted_at IS NOT NULL THEN '[deleted user]'
                ELSE users.username
            END AS username,
            messages.message,
            messages.created_at

        FROM messages

        JOIN rooms
        ON messages.room_id = rooms.id

        JOIN users
        ON messages.user_id = users.id

        WHERE rooms.room_code = ?

        ORDER BY messages.id ASC
        """,
        (room_code,)
    ).fetchall()

    conn.close()

    return messages

def add_room_request(room_code, user_id):

    conn = get_db()

    room = conn.execute(
        """
        SELECT id
        FROM rooms
        WHERE room_code = ?
        """,
        (room_code,)
    ).fetchone()

    if room is None:

        conn.close()

        return None

    room_id = room["id"]

    existing_request = conn.execute(
        """
        SELECT id, status
        FROM room_requests

        WHERE room_id = ?
        AND user_id = ?
        """,
        (room_id, user_id)
    ).fetchone()

    if existing_request:

        if existing_request["status"] == "pending":

            request_id = existing_request["id"]

        else:

            conn.execute(
                """
                UPDATE room_requests

                SET status = 'pending'

                WHERE id = ?
                """,
                (existing_request["id"],)
            )

            request_id = existing_request["id"]

    else:

        cursor = conn.execute(
            """
            INSERT INTO room_requests
            (room_id, user_id, status)

            VALUES (?, ?, 'pending')
            """,
            (room_id, user_id)
        )

        request_id = cursor.lastrowid

    conn.commit()

    conn.close()

    return request_id


def get_pending_requests(room_code):

    conn = get_db()

    requests = conn.execute(
        """
        SELECT
            room_requests.id,
            users.id AS user_id,
            users.username

        FROM room_requests

        JOIN rooms
        ON room_requests.room_id = rooms.id

        JOIN users
        ON room_requests.user_id = users.id

        WHERE rooms.room_code = ?

        AND room_requests.status = 'pending'
        """,
        (room_code,)
    ).fetchall()

    conn.close()

    return requests


def get_room_from_request(request_id):

    conn = get_db()

    req = conn.execute(
        """
        SELECT
            room_requests.id,
            room_requests.room_id,
            room_requests.user_id,
            room_requests.status,
            rooms.room_code,
            rooms.created_by

        FROM room_requests

        JOIN rooms
        ON room_requests.room_id = rooms.id

        WHERE room_requests.id = ?
        """,
        (request_id,)
    ).fetchone()

    conn.close()

    return req


def update_room_request(request_id, status):

    conn = get_db()

    req = conn.execute(
        """
        SELECT
            room_id,
            user_id

        FROM room_requests

        WHERE id = ?
        """,
        (request_id,)
    ).fetchone()

    if req is None:

        conn.close()

        return None

    conn.execute(
        """
        UPDATE room_requests

        SET status = ?

        WHERE id = ?
        """,
        (status, request_id)
    )

    conn.commit()

    conn.close()

    return req