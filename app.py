import random
import string
import os

from flask import (
    Flask,
    render_template,
    request,
    session,
    redirect,
    url_for
)

from dotenv import load_dotenv

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from flask_socketio import (
    SocketIO,
    join_room,
    leave_room
)

from database import (
    init_db,

    add_user,
    get_user,
    delete_user,

    add_room,
    get_room,
    delete_room,

    add_room_member,
    remove_room_member,
    is_room_member,

    get_room_members,
    get_user_rooms,

    add_message,
    get_messages,

    add_room_request,
    get_pending_requests,
    get_room_from_request,
    update_room_request
)


# --------------------------------------------------
# APP SETUP
# --------------------------------------------------

load_dotenv()

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY")

socketio = SocketIO(app)


# --------------------------------------------------
# CONNECT
# --------------------------------------------------
# Every client joins a private room keyed to their own user id the
# moment they connect - not just once they open a specific chat room.
# This is what lets us push "someone wants to join your room" or
# "you've been kicked" to a user regardless of which page they're on
# (e.g. still sitting in the lobby, not inside any room yet).

@socketio.on("connect")
def handle_connect():

    user_id = session.get("user_id")

    if user_id is None:

        return

    join_room(f"user_{user_id}")


# --------------------------------------------------
# LOBBY
# --------------------------------------------------

@app.route("/")
def lobby():

    if "user_id" not in session:

        return redirect(url_for("login"))

    return render_template("lobby.html")


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":

        return render_template("login.html")

    username = request.form["username"]
    password = request.form["password"]

    user = get_user(username)

    if user is None:

        return redirect(url_for("register"))

    if not check_password_hash(user["password_hash"], password):
        return "Invalid username or password"

    session["user_id"] = user["id"]

    session["username"] = user["username"]

    return redirect(url_for("lobby"))


# --------------------------------------------------
# REGISTER
# --------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":

        return render_template("register.html")

    username = request.form["username"]

    password = request.form["password"]

    confirm_password = request.form["confirm_password"]

    if password != confirm_password:

        return render_template(
            "register.html",
            error="Passwords do not match"
        )

    existing_user = get_user(username)

    if existing_user:

        return render_template(
            "register.html",
            error="Username already exists"
        )

    password_hash = generate_password_hash(password)

    add_user(
        username,
        password_hash
    )

    return redirect(url_for("login"))


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# --------------------------------------------------
# DELETE ACCOUNT
# --------------------------------------------------

@app.route("/delete-account", methods=["POST"])
def delete_account():

    if "user_id" not in session:

        return redirect(url_for("login"))

    user_id = session["user_id"]

    delete_user(user_id)

    session.clear()

    return redirect(url_for("register"))


# --------------------------------------------------
# CREATE ROOM
# --------------------------------------------------

@socketio.on("create_room")
def create_room_event(room_name):

    if "user_id" not in session:

        return {
            "success": False,
            "error": "Not logged in"
        }

    characters = string.ascii_uppercase + string.digits

    while True:

        room_code = ""

        for i in range(5):

            room_code += random.choice(characters)

        if get_room(room_code) is None:

            break

    user_id = session["user_id"]

    add_room(
        room_code,
        room_name,
        user_id
    )

    add_room_member(
        room_code,
        user_id
    )

    join_room(room_code)

    return {
        "success": True,
        "room_code": room_code
    }


# --------------------------------------------------
# JOIN ROOM
# --------------------------------------------------

@socketio.on("join_room")
def join_existing_room(room_code):

    if "user_id" not in session:

        return {
            "success": False,
            "error": "Not logged in"
        }

    user_id = session["user_id"]

    username = session["username"]

    room = get_room(room_code)

    if room is None:

        return {
            "success": False,
            "error": "Room does not exist"
        }

    # Already a member
    if is_room_member(
        room_code,
        user_id
    ):

        join_room(room_code)

        members = get_room_members(room_code)

        socketio.emit(
            "room_members",
            {
                "members": [
                    {
                        "id": member["id"],
                        "username": member["username"]
                    }

                    for member in members
                ]
            },
            to=room_code
        )

        return {
            "success": True,
            "room_code": room_code
        }

    # Creator
    if room["created_by"] == user_id:

        add_room_member(
            room_code,
            user_id
        )

        join_room(room_code)

        return {
            "success": True,
            "room_code": room_code
        }

    # Normal user needs approval
    request_id = add_room_request(
        room_code,
        user_id
    )

    if request_id is None:

        return {
            "success": False,
            "error": "Could not create join request"
        }

    socketio.emit(
        "join_request",
        {
            "request_id": request_id,
            "user_id": user_id,
            "username": username,
            "room_code": room_code
        },
        to=f"user_{room['created_by']}"
    )

    return {
        "success": False,
        "pending": True,
        "message": "Join request sent to creator"
    }


# --------------------------------------------------
# ROOM PAGE
# --------------------------------------------------

@app.route("/room/<room_code>")
def room(room_code):

    if "user_id" not in session:

        return redirect(url_for("login"))

    room_data = get_room(room_code)

    if room_data is None:

        return "Room does not exist"

    user_id = session["user_id"]

    if not is_room_member(
        room_code,
        user_id
    ):

        return "You are not a member of this room"

    members = get_room_members(room_code)

    messages = get_messages(room_code)

    pending_requests = []

    if room_data["created_by"] == user_id:

        pending_requests = get_pending_requests(
            room_code
        )

    return render_template(
        "room.html",

        room_code=room_code,

        room_name=room_data["room_name"],

        members=members,

        messages=messages,

        creator_id=room_data["created_by"],

        pending_requests=pending_requests
    )


# --------------------------------------------------
# SEND MESSAGE
# --------------------------------------------------

@socketio.on("send_message")
def send_message(data):

    if "user_id" not in session:

        return {
            "success": False,
            "error": "Not logged in"
        }

    room_code = data["room_code"]

    message = data["message"]

    user_id = session["user_id"]

    # Security check:
    # user must actually be a member
    if not is_room_member(
        room_code,
        user_id
    ):

        return {
            "success": False,
            "error": "You are not a member of this room"
        }

    if not message.strip():

        return {
            "success": False,
            "error": "Message cannot be empty"
        }

    add_message(
        room_code,
        user_id,
        message
    )

    socketio.emit(
        "receive_message",
        {
            "username": session["username"],
            "message": message
        },
        to=room_code
    )

    return {
        "success": True
    }


# --------------------------------------------------
# DELETE ROOM
# --------------------------------------------------

@socketio.on("delete_room")
def delete_room_event(room_code):

    if "user_id" not in session:

        return {
            "success": False,
            "error": "Not logged in"
        }

    room = get_room(room_code)

    if room is None:

        return {
            "success": False,
            "error": "Room does not exist"
        }

    # Only creator
    if room["created_by"] != session["user_id"]:

        return {
            "success": False,
            "error": "Only the creator can delete this room"
        }

    delete_room(room_code)

    socketio.emit(
        "room_deleted",
        to=room_code
    )

    return {
        "success": True
    }


# --------------------------------------------------
# KICK MEMBER
# --------------------------------------------------

@socketio.on("kick_member")
def kick_member(data):

    if "user_id" not in session:

        return {
            "success": False,
            "error": "Not logged in"
        }

    room_code = data["room_code"]

    user_id = data["user_id"]

    room = get_room(room_code)

    if room is None:

        return {
            "success": False,
            "error": "Room does not exist"
        }

    # Only creator can kick
    if room["created_by"] != session["user_id"]:

        return {
            "success": False,
            "error": "Only the creator can kick members"
        }

    # Creator cannot kick themselves
    if user_id == room["created_by"]:

        return {
            "success": False,
            "error": "Creator cannot be kicked"
        }

    # Check target is actually a member
    if not is_room_member(
        room_code,
        user_id
    ):

        return {
            "success": False,
            "error": "User is not a member"
        }

    remove_room_member(
        room_code,
        user_id
    )

    # Notify the kicked user directly via their personal room -
    # works no matter which page they're currently on
    socketio.emit(
        "kicked",
        {
            "room_code": room_code
        },
        to=f"user_{user_id}"
    )

    # Update member list for everyone still inside
    members = get_room_members(room_code)

    socketio.emit(
        "room_members",
        {
            "members": [
                {
                    "id": member["id"],
                    "username": member["username"]
                }

                for member in members
            ]
        },
        to=room_code
    )

    return {
        "success": True
    }


# --------------------------------------------------
# HANDLE JOIN REQUEST
# --------------------------------------------------

@socketio.on("handle_join_request")
def handle_join_request(data):

    if "user_id" not in session:

        return {
            "success": False,
            "error": "Not logged in"
        }

    request_id = data["request_id"]

    action = data["action"]

    request_data = get_room_from_request(
        request_id
    )

    if request_data is None:

        return {
            "success": False,
            "error": "Request does not exist"
        }

    # Only creator can accept/reject
    if request_data["created_by"] != session["user_id"]:

        return {
            "success": False,
            "error": "Only the creator can handle join requests"
        }

    if request_data["status"] != "pending":

        return {
            "success": False,
            "error": "Request has already been handled"
        }

    # ACCEPT
    if action == "accept":

        add_room_member(
            request_data["room_code"],
            request_data["user_id"]
        )

        update_room_request(
            request_id,
            "accepted"
        )

        socketio.emit(
            "join_accepted",
            {
                "room_code": request_data["room_code"]
            },
            to=f"user_{request_data['user_id']}"
        )

        members = get_room_members(
            request_data["room_code"]
        )

        socketio.emit(
            "room_members",
            {
                "members": [
                    {
                        "id": member["id"],
                        "username": member["username"]
                    }

                    for member in members
                ]
            },
            to=request_data["room_code"]
        )

        return {
            "success": True
        }

    # REJECT
    if action == "reject":

        update_room_request(
            request_id,
            "rejected"
        )

        socketio.emit(
            "join_rejected",
            {
                "room_code": request_data["room_code"]
            },
            to=f"user_{request_data['user_id']}"
        )

        return {
            "success": True
        }

    return {
        "success": False,
        "error": "Invalid action"
    }


# --------------------------------------------------
# PROFILE
# --------------------------------------------------

@app.route("/profile")
def profile():

    if "user_id" not in session:

        return redirect(url_for("login"))

    rooms = get_user_rooms(
        session["user_id"]
    )

    return render_template(
        "profile.html",
        username=session["username"],
        rooms=rooms
    )


# --------------------------------------------------
# RUN APP
# --------------------------------------------------

if __name__ == "__main__":

    init_db()

    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=True
    )