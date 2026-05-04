# Vidcat

Vidcat là một ứng dụng xử lý video mạnh mẽ với giao diện đồ họa (GUI) thân thiện, được xây dựng trên nền tảng Python, PyQt6 và FFmpeg. Ứng dụng cung cấp giải pháp toàn diện cho các tác vụ xử lý video thường ngày, đặc biệt là xử lý hàng loạt.

## Tính năng nổi bật

- **Xóa Logo / Watermark:**
  - Hỗ trợ phương pháp **Zoom-in**: Cắt bỏ logo ở viền video bằng cách phóng to khung hình.
  - Hỗ trợ phương pháp **Delogo**: Làm mờ logo dựa trên bộ lọc nội suy của FFmpeg.
- **Xử lý hàng loạt (Batch Processing):**
  - Kéo thả nhiều video cùng lúc hoặc chọn cả thư mục.
  - Có màu sắc / đánh dấu phân biệt các nhóm video.
  - Xử lý tuần tự không làm quá tải hệ thống.
- **Giao diện trực quan:**
  - Timer đếm thời gian xử lý thực tế.
  - Liên kết trực tiếp để mở thư mục chứa video đầu ra sau khi hoàn thành.
- **Tính năng tiện ích khác:**
  - Ghi nhớ cấu hình: Lưu lại đường dẫn xuất video và các tùy chọn lần cuối bạn sử dụng.
  - Hỗ trợ chạy ẩn xuống System Tray (khay hệ thống) để không làm phiền quá trình làm việc.

## Yêu cầu hệ thống
- Hệ điều hành: Windows, macOS hoặc Linux.
- Có cài đặt sẵn [FFmpeg](https://ffmpeg.org/download.html) và thêm vào biến môi trường (PATH) (nếu bạn chạy từ mã nguồn).

## Cài đặt từ mã nguồn

Dự án này sử dụng [uv](https://github.com/astral-sh/uv) để quản lý môi trường và thư viện:

```bash
# Clone repository
git clone <url_repo>
cd vidcat

# Đồng bộ các thư viện môi trường
uv sync

# Khởi chạy ứng dụng
uv run main.py
```

## Đóng gói ứng dụng (Tạo file .exe)

Bạn có thể tự đóng gói ứng dụng thành file thực thi độc lập (standalone executable) bằng PyInstaller. Toàn bộ cấu hình đã được thiết lập sẵn trong file `vidcat.spec`.

```bash
# Đảm bảo bạn đã cài đặt các dependency dev
uv sync

# Chạy lệnh đóng gói
uv run pyinstaller -y vidcat.spec
```

File thực thi sẽ nằm trong thư mục `dist/Vidcat.exe`.

## Cấu trúc thư mục

- `main.py`: File khởi chạy chính.
- `core/`: Chứa các logic xử lý video bằng FFmpeg, quản lý tiến trình.
- `ui/`: Các thành phần giao diện được xây dựng bằng PyQt6.
- `installer/`: Chứa kịch bản NSIS để build bộ cài.
- `assets/`: Biểu tượng, hình ảnh và tài nguyên khác.

## Tác giả / Phiên bản
- Phiên bản: 0.1.0
- Phát triển bằng: Python 3.13, PyQt6, FFmpeg-python
