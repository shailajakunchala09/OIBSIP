from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import secrets

from flask import Flask, jsonify, render_template, request, session

from server.auth import hash_password, validate_room_name, validate_username, validate_password, verify_password
from server.database import Database, UsernameTaken, RoomExists


app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

db = Database()


@app.route("/")
def home():
    return render_template("index.html")


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.get_user_by_id(int(user_id))


@app.post("/api/register")
def register():
    data = request.get_json(silent=True) or {}

    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))

    try:
        validate_username(username)
        validate_password(password)
    except ValueError as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400

    try:
        user = db.create_user(username, hash_password(password))
    except UsernameTaken:
        return jsonify({
            "ok": False,
            "message": "That username is already registered."
        }), 409

    session["user_id"] = user["id"]

    return jsonify({
        "ok": True,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "created_at": user["created_at"],
        }
    })


@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}

    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))

    user = db.get_user_by_name(username)

    if not user or not verify_password(password, user["password_hash"]):
        return jsonify({
            "ok": False,
            "message": "Invalid username or password."
        }), 401

    db.touch_last_seen(user["id"])
    session["user_id"] = user["id"]

    return jsonify({
        "ok": True,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "created_at": user["created_at"],
        }
    })


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.get("/api/rooms")
def rooms():
    user = current_user()

    if not user:
        return jsonify({"ok": False, "message": "Not logged in."}), 401

    joined = db.room_ids_for_user(user["id"])

    result = []

    for room in db.list_rooms():
        room["joined"] = room["id"] in joined
        result.append(room)

    return jsonify({
        "ok": True,
        "rooms": result
    })


@app.post("/api/rooms")
def create_room():
    user = current_user()

    if not user:
        return jsonify({"ok": False, "message": "Not logged in."}), 401

    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()
    description = str(data.get("description", "")).strip()

    try:
        validate_room_name(name)
    except ValueError as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400

    try:
        room = db.create_room(name, description, user["id"])
    except RoomExists:
        return jsonify({
            "ok": False,
            "message": "A room with that name already exists."
        }), 409

    db.add_member(room["id"], user["id"])

    return jsonify({
        "ok": True,
        "room": room
    })


@app.post("/api/rooms/<int:room_id>/join")
def join_room(room_id: int):
    user = current_user()

    if not user:
        return jsonify({"ok": False, "message": "Not logged in."}), 401

    room = db.get_room(room_id)

    if not room:
        return jsonify({"ok": False, "message": "Room not found."}), 404

    db.add_member(room_id, user["id"])

    return jsonify({
        "ok": True,
        "room": room,
        "history": db.recent_messages(room_id),
        "members": db.members(room_id),
    })


@app.post("/api/rooms/<int:room_id>/leave")
def leave_room(room_id: int):
    user = current_user()

    if not user:
        return jsonify({"ok": False, "message": "Not logged in."}), 401

    db.remove_member(room_id, user["id"])

    return jsonify({"ok": True})


@app.get("/api/rooms/<int:room_id>/messages")
def get_messages(room_id: int):
    user = current_user()

    if not user:
        return jsonify({"ok": False, "message": "Not logged in."}), 401

    if not db.is_member(room_id, user["id"]):
        return jsonify({
            "ok": False,
            "message": "Join the room first."
        }), 403

    return jsonify({
        "ok": True,
        "messages": db.recent_messages(room_id),
        "members": db.members(room_id),
    })


@app.post("/api/rooms/<int:room_id>/messages")
def send_message(room_id: int):
    user = current_user()

    if not user:
        return jsonify({"ok": False, "message": "Not logged in."}), 401

    if not db.is_member(room_id, user["id"]):
        return jsonify({
            "ok": False,
            "message": "Join the room first."
        }), 403

    data = request.get_json(silent=True) or {}

    text = str(data.get("text", "")).strip()

    if not text:
        return jsonify({
            "ok": False,
            "message": "Message cannot be empty."
        }), 400

    if len(text) > 2000:
        return jsonify({
            "ok": False,
            "message": "Message is too long."
        }), 400

    message = db.add_message(
        room_id,
        user["id"],
        text,
        "user"
    )

    return jsonify({
        "ok": True,
        "message": message
    })


@app.get("/api/me")
def me():
    user = current_user()

    if not user:
        return jsonify({
            "ok": False,
            "logged_in": False
        })

    return jsonify({
        "ok": True,
        "logged_in": True,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "created_at": user["created_at"],
        }
    })

    if __name__ == "__main__":
    import os

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )