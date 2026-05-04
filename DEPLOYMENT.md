# Hướng dẫn đóng gói và triển khai (Deployment Guide)

Tài liệu này hướng dẫn cách đóng gói ứng dụng VidCat thành một file cài đặt `.exe` độc lập để phân phối cho người dùng Windows.

## Yêu cầu hệ thống

Trước khi tiến hành đóng gói, đảm bảo bạn đã cài đặt các công cụ sau:
1. **Python** (và môi trường ảo đã cài đủ các thư viện phụ thuộc).
2. **PyInstaller**: Công cụ để biên dịch mã nguồn Python thành file thực thi `.exe`.
3. **NSIS (Nullsoft Scriptable Install System)**: Công cụ để tạo trình cài đặt (Installer). Đảm bảo phần mềm được cài đặt tại `C:\Program Files (x86)\NSIS\makensis.exe` (hoặc cài đặt ở đường dẫn khác và tự động thay đổi lệnh tương ứng).

## Quy trình đóng gói

Quá trình đóng gói bao gồm 2 bước chính: Biên dịch mã nguồn thành ứng dụng độc lập, sau đó tạo file cài đặt.

### Bước 1: Biên dịch mã nguồn bằng PyInstaller

Sử dụng tệp cấu hình đã định nghĩa sẵn là `vidcat.spec` để build bản thực thi.

Chạy lệnh sau từ thư mục gốc của dự án (sử dụng PowerShell):
```powershell
.venv\Scripts\pyinstaller.exe -y vidcat.spec
```
*(Lưu ý: Nếu bạn chạy môi trường khác, hãy gọi `pyinstaller` tương ứng trong môi trường ảo của bạn)*

- Tham số `-y`: Tự động ghi đè và làm sạch thư mục `dist` cũng như `build` cũ.
- **Kết quả:** Thư mục `dist/VidCat` sẽ được tạo ra, chứa file thực thi `VidCat.exe` cùng toàn bộ tài nguyên, thư viện liên quan.

### Bước 2: Tạo trình cài đặt (Installer) bằng NSIS

Sử dụng kịch bản đã cấu hình trong `installer/setup.nsi`. Kịch bản này sẽ lấy toàn bộ nội dung trong thư mục `dist/VidCat` (từ Bước 1) và nén lại thành một file `.exe` cài đặt duy nhất.

Chạy lệnh sau từ thư mục gốc của dự án:
```powershell
& "C:\Program Files (x86)\NSIS\makensis.exe" installer\setup.nsi
```
*(Thay đổi đường dẫn tới `makensis.exe` nếu bạn cài NSIS ở ổ đĩa/thư mục khác)*

- **Kết quả:** File cài đặt hoàn chỉnh sẽ được tạo ra tại thư mục `installer`, ví dụ: `installer/VidCat_Installer_v1.0.exe`.

## Phân phối ứng dụng

Sau khi lệnh NSIS hoàn tất, bạn chỉ cần chia sẻ file `VidCat_Installer_v1.0.exe` cho người dùng. 
Khi người dùng chạy file này, phần mềm sẽ tự động được cài đặt vào hệ thống, tạo shortcut ra Desktop và Start Menu mà không yêu cầu người dùng phải cài thêm Python hay cấu hình bất kỳ thứ gì khác.
