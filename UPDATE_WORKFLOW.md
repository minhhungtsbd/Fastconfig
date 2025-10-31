# Quy trình cập nhật phần mềm qua GitHub Releases

## Cách hoạt động
- App kiểm tra phiên bản mới từ GitHub Releases API
- So sánh VERSION hiện tại với tag mới nhất (ví dụ: v3.1 → v3.2)
- Tải file EXE mới từ release assets
- Tự động thay thế EXE và khởi động lại

## Hướng dẫn phát hành phiên bản mới

### 1. Chuẩn bị
- Cập nhật VERSION trong `FastConfigVPS.py`:
  ```python
  VERSION = "3.2"  # Tăng version
  ```
- Commit thay đổi: `git commit -am "Release v3.2"`

### 2. Build EXE
```powershell
.\build.bat
```
EXE sẽ nằm trong `dist\FastConfigVPS_v3.2.exe`

### 3. Tạo GitHub Release
```bash
# Tạo tag
git tag v3.2
git push origin v3.2

# Hoặc dùng GitHub CLI
gh release create v3.2 dist\FastConfigVPS_v3.2.exe --title "FastConfigVPS v3.2" --notes "Release notes..."
```

Hoặc tạo manual trên GitHub:
1. Vào `https://github.com/your-username/fastconfig-repo/releases/new`
2. Tag: `v3.2`
3. Title: `FastConfigVPS v3.2`
4. Upload file `FastConfigVPS_v3.2.exe` vào Assets
5. Publish release

### 4. Cấu hình repo trong code
Mở `FastConfigVPS.py` và thay đổi dòng 1851:
```python
GITHUB_REPO = "your-username/fastconfig-repo"  # Thay bằng repo thật
```

### 5. Kiểm tra cập nhật
- Người dùng nhấn nút ⟳ trong app
- App sẽ kiểm tra, tải và tự động cập nhật

## Lưu ý
- Tag phải theo format `v3.1`, `v3.2`... (có chữ "v")
- File EXE trong release assets phải có đuôi `.exe`
- App sẽ tự tìm file EXE đầu tiên trong assets
- Updater script tự xóa sau khi hoàn tất

## Thử nghiệm local
Để test updater mà không cần push lên GitHub:
1. Tạo mock server trả về JSON giống GitHub API
2. Sửa GITHUB_API trong code tạm thời
3. Test flow download + replace
