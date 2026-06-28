"""
face_trainer.py
Quản lý việc huấn luyện và cache dữ liệu nhận diện khuôn mặt.
"""

import os
import hashlib
import pickle

import face_recognition

from config import TRAINING_DIR, TRAINED_DATA_FILE


# ── Tính hash thư mục training ────────────────────────────────────────────────

def get_training_dir_hash(training_dir: str = TRAINING_DIR) -> str:
    """SHA-256 của toàn bộ nội dung file trong thư mục training."""
    hasher = hashlib.sha256()
    for root, _, files in sorted(os.walk(training_dir)):
        for file in sorted(files):
            file_path = os.path.join(root, file)
            try:
                with open(file_path, "rb") as f:
                    hasher.update(f.read())
            except Exception as e:
                print(f"[ERROR] Không thể đọc file: {file_path} - {e}")
    return hasher.hexdigest()


# ── Huấn luyện từ ảnh ─────────────────────────────────────────────────────────

def load_training_data(training_dir: str = TRAINING_DIR):
    """
    Duyệt qua từng thư mục con (= tên người) trong training_dir,
    trích xuất face encoding và trả về (encodings, names).
    """
    encodings, names = [], []

    for person_name in os.listdir(training_dir):
        person_path = os.path.join(training_dir, person_name)
        if not os.path.isdir(person_path):
            continue

        for image_name in os.listdir(person_path):
            image_path = os.path.join(person_path, image_name)
            try:
                image     = face_recognition.load_image_file(image_path)
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


# ── Lưu / tải cache ───────────────────────────────────────────────────────────

def save_trained_data(encodings, names, dir_hash: str) -> None:
    try:
        with open(TRAINED_DATA_FILE, "wb") as f:
            pickle.dump({"encodings": encodings, "names": names, "dir_hash": dir_hash}, f)
        print("[INFO] Đã lưu dữ liệu huấn luyện.")
    except Exception as e:
        print(f"[ERROR] Lỗi khi lưu dữ liệu huấn luyện: {e}")


def load_trained_data():
    if not os.path.exists(TRAINED_DATA_FILE):
        return None
    try:
        with open(TRAINED_DATA_FILE, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        print(f"[ERROR] Lỗi khi tải dữ liệu huấn luyện: {e}")
        return None


# ── Khởi tạo tổng hợp ─────────────────────────────────────────────────────────

def initialize_training_data() -> tuple[list, list]:
    """
    Trả về (known_encodings, known_names).
    Dùng cache nếu thư mục training chưa thay đổi,
    huấn luyện lại và lưu cache nếu có thay đổi.
    """
    current_hash = get_training_dir_hash()
    trained_data = load_trained_data()

    if trained_data and trained_data.get("dir_hash") == current_hash:
        print("[INFO] Tải dữ liệu huấn luyện từ cache...")
        return trained_data["encodings"], trained_data["names"]

    print("[INFO] Bắt đầu huấn luyện dữ liệu mới...")
    encodings, names = load_training_data()
    save_trained_data(encodings, names, current_hash)
    print("[INFO] Hoàn tất huấn luyện dữ liệu.")
    return encodings, names
