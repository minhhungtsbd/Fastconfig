# FastConfigVPS v3.1 - Python PyQt6

## Giới thiệu

FastConfigVPS là công cụ cấu hình VPS Windows tự động, được chuyển đổi từ AutoIt sang Python PyQt6 với giao diện hiện đại, gọn gàng và dễ sử dụng.

## Tính năng chính

### 1. Cài đặt phần mềm tự động
- **Trình duyệt web**: Chrome, Firefox, Edge, Opera, Brave, Centbrowser
- **Công cụ hỗ trợ**: Bitvise SSH, Proxifier, WinRAR, 7-Zip, Notepad++, VLC
- Hỗ trợ cài đặt im lặng (silent installation)
- Tùy chọn chỉ tải về không cài đặt
- Tự động chọn URL phù hợp với phiên bản Windows

### 2. Cấu hình hệ thống
- Tắt UAC (User Account Control)
- Tắt IE Enhanced Security
- Tắt Windows Update
- Tắt Windows Firewall
- Cấu hình System Tray và Taskbar
- Thay đổi mật khẩu Windows với kiểm tra độ mạnh

### 3. Cấu hình mạng
- Cấu hình IP tĩnh và Gateway
- Thiết lập DNS servers (Google, Cloudflare, OpenDNS, Quad9)
- DNS tùy chỉnh
- Tự động phát hiện cấu hình mạng hiện tại

### 4. Tùy chọn nâng cao
- Kích hoạt Windows (180 ngày)
- Mở rộng ổ đĩa hệ thống
- Chuyển đổi Windows Edition (Evaluation → Standard)
  - Windows Server 2012/2016/2019/2022

### 5. Lịch sử đăng nhập RDP
- Xem các địa chỉ IP đã đăng nhập RDP
- Lọc theo LogonType 10 (RDP)
- Xuất lịch sử ra file text
- Hiển thị 7 ngày gần nhất

### 6. Giao diện
- Thiết kế hiện đại với PyQt6
- Hỗ trợ chế độ sáng/tối
- Progress bar và status tracking
- Logging chi tiết

## Yêu cầu hệ thống

- Windows 10/11 hoặc Windows Server 2012 R2 trở lên
- Python 3.8 trở lên
- Quyền Administrator (cho một số chức năng)

## Cài đặt

### 1. Cài đặt Python dependencies:

```bash
pip install PyQt5
```

### 2. Chạy ứng dụng:

```bash
python fast_config_vps.py
```

## Hướng dẫn sử dụng

### Bước 1: Chọn chức năng cần cấu hình
- Mở tab tương ứng (Cài đặt phần mềm, Cấu hình hệ thống, Mạng & Nâng cao)
- Chọn các checkbox cho chức năng muốn thực hiện

### Bước 2: Cấu hình tùy chỉnh (nếu cần)
- **Mật khẩu Windows**: Nhập mật khẩu mới nếu muốn thay đổi
- **Cấu hình mạng**: Nhập IP|Subnet|Gateway hoặc để hệ thống tự động phát hiện
- **DNS**: Chọn DNS có sẵn hoặc nhập DNS tùy chỉnh

### Bước 3: Bắt đầu cấu hình
- Nhấn nút "🚀 Bắt đầu cấu hình"
- Theo dõi tiến trình qua progress bar và log

### Bước 4: Xem lịch sử RDP (tùy chọn)
- Chuyển sang tab "Logs & RDP History"
- Nhấn "Lấy lịch sử RDP"
- Xuất ra file nếu cần

## So sánh với phiên bản AutoIt

| Tính năng | AutoIt | Python PyQt6 |
|-----------|--------|--------------|
| Giao diện | GUI cơ bản | Giao diện hiện đại với tabs |
| Theme | Chỉ sáng | Sáng + Tối |
| Logging | File log | File log + UI real-time |
| Progress tracking | Có | Có với chi tiết hơn |
| Multi-threading | Có | Có (QThread) |
| Cross-platform | Chỉ Windows | Windows (có thể mở rộng) |
| Bảo trì | Khó | Dễ dàng hơn |

## Cấu trúc code

```
fast_config_vps.py
├── DownloadThread        # Thread download file
├── InstallThread         # Thread cài đặt phần mềm
└── FastConfigVPS         # Main window class
    ├── init_ui()                    # Khởi tạo giao diện
    ├── create_software_tab()        # Tab cài đặt phần mềm
    ├── create_system_tab()          # Tab cấu hình hệ thống
    ├── create_network_tab()         # Tab cấu hình mạng
    ├── create_logs_tab()            # Tab logs & RDP
    ├── process_system_configuration()   # Xử lý cấu hình hệ thống
    ├── process_network_configuration()  # Xử lý cấu hình mạng
    ├── process_advanced_options()       # Xử lý tùy chọn nâng cao
    ├── process_software_installation()  # Xử lý cài đặt phần mềm
    └── get_rdp_history()                # Lấy lịch sử RDP
```

## Lưu ý quan trọng

1. **Quyền Administrator**: Một số chức năng yêu cầu quyền Administrator:
   - Cấu hình registry (UAC, IE ESC, Windows Update)
   - Cấu hình mạng
   - Kích hoạt Windows
   - Lấy lịch sử RDP

2. **Mật khẩu**: 
   - Kiểm tra độ mạnh mật khẩu real-time
   - Khuyến nghị mật khẩu ít nhất 8 ký tự với chữ hoa, chữ thường, số và ký tự đặc biệt

3. **Cấu hình mạng**:
   - Định dạng: `IP|Subnet|Gateway` (ví dụ: `192.168.1.100|255.255.255.0|192.168.1.1`)
   - Hệ thống tự động phát hiện cấu hình hiện tại
   - Kiểm tra kỹ trước khi áp dụng để tránh mất kết nối

4. **Khởi động lại**: Một số thay đổi yêu cầu khởi động lại hệ thống để có hiệu lực

## Logs

- Logs được lưu tại: `logs/fastconfig_YYYY-MM-DD.log`
- Mỗi ngày tạo một file log mới
- Log bao gồm timestamp và chi tiết từng bước thực hiện

## Troubleshooting

### Không thể tải phần mềm
- Kiểm tra kết nối internet
- Thử lại với URL fallback
- Kiểm tra firewall/antivirus

### Không thể cấu hình registry
- Chạy ứng dụng với quyền Administrator
- Kiểm tra Group Policy có chặn không

### Không thể lấy lịch sử RDP
- Chạy ứng dụng với quyền Administrator
- Kiểm tra Audit Policy: `AuditPol.exe /get /subcategory:"Logon"`
- Bật audit nếu cần: `AuditPol.exe /set /subcategory:'Logon' /success:enable`

## Tác giả

Chuyển đổi từ FastConfigVPS v2.6 (AutoIt) sang Python PyQt6
Version: 3.1

## License

Free to use for personal and commercial purposes.
