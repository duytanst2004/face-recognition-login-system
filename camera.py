"""
camera.py
Quản lý luồng đọc webcam và sinh frame MJPEG có vẽ khung nhận diện khuôn mặt.
"""

import time
import threading
from queue import Queue

import cv2
import numpy as np
import face_recognition

from config import DISTANCE_THRESHOLD

# Shared state
frame_queue: Queue = Queue(maxsize=1)
_cap              = None
_running          = False
_lock             = threading.Lock()


# Capture thread

def _capture_loop() -> None:
    global _cap, _running

    _cap = cv2.VideoCapture(0)
    if not _cap.isOpened():
        print("[ERROR] Không thể mở webcam.")
        return

    while _running:
        ret, frame = _cap.read()
        if not ret:
            print("[ERROR] Không thể đọc frame từ webcam.")
            break

        frame = cv2.flip(frame, 1)

        # Giữ frame mới nhất trong queue (maxsize=1)
        if frame_queue.full():
            try:
                frame_queue.get_nowait()
            except Exception:
                pass
        frame_queue.put(frame)

    _cap.release()
    print("[INFO] Dừng capture webcam.")


def start_capture() -> threading.Thread:
    """Khởi động thread đọc webcam và trả về thread đó."""
    global _running
    _running = True
    t = threading.Thread(target=_capture_loop, daemon=True)
    t.start()
    return t


def stop_capture() -> None:
    global _running
    _running = False


# MJPEG generator

def _draw_face(frame, top, right, bottom, left, name: str) -> None:
    color = (0, 0, 255) if name == "Unknown" else (0, 255, 0)
    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
    cv2.putText(frame, name, (left, top - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)


def _recognize(rgb_frame, known_encodings, known_names) -> list[tuple[tuple, str]]:
    """Trả về danh sách ((top,right,bottom,left), name) cho mỗi khuôn mặt."""
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
    results = []

    for location, encoding in zip(face_locations, face_encodings):
        name = "Unknown"
        if known_encodings:
            matches        = face_recognition.compare_faces(known_encodings, encoding)
            face_distances = face_recognition.face_distance(known_encodings, encoding)
            if face_distances.size > 0:
                best_idx  = int(np.argmin(face_distances))
                best_dist = face_distances[best_idx]
                if best_dist < DISTANCE_THRESHOLD and matches[best_idx]:
                    name = known_names[best_idx]
        results.append((location, name))

    return results


def generate_frames(known_encodings, known_names):
    """Generator sinh frame MJPEG kèm bounding-box nhận diện khuôn mặt."""
    while _running:
        if frame_queue.empty():
            time.sleep(0.01)
            continue

        try:
            frame     = frame_queue.get()
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            for (top, right, bottom, left), name in _recognize(rgb_frame, known_encodings, known_names):
                _draw_face(frame, top, right, bottom, left, name)

            ret, buffer = cv2.imencode(".jpg", frame)
            if not ret:
                print("[ERROR] Lỗi encode frame thành JPEG.")
                continue

            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n"
                   + buffer.tobytes()
                   + b"\r\n")

        except Exception as e:
            print(f"[ERROR] Lỗi xử lý frame: {e}")


def get_current_frame():
    """Lấy frame hiện tại từ queue (dùng cho route /login)."""
    if frame_queue.empty():
        return None
    return frame_queue.get()
