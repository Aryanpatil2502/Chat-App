import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room
from werkzeug.security import generate_password_hash, check_password_hash
from database import (init_db, add_user, get_user, delete_user, add_room, get_room, get_all_rooms, add_member, get_hosted_rooms, get_joined_rooms, add_message, get_messages, delete_room)
import random
import string

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

socketio = SocketIO(app)

init_db()

@app.route('/')
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    rooms = get_all_rooms()
    return render_template('lobby.html', rooms=rooms)

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

    add_user(username, password_hash)

    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template("auth/login.html")

    username = request.form["username"]
    password = request.form["password"]

    user = get_user(username)

    if user is None:
        return redirect(url_for("register"))

    if not check_password_hash(user["password_hash"], password):
        return "Invalid username or password"

    session["user_id"] = user["id"]
    session["username"] = user["username"]

    return redirect(url_for("home"))

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


@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    hosted_rooms = get_hosted_rooms(user_id)
    joined_rooms = get_joined_rooms(user_id)

    return render_template(
        "profile.html",
        username=session.get("username"),
        hosted_rooms=hosted_rooms,
        joined_rooms=joined_rooms
    )


@app.route('/room/<code>')
def room(code):
    if "user_id" not in session:
        return redirect(url_for("login"))

    room_row = get_room(code)

    if room_row is None:
        return redirect(url_for("home"))

    is_creator = room_row["created_by"] == session["user_id"]

    return render_template(
        'room.html',
        room_code=code,
        room_name=room_row["room_name"],
        is_creator=is_creator
    )


@socketio.on('create_room')
def handle_create_room(data):

    if "user_id" not in session:
        emit('join_error', {"error": "Not logged in"})
        return

    room_name = data.get("name", "Untitled Room")

    characters = string.ascii_uppercase + string.digits

    while True:
        room_code = ""

        for i in range(5):
            room_code += random.choice(characters)

        if get_room(room_code) is None:
            break

    user_id = session["user_id"]

    add_room(room_code, room_name, user_id)

    emit('room_created', {"code": room_code})


@socketio.on('send_message')
def handle_send_message(data):

    code = data["room"]
    message = data["message"]
    user_id = session.get("user_id")
    username = session.get("username", "Unknown")

    if get_room(code) is None:
        return

    add_message(code, user_id, username, message)

    emit('new_message', {
        "username": username,
        "message": message
    }, room=code)

@socketio.on('join_room_event')
def handle_join_room(data):

    code = data['code']

    if get_room(code) is None:
        emit('join_error', {"error": "Room not found"})
        return

    join_room(code)

    user_id = session.get("user_id")
    if user_id:
        add_member(code, user_id)

    history = get_messages(code)
    emit('chat_history', {
        "messages": [
            {"username": m["username"], "message": m["content"]}
            for m in history
        ]
    })

    username = session.get("username", "Unknown")

    emit('user_joined', {"username": username}, room=code)


@socketio.on('delete_room_event')
def handle_delete_room(data):

    code = data['code']
    user_id = session.get("user_id")

    if user_id is None:
        emit('delete_error', {"error": "Not logged in"})
        return

    success = delete_room(code, user_id)

    if not success:
        emit('delete_error', {"error": "Only the creator can delete this room"})
        return

    # tell everyone currently in the room to leave, including the creator
    emit('room_deleted', {"code": code}, room=code)


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)