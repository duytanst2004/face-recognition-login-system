# Face Recognition Login System
Face Recognition Login System là một ứng dụng web được phát triển bằng Flask cho phép người dùng đăng nhập bằng nhận diện khuôn mặt. Hệ thống sử dụng thư viện face_recognition để trích xuất đặc trưng khuôn mặt và so khớp với dữ liệu đã được huấn luyện.

## Tính năng
* Đăng nhập bằng nhận diện khuôn mặt.
* Nhận diện khuôn mặt trực tiếp từ webcam.
* Tự động phát hiện thay đổi trong dữ liệu huấn luyện.
* Lưu và tải dữ liệu huấn luyện nhằm giảm thời gian khởi động.
* Hiển thị kết quả nhận diện theo thời gian thực.
* Giao diện web xây dựng bằng Flask.

## Dữ liệu huấn luyện

Mỗi người cần có một thư mục riêng bên trong thư mục training.

Tên thư mục sẽ được sử dụng làm tên người dùng khi nhận diện.

## Cài đặt

Cài đặt các thư viện:

pip install -r requirements.txt
▶️ Chạy chương trình
python app.py

🚀 Quy trình hoạt động
* Đọc dữ liệu ảnh trong thư mục training.
* Trích xuất đặc trưng khuôn mặt.
* Lưu dữ liệu huấn luyện.
* Mở webcam.
* Phát hiện khuôn mặt trong từng khung hình.
* So khớp với dữ liệu đã huấn luyện.
* Nếu nhận diện thành công, người dùng được đăng nhập.

## Demo
### Trang đăng nhập
![login.png](image/login.png)
### Trang Chủ
![home.png](image/home.png)