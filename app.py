"""
app.py
Điểm khởi động ứng dụng.
"""

from flask import Flask

from config import SECRET_KEY, HOST, PORT
from face_trainer import initialize_training_data
from camera import start_capture, stop_capture
import routes


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    routes.register_routes(app)
    return app


def main() -> None:
    print("[INFO] Khởi tạo dữ liệu huấn luyện...")
    known_encodings, known_names = initialize_training_data()
    routes.init_known_data(known_encodings, known_names)

    start_capture()

    app = create_app()
    try:
        app.run(debug=True, host=HOST, port=PORT, use_reloader=False)
    finally:
        stop_capture()
        print("[INFO] Ứng dụng Flask đã dừng.")


if __name__ == "__main__":
    main()