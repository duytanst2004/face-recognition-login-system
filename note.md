# Note

## Library
* os: Tương tác với hệ điều hành.
* cv2: Thị giác máy tính.
* numpy: Xử lý toán học.
* face_recognition: nhận diện khuôn mặt.
* pickle: Tuần tự hóa (serialize) và giải tuần tự hóa (deserialize) các đối tượng.
* hashlib: Cung cấp thuật toán hashing an toàn.
* flask: Ứng dụng web.
* queue: Hàng đợi.
* threading: Luồng

## Function

### get_training_dir_hash()
* Mục đích: Trả về mã hash SHA-256 (dạng hexdigest).
* hashlib.sha256(): Khởi tạo đối tượng hash 256 sử dụng thuận toán SHA-256.
* os.walk():
  - Duyệt thư mục.
  - Trả về tuple (root, dirs, files)
* hasher.hexdigest(): trả về chuỗi hex chứa digest (bản tóm tắt) của dữ liệu.

### Load_training_data(training_dir)
* Mục đích: Tải (nếu có) hoặc huấn luyện dữ liệu.

### save_trained_data(encodings, names, dir_hash)
* Mục đích:
  - Lưu đối tượng thành chuỗi byte:
    + dictionary: ('encodings', 'names', 'dir_hash')

### load_trained_data()
* Mục đích: Tải dữ liệu đã được lưu.

### initialize_training_data()
* Mục đích: Khởi tạo dữ liệu đã được training, kiểm tra xem dữ liệu đã được lưu chưa và còn mới không.
* Case:
  1. Tải dữ liệu đã được training.
  2. Bắt đầu training.

### capture_frames()
* Mục đích: Lấy khung hình từ webcam đưa vào hàng đợi.
* cv2.VideoCapture(): Tạo đối tượng để truy cập vào webcam.
* cap.read(): Trả về tuple (ret, frame).

### generate_frames()
* Mục đích: 
  - Xử lý từng frame video để phát hiện và nhận diện khuôn mặt.
  - Tạo ra một luồng các frame đã được xử lý:
    + Xác định vị trí khuôn mặt.
    + Hiển thị tên.
* face_recognition.face_locations(): Trả về danh sách (top, right, bottom, left)
* cv2.imencode('.jpg', frame):
  - Mã hóa frame (numpy array) thành JPEG nén.
  - Trả về: Tuple (Thành công, dữ liệu dang byte).
* yield:
  - Tạo ra một phần của luồng dữ liệu mà trình duyệt có thể hiểu để hiển thị video trực tiếp.
  - Gửi frame ảnh mới đến trình duyệt có đinh dạng multipart/x-mixed-replace cho phép trình duyệt liên tục thay thế frame cũ bằng frame mới nhận được, tạo hiệu ứng video.

### @app.route()
* Mục đích: Đây là một decorator trong Flask, liên kết với đường dẫn gốc của ứng dụng web.

### index()
* Mục đích: render và trả về nội dung của file index.html trong thư mục templates.

### video_feed()
* Mục đích: Trả về đối tượng Response chứa luồng video.

### login()
* Mục đích: Xử lý yêu cầu đăng nhập bằng cách nhận diện khuôn mặt từ frame hiện tại.
* Case:
  1. Không tìm thấy khuôn mặt.
  2. Đăng nhập thành công.
  3. Đăng nhập thất bại.

### welcome()
* Mục đích: Hiển thị welcome.
* redirect(): Chuyển hướng.

### main()
* Mục đích: Khởi chạy ứng dụng Flask.

### DISTANCE_THRESHOLD: Ngưỡng khoảng cách để xác định khuôn mặt có khớp hay không.