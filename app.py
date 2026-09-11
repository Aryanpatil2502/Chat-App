import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room
from werkzeug.security import generate_password_hash, check_password_hash
from database import init_db, add_user, get_user, delete_user
import random
import string

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

socketio = SocketIO(app)

init_db()

rooms = {}

@app.route('/')
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template('lobby.html')

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
        return redirect(url_for("register"))

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

    if not check_password_hash(
        user["password_hash"],
        password
    ):
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

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)