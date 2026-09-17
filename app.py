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



load_dotenv()

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", os.urandom(32))

socketio = SocketIO(app)

init_db()


@socketio.on("connect")
def handle_connect():

    user_id = session.get("user_id")

    if user_id is None:

        return

    join_room(f"user_{user_id}")



@app.route("/")
def lobby():

    if "user_id" not in session:

        return redirect(url_for("login"))

    return render_template("lobby.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":

        return render_template("auth/login.html")

    username = request.form["username"]
    password = request.form["password"]

    user = get_user(username)

    if user is None:

        return render_template(
            "auth/login.html",
            error="Invalid username or password"
        )

    if not check_password_hash(user["password_hash"], password):

        return render_template(
            "auth/login.html",
            error="Invalid username or password"
        )

    session["user_id"] = user["id"]

    session["username"] = user["username"]

    return redirect(url_for("lobby"))


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":

        return render_template("auth/register.html")

    username = request.form["username"]

    password = request.form["password"]

    confirm_password = request.form["confirm_password"]

    if password != confirm_password:

        return render_template(
            "auth/register.html",
            error="Passwords do not match"
        )

    existing_user = get_user(username)

    if existing_user:

        return render_template(
            "auth/register.html",
            error="Username already exists"
        )

    password_hash = generate_password_hash(password)

    add_user(
        username,
        password_hash
    )

    return redirect(url_for("login"))


@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


@app.route("/delete-account", methods=["POST"])
def delete_account():

    if "user_id" not in session:

        return redirect(url_for("login"))

    user_id = session["user_id"]

    delete_user(user_id)

    session.clear()

    return redirect(url_for("register"))


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

        is_creator=(room_data["created_by"] == user_id),

        user_id=user_id,

        pending_requests=pending_requests
    )



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


@socketio.on("leave_room")
def leave_room_event(room_code):

    if "user_id" not in session:

        return {
            "success": False,
            "error": "Not logged in"
        }

    user_id = session["user_id"]

    room = get_room(room_code)

    if room is None:

        return {
            "success": False,
            "error": "Room does not exist"
        }

    if not is_room_member(
        room_code,
        user_id
    ):

        return {
            "success": False,
            "error": "You are not a member of this room"
        }

    if room["created_by"] == user_id:

        return {
            "success": False,
            "error": "Creator cannot leave the room. Delete it instead."
        }

    remove_room_member(
        room_code,
        user_id
    )

    leave_room(room_code)

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

    if room["created_by"] != session["user_id"]:

        return {
            "success": False,
            "error": "Only the creator can kick members"
        }

    if user_id == room["created_by"]:

        return {
            "success": False,
            "error": "Creator cannot be kicked"
        }

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


    socketio.emit(
        "kicked",
        {
            "room_code": room_code
        },
        to=f"user_{user_id}"
    )

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


@app.route("/profile")
def profile():

    if "user_id" not in session:

        return redirect(url_for("login"))

    user_id = session["user_id"]

    rooms = get_user_rooms(user_id)

    hosted_rooms = [
        room for room in rooms
        if room["created_by"] == user_id
    ]

    joined_rooms = [
        room for room in rooms
        if room["created_by"] != user_id
    ]

    return render_template(
        "profile.html",
        username=session["username"],
        hosted_rooms=hosted_rooms,
        joined_rooms=joined_rooms
    )


if __name__ == "__main__":

    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=True
    )