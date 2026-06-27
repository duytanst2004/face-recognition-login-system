import os
import cv2
import numpy as np
import face_recognition
import pickle
import hashlib
from flask import Flask, render_template, Response, jsonify, request, redirect, url_for, session
from queue import Queue
import threading

app = Flask(__name__)
app.secret_key = 'your-secret-key'

DISTANCE_THRESHOLD = 0.4
TRAINING_DIR = "training"
TRAINED_DATA_FILE = "trained_data.pkl"

known_encodings = []
known_names = []
frame_queue = Queue(maxsize=1)
cap = None
running = True


def get_training_dir_hash():
    hasher = hashlib.sha256()
    for root, _, files in sorted(os.walk(TRAINING_DIR)):
        for file in sorted(files):
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'rb') as f:
                    hasher.update(f.read())
            except Exception as e:
                print(f"[ERROR] Không thể đọc file: {file_path} - {e}")
    return hasher.hexdigest()


def load_training_data(training_dir):
    encodings = []
    names = []
    for person_name in os.listdir(training_dir):
        person_path = os.path.join(training_dir, person_name)
        if not os.path.isdir(person_path):
            continue
        for image_name in os.listdir(person_path):
            image_path = os.path.join(person_path, image_name)
            try:
                image = face_recognition.load_image_file(image_path)
                face_encs = face_recognition.face_encodings(image)
                if face_encs:
                    encodings.append(face_encs[0])
                    names.append(person_name)
                    print(f"[INFO] Đã huấn luyện: {image_name} -> {person_name}")
                else:
                    print(f"[WARN] Không tìm thấy khuôn mặt trong: {image_name}")
            except Exception as e:
                print(f"[ERROR] Không thể xử lý ảnh: {image_path} - {e}")
    return encodings, names


def save_trained_data(encodings, names, dir_hash):
    try:
        with open(TRAINED_DATA_FILE, 'wb') as f:
            pickle.dump({'encodings': encodings, 'names': names, 'dir_hash': dir_hash}, f)
        print("[INFO] Đã lưu dữ liệu huấn luyện.")
    except Exception as e:
        print(f"[ERROR] Lỗi khi lưu dữ liệu huấn luyện: {e}")


def load_trained_data():
    if not os.path.exists(TRAINED_DATA_FILE):
        return None
    try:
        with open(TRAINED_DATA_FILE, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        print(f"[ERROR] Lỗi khi tải dữ liệu huấn luyện: {e}")
        return None


def initialize_training_data():
    global known_encodings, known_names
    current_dir_hash = get_training_dir_hash()
    trained_data = load_trained_data()

    if trained_data and trained_data.get('dir_hash') == current_dir_hash:
        print("[INFO] Tải dữ liệu huấn luyện từ file...")
        known_encodings = trained_data['encodings']
        known_names = trained_data['names']
    else:
        print("[INFO] Bắt đầu huấn luyện dữ liệu mới...")
        known_encodings, known_names = load_training_data(TRAINING_DIR)
        save_trained_data(known_encodings, known_names, current_dir_hash)
        print("[INFO] Hoàn tất huấn luyện dữ liệu.")


def capture_frames():
    global cap, running
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Không thể mở webcam.")
        return

    while running:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Không thể đọc frame từ webcam.")
            break
        frame = cv2.flip(frame, 1)
        try:
            if not frame_queue.full():
                frame_queue.put(frame)
            else:
                frame_queue.get()
                frame_queue.put(frame)
        except Exception as e:
            print(f"[ERROR] Lỗi với hàng đợi frame: {e}")

    cap.release()
    print("[INFO] Dừng capture webcam.")


def generate_frames():
    while running:
        try:
            if not frame_queue.empty():
                frame = frame_queue.get()
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(rgb_frame)
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

                for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                    matches = face_recognition.compare_faces(known_encodings, face_encoding)
                    name = "Unknown"
                    face_distances = face_recognition.face_distance(known_encodings, face_encoding)
                    if face_distances.size > 0:
                        best_match_index = np.argmin(face_distances)
                        face_distance_value = face_distances[best_match_index]
                        if face_distance_value < DISTANCE_THRESHOLD and matches[best_match_index]:
                            name = known_names[best_match_index]

                    color = (0, 0, 255) if name == "Unknown" else (0, 255, 0)
                    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                    cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)

                ret, buffer = cv2.imencode('.jpg', frame)
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                else:
                    print("[ERROR] Lỗi encode frame thành JPEG.")
            else:
                import time
                time.sleep(0.01)  # Tránh việc loop quá nhanh khi queue rỗng
        except Exception as e:
            print(f"[ERROR] Lỗi trong quá trình xử lý frame: {e}")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/login', methods=['POST'])
def login():
    if frame_queue.empty():
        return jsonify({"status": "error", "message": "Không có frame từ webcam."})

    try:
        frame = frame_queue.get()
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        if not face_encodings:
            return jsonify({"status": "failed", "message": "Không tìm thấy khuôn mặt."})

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_encodings, face_encoding)
            face_distances = face_recognition.face_distance(known_encodings, face_encoding)
            if face_distances.size > 0:
                best_match_index = np.argmin(face_distances)
                face_distance_value = face_distances[best_match_index]

                if face_distance_value < DISTANCE_THRESHOLD and matches[best_match_index]:
                    name = known_names[best_match_index]
                    session['user'] = name
                    return jsonify({"status": "success", "welcome_url": url_for('welcome'), "name": name})

        return jsonify({"status": "failed", "message": "Đăng nhập thất bại: Khuôn mặt không nhận diện được."})

    except Exception as e:
        print(f"[ERROR] Lỗi trong quá trình đăng nhập: {e}")
        return jsonify({"status": "error", "message": f"Lỗi: {e}"})


@app.route('/welcome', methods=['POST'])
def welcome():
    name = request.form.get('name')
    if 'user' not in session or session['user'] != name:
        return redirect(url_for('index'))
    return render_template('welcome.html', name=name)

def main():
    print("[INFO] Khởi tạo dữ liệu huấn luyện...")
    initialize_training_data()

    capture_thread = threading.Thread(target=capture_frames)
    capture_thread.daemon = True
    capture_thread.start()

    try:
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
    finally:
        running = False
        if cap is not None and cap.isOpened():
            cap.release()
        print("[INFO] Ứng dụng Flask đã dừng.")

if __name__ == '__main__':
    main()