"""
routes.py
Toàn bộ route Flask — gắn thẳng vào app qua register_routes(app)
để giữ nguyên tên endpoint gốc (không có prefix blueprint).
"""

import cv2
import numpy as np
import face_recognition
from flask import (
    Flask, Response, jsonify, redirect,
    render_template, request, session, url_for,
)

from config import DISTANCE_THRESHOLD
from camera import generate_frames, get_current_frame

# Được gán từ app.py sau khi khởi tạo dữ liệu huấn luyện
known_encodings = []
known_names     = []


def init_known_data(encodings, names) -> None:
    """Gắn dữ liệu huấn luyện vào module routes."""
    global known_encodings, known_names
    known_encodings = encodings
    known_names     = names


# Route handlers

def index():
    return render_template("index.html")


def welcome():
    name = request.form.get("name")
    if "user" not in session or session["user"] != name:
        return redirect(url_for("index"))
    return render_template("welcome.html", name=name)


def video_feed():
    return Response(
        generate_frames(known_encodings, known_names),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


def _identify_face(frame):
    """Trả về tên người nếu nhận diện được, None nếu không."""
    rgb_frame      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    if not face_encodings:
        return None

    for encoding in face_encodings:
        matches        = face_recognition.compare_faces(known_encodings, encoding)
        face_distances = face_recognition.face_distance(known_encodings, encoding)
        if face_distances.size == 0:
            continue
        best_idx  = int(np.argmin(face_distances))
        best_dist = face_distances[best_idx]
        if best_dist < DISTANCE_THRESHOLD and matches[best_idx]:
            return known_names[best_idx]

    return None


def login():
    frame = get_current_frame()
    if frame is None:
        return jsonify({"status": "error", "message": "Không có frame từ webcam."})

    try:
        name = _identify_face(frame)
        if name:
            session["user"] = name
            return jsonify({
                "status":      "success",
                "welcome_url": url_for("welcome"),
                "name":        name,
            })
        return jsonify({"status": "failed", "message": "Khuôn mặt không nhận diện được."})

    except Exception as e:
        print(f"[ERROR] Lỗi đăng nhập: {e}")
        return jsonify({"status": "error", "message": str(e)})


# Đăng ký route vào app

def register_routes(app: Flask) -> None:
    app.add_url_rule("/",           "index",      index)
    app.add_url_rule("/welcome",    "welcome",    welcome,    methods=["POST"])
    app.add_url_rule("/video_feed", "video_feed", video_feed)
    app.add_url_rule("/login",      "login",      login,      methods=["POST"])