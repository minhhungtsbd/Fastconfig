"""
FastConfigVPS - Windows VPS Configuration Tool
Chuyển đổi từ AutoIt sang Python PyQt5
Version: 3.1
"""

import sys
import os
import json
import time
import threading
import subprocess
import winreg
import urllib.request
import tempfile
import re
import warnings
import ssl
import platform
from datetime import datetime, timedelta

# Suppress deprecation warnings from PyQt5
warnings.filterwarnings("ignore", category=DeprecationWarning)

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QLineEdit, QPushButton, QGroupBox,
    QCheckBox, QTabWidget, QTextEdit, QProgressBar, QMessageBox,
    QComboBox, QFileDialog, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread, QMetaObject, Q_ARG, pyqtSlot
from PyQt5.QtGui import QIcon, QColor, QFont, QTextCursor


class DownloadThread(QThread):
    """Thread để download file"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)
    log_signal = pyqtSignal(str)
    
    def __init__(self, url, filepath, software_name):
        super().__init__()
        self.url = url
        self.filepath = filepath
        self.software_name = software_name
    
    def run(self):
        try:
            self.log_signal.emit(f"Đang tải {self.software_name} từ {self.url}...")
            
            def report_progress(block_num, block_size, total_size):
                downloaded = block_num * block_size
                if total_size > 0:
                    percent = int((downloaded / total_size) * 100)
                    self.progress.emit(percent)
            
            # Create SSL context that bypasses certificate verification for problematic URLs
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Use SSL context for HTTPS requests
            if self.url.startswith('https://'):
                urllib.request.install_opener(urllib.request.build_opener(
                    urllib.request.HTTPSHandler(context=ssl_context)
                ))
            
            urllib.request.urlretrieve(self.url, self.filepath, report_progress)
            
            if os.path.exists(self.filepath):
                size = os.path.getsize(self.filepath)
                self.log_signal.emit(f"✓ Tải {self.software_name} thành công ({size} bytes)")
                
                # Kiểm tra và đổi tên file nếu là MSI nhưng có tên .exe (đặc biệt với Chrome)
                if self.software_name == "Chrome":
                    actual_filepath = self._check_and_rename_msi(self.filepath)
                    self.finished.emit(True, actual_filepath)
                else:
                    self.finished.emit(True, self.filepath)
            else:
                self.log_signal.emit(f"✗ Không thể tải {self.software_name}")
                self.finished.emit(False, "")
        
        except Exception as e:
            self.log_signal.emit(f"✗ Lỗi khi tải {self.software_name}: {str(e)}")
            self.finished.emit(False, "")
    
    def _check_and_rename_msi(self, filepath):
        """Kiểm tra file header và đổi tên nếu là MSI"""
        try:
            with open(filepath, 'rb') as f:
                header = f.read(8)
            
            # MSI file signature: D0 CF 11 E0 A1 B1 1A E1
            if header[:8] == b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1':
                self.log_signal.emit("🔍 Phát hiện file MSI (header: D0CF11E0)")
                
                # Đổi tên từ .exe sang .msi
                if filepath.endswith('.exe'):
                    new_filepath = filepath[:-4] + '.msi'
                    
                    # Retry logic để xử lý file lock
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            if os.path.exists(new_filepath):
                                os.remove(new_filepath)
                            os.rename(filepath, new_filepath)
                            self.log_signal.emit(f"✓ Đã đổi tên file thành {os.path.basename(new_filepath)}")
                            return new_filepath
                        except Exception as e:
                            if attempt < max_retries - 1:
                                time.sleep(0.5)  # Đợi một chút trước khi thử lại
                            else:
                                self.log_signal.emit(f"⚠️ Không thể đổi tên file: {str(e)}")
                                return filepath
            
            return filepath
        
        except Exception as e:
            self.log_signal.emit(f"⚠️ Lỗi khi kiểm tra file header: {str(e)}")
            return filepath


class InstallThread(QThread):
    """Thread để cài đặt phần mềm"""
    finished = pyqtSignal(bool, str)
    log_signal = pyqtSignal(str)
    
    def __init__(self, filepath, software_name, silent=True):
        super().__init__()
        self.filepath = filepath
        self.software_name = software_name
        self.silent = silent
    
    def run(self):
        try:
            self.log_signal.emit(f"Đang cài đặt {self.software_name}...")
            
            # Lấy phiên bản Windows
            win_version = platform.version()
            self.log_signal.emit(f"💻 Windows version: {win_version}")
            
            # Kiểm tra loại file
            is_msi = self.filepath.lower().endswith('.msi')
            
            # Logic đặc biệt cho Chrome
            if self.software_name == "Chrome":
                success = self._install_chrome(is_msi)
                if success:
                    self.log_signal.emit(f"✓ Cài đặt {self.software_name} thành công")
                    self.finished.emit(True, self.software_name)
                else:
                    self.log_signal.emit(f"✗ Cài đặt {self.software_name} thất bại với tất cả methods")
                    self.finished.emit(False, self.software_name)
                return
            
            # Logic cho các phần mềm khác
            if self.software_name == "Firefox":
                params = "-ms" if self.silent else ""
            elif self.software_name == "Edge":
                params = "/silent /install" if self.silent else ""
            else:
                params = "/S" if self.silent else ""
            
            # Chạy installer
            cmd = f'"{self.filepath}" {params}'
            self.log_signal.emit(f"🔧 Chạy: {cmd}")
            result = subprocess.run(cmd, shell=True, capture_output=True, timeout=300)
            
            if result.returncode == 0:
                self.log_signal.emit(f"✓ Cài đặt {self.software_name} thành công")
                self.finished.emit(True, self.software_name)
            else:
                self.log_signal.emit(f"✗ Cài đặt {self.software_name} thất bại (code: {result.returncode})")
                self.finished.emit(False, self.software_name)
        
        except subprocess.TimeoutExpired:
            self.log_signal.emit(f"✗ Cài đặt {self.software_name} timeout")
            self.finished.emit(False, self.software_name)
        except Exception as e:
            self.log_signal.emit(f"✗ Lỗi khi cài đặt {self.software_name}: {str(e)}")
            self.finished.emit(False, self.software_name)
    
    def _install_chrome(self, is_msi):
        """Cài đặt Chrome với các phương pháp đã test thành công"""
        if is_msi:
            # Phương pháp MSI - thử /qn trước, sau đó /passive
            methods = [
                ('msiexec /qn', f'msiexec /i "{self.filepath}" /qn /norestart'),
                ('msiexec /passive', f'msiexec /i "{self.filepath}" /passive /norestart')
            ]
        else:
            # Phương pháp EXE - thử /silent /install trước, sau đó interactive
            methods = [
                ('AutoIt (/silent /install)', f'"{self.filepath}" /silent /install'),
                ('Interactive (no params)', f'"{self.filepath}"')
            ]
        
        for method_name, cmd in methods:
            try:
                self.log_signal.emit(f"🔧 Thử phương pháp: {method_name}")
                self.log_signal.emit(f"   Lệnh: {cmd}")
                
                result = subprocess.run(
                    cmd, 
                    shell=True, 
                    capture_output=True, 
                    text=True, 
                    timeout=300
                )
                
                self.log_signal.emit(f"   Exit code: {result.returncode}")
                
                # Kiểm tra Chrome có thực sự được cài hay không
                chrome_paths = [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
                ]
                
                chrome_found = any(os.path.exists(path) for path in chrome_paths)
                
                # Điều kiện thành công: exit code = 0 VÀ Chrome được cài
                if result.returncode == 0:
                    if chrome_found:
                        self.log_signal.emit(f"✓ {method_name} thành công - Chrome đã được cài đặt")
                        return True
                    else:
                        self.log_signal.emit(f"⚠️ Exit code 0 nhưng Chrome không được cài - thử phương pháp tiếp theo")
                else:
                    self.log_signal.emit(f"✗ Phương pháp {method_name} thất bại (exit code: {result.returncode})")
                    if result.stderr:
                        error_msg = result.stderr.strip()
                        if error_msg:
                            self.log_signal.emit(f"   Error: {error_msg[:200]}")
                    
            except subprocess.TimeoutExpired:
                self.log_signal.emit(f"⚠️ Timeout - Phương pháp {method_name} chạy quá lâu")
                continue
            except Exception as e:
                self.log_signal.emit(f"✗ Lỗi với phương pháp {method_name}: {str(e)}")
                continue
        
        # Nếu tất cả phương pháp đều thất bại
        self.log_signal.emit("✗ Tất cả các phương pháp cài đặt Chrome đều thất bại")
        return False


class FastConfigVPS(QMainWindow):
    """Ứng dụng chính FastConfigVPS"""
    
    VERSION = "3.1"
    
    # Custom signals for thread-safe UI updates
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    stop_processing_signal = pyqtSignal()
    enable_button_signal = pyqtSignal(bool)
    show_update_dialog_signal = pyqtSignal(str, str, float)  # version, size_mb, download_url
    show_message_signal = pyqtSignal(str, str, str)  # title, message, type (info/warning/error)
    
    # URLs cho các phần mềm
    SOFTWARE_URLS = {
        "Chrome": {
            "6.3": "https://files.cloudmini.net/ChromeSetup.exe",  # Prioritize working fallback URL
            "10.0": "https://dl.google.com/dl/chrome/install/googlechromestandaloneenterprise64.msi",
            "fallback": "https://archive.org/download/browser_02.05.2022/Browser/ChromeSetup.exe",  # Move problematic URL to fallback
            "filename": "chrome_installer.exe"
        },
        "Firefox": {
            "6.3": "https://download.mozilla.org/?product=firefox-esr115-latest-ssl&os=win64&lang=en-US",
            "10.0": "https://download.mozilla.org/?product=firefox-latest&os=win64&lang=en-US",
            "fallback": "https://files.cloudmini.net/FirefoxSetup.exe",
            "filename": "firefox_installer.exe"
        },
        "Edge": {
            "6.3": "https://files.cloudmini.net/MicrosoftEdgeSetup.exe",
            "10.0": "https://c2rsetup.officeapps.live.com/c2r/downloadEdge.aspx?ProductreleaseID=Edge&platform=Default&version=Edge&source=EdgeStablePage&Channel=Stable&language=en",
            "fallback": "https://files.cloudmini.net/MicrosoftEdgeSetup.exe",
            "filename": "edge_installer.exe"
        },
        "Brave": {
            "6.3": "https://github.com/brave/brave-browser/releases/download/v1.43.93/BraveBrowserStandaloneSilentSetup.exe",
            "10.0": "https://laptop-updates.brave.com/latest/winx64",
            "fallback": "https://files.cloudmini.net/BraveBrowserSetup.exe",
            "filename": "brave_installer.exe"
        },
        "Opera": {
            "6.3": "https://download.opera.com/download/get/?id=63649&nothanks=yes&sub=marine&utm_tryagain=yes",
            "10.0": "https://download.opera.com/download/get/?id=74098&nothanks=yes&sub=marine&utm_tryagain=yes",
            "fallback": "https://files.cloudmini.net/Opera_10.exe",
            "fallback_6.3": "https://files.cloudmini.net/Opera_6.3.exe",
            "filename": "opera_installer.exe"
        },
        "Centbrowser": {
            "10.0": "https://static.centbrowser.com/win_stable/5.2.1168.83/centbrowser_5.2.1168.83_x64.exe",
            "fallback": "https://files.cloudmini.net/CentbrowserSetup.exe",
            "filename": "centbrowser.exe"
        },
        "Bitvise SSH": {
            "10.0": "https://dl.bitvise.com/BvSshClient-Inst.exe",
            "fallback": "https://files.cloudmini.net/BvSshClient-Inst.exe",
            "filename": "BvSshClient-Inst.exe"
        },
        "Proxifier": {
            "10.0": "https://www.proxifier.com/download/ProxifierSetup.exe",
            "fallback": "https://files.cloudmini.net/ProxifierSetup.exe",
            "filename": "ProxifierSetup.exe"
        },
        "WinRAR": {
            "10.0": "https://www.rarlab.com/rar/winrar-x64-713.exe",
            "fallback": "https://files.cloudmini.net/winrar-x64.exe",
            "filename": "winrar.exe"
        },
        "7-Zip": {
            "10.0": "https://www.7-zip.org/a/7z2501-x64.exe",
            "fallback": "https://files.cloudmini.net/7z-x64.exe",
            "filename": "7zip.exe"
        },
        "Notepad++": {
            "10.0": "https://github.com/notepad-plus-plus/notepad-plus-plus/releases/download/v8.8.6/npp.8.8.6.Installer.x64.exe",
            "fallback": "https://files.cloudmini.net/npp.Installer.x64.exe",
            "filename": "notepadpp.exe"
        },
        "VLC": {
            "10.0": "https://files.cloudmini.net/vlc-win64.exe",
            "fallback": "https://files.cloudmini.net/vlc-win64.exe",
            "filename": "vlc.exe"
        }
    }
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"FastConfigVPS v{self.VERSION}")
        self.setGeometry(100, 100, 750, 600)
        self.setMinimumSize(700, 550)
        
        # Tạo thư mục logs TRUNƠC (cần trước khi gọi bất kỳ log())
        appdata_local = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), '..', 'Local', 'FastConfigVPS')
        self.logs_dir = os.path.normpath(appdata_local)
        if not os.path.exists(self.logs_dir):
            try:
                os.makedirs(self.logs_dir)
            except Exception as e:
                # Fallback đến thư mục cùng nếu AppData không khả dụng
                self.logs_dir = "logs"
                if not os.path.exists(self.logs_dir):
                    os.makedirs(self.logs_dir)
        
        # Set icon
        self.set_app_icon()
        
        # Khởi tạo biến
        self.current_theme = "light"
        self.windows_version = self.detect_windows_version()
        self.total_steps = 0
        self.current_step = 0
        self.running_tasks = []
        self.install_queue = []  # Queue for sequential software installation
        self.current_install_thread = None
        self.has_errors = False  # Track nếu có lỗi trong quá trình cấu hình
        self.downloaded_files = []  # Danh sách file đã tải trong chế độ download-only
        
        # Cấu hình giao diện
        self.init_ui()
        self.apply_theme()
        
        # Connect signals for thread-safe UI updates
        self.log_signal.connect(self._append_log)
        self.status_signal.connect(self._update_status_ui)
        self.progress_signal.connect(self._update_progress_ui)
        self.stop_processing_signal.connect(self._stop_processing_ui)
        self.enable_button_signal.connect(self.start_button.setEnabled)
        self.show_update_dialog_signal.connect(self._show_update_dialog)
        self.show_message_signal.connect(self._show_message_box)
        
        # Log khởi động
        self.log(f"FastConfigVPS v{self.VERSION} đã khởi động")
        self.log(f"Phát hiện Windows version: {self.windows_version}")
        
        # Detect network configuration
        self.detect_network_config()

        # Log update system availability
        self.log("Hệ thống cập nhật từ GitHub Releases sẵn sàng. Dùng nút ⟳ để kiểm tra.")
    
    def set_app_icon(self):
        """Thiết lập icon cho ứng dụng"""
        try:
            # Nếu chạy từ PyInstaller
            if getattr(sys, 'frozen', False):
                # Chạy từ exe
                base_path = sys._MEIPASS
            else:
                # Chạy từ script Python
                base_path = os.path.dirname(os.path.abspath(__file__))
            
            icon_path = os.path.join(base_path, "app_icon.png")
            
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
            else:
                # Thử tìm ở thư mục hiện tại
                if os.path.exists("app_icon.png"):
                    self.setWindowIcon(QIcon("app_icon.png"))
        except Exception as e:
            print(f"Không thể tải icon: {str(e)}")
    
    def init_ui(self):
        """Khởi tạo giao diện người dùng"""
        # Widget trung tâm
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout chính
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # Top bar với nút theme
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        
        # Title label - Hiển thị Windows version
        windows_display_name = self.get_windows_display_name()
        title_label = QLabel(windows_display_name)
        title_label.setFont(QFont("Segoe UI", 10, QFont.Medium))
        title_label.setStyleSheet("color: #6b7280;")
        
        # Theme toggle button với icon
        self.theme_button = QPushButton("☀")
        self.theme_button.setToolTip("Chuyển chế độ tối/sáng")
        self.theme_button.setFixedSize(36, 36)
        self.theme_button.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 2px solid #d1d5db;
                border-radius: 18px;
                font-size: 20px;
                padding: 0px;
                color: #1e293b;
            }
            QPushButton:hover {
                background-color: #f9fafb;
                border-color: #9ca3af;
            }
        """)
        self.theme_button.clicked.connect(self.toggle_theme)

        # Update button (GitHub Releases)
        self.update_button = QPushButton("⟳")
        self.update_button.setToolTip("Kiểm tra cập nhật")
        self.update_button.setFixedSize(36, 36)
        self.update_button.setStyleSheet(self.theme_button.styleSheet())
        self.update_button.clicked.connect(self.on_check_update_click)
        
        top_bar.addWidget(title_label)
        top_bar.addStretch()
        top_bar.addWidget(self.update_button)
        top_bar.addWidget(self.theme_button)
        
        main_layout.addLayout(top_bar)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Tab 1: Software Installation
        self.create_software_tab()
        
        # Tab 2: System Configuration
        self.create_system_tab()
        
        # Tab 3: Network & Advanced
        self.create_network_tab()
        
        # Tab 4: Logs & RDP History
        self.create_logs_tab()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # Status label
        self.status_label = QLabel("Sẵn sàng cấu hình hệ thống...")
        self.status_label.setStyleSheet("padding: 5px; border: 1px solid #e5e7eb;")
        
        # Main button
        self.start_button = QPushButton("🚀 Bắt đầu cấu hình")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4f46e5;
                color: white;
                padding: 8px;
                border-radius: 5px;
                font-size: 13px;
                font-weight: 600;
                min-height: 38px;
            }
            QPushButton:hover {
                background-color: #4338ca;
            }
            QPushButton:pressed {
                background-color: #3730a3;
            }
        """)
        self.start_button.clicked.connect(self.start_configuration)
        
        # Spinner icon cho button state
        self.is_processing = False
        
        # Add widgets to main layout
        main_layout.addWidget(self.tab_widget)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(self.start_button)
    
    def create_software_tab(self):
        """Tạo tab Software Installation"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Browsers group
        browsers_group = QGroupBox("Trình duyệt Web")
        browsers_layout = QGridLayout()
        browsers_layout.setSpacing(6)
        
        self.cb_chrome = QCheckBox("Google Chrome (Latest)")
        self.cb_firefox = QCheckBox("Mozilla Firefox (Latest)")
        self.cb_opera = QCheckBox("Opera Browser")
        self.cb_edge = QCheckBox("Microsoft Edge")
        self.cb_brave = QCheckBox("Brave Browser")
        self.cb_centbrowser = QCheckBox("Centbrowser")
        
        browsers_layout.addWidget(self.cb_chrome, 0, 0)
        browsers_layout.addWidget(self.cb_firefox, 0, 1)
        browsers_layout.addWidget(self.cb_opera, 1, 0)
        browsers_layout.addWidget(self.cb_edge, 1, 1)
        browsers_layout.addWidget(self.cb_brave, 2, 0)
        browsers_layout.addWidget(self.cb_centbrowser, 2, 1)
        
        browsers_group.setLayout(browsers_layout)
        
        # Utilities group
        utils_group = QGroupBox("Tiện ích & Công cụ")
        utils_layout = QGridLayout()
        utils_layout.setSpacing(6)
        
        self.cb_bitvise = QCheckBox("Bitvise SSH Client")
        self.cb_notepadpp = QCheckBox("Notepad++")
        self.cb_winrar = QCheckBox("WinRAR")
        self.cb_proxifier = QCheckBox("Proxifier")
        self.cb_7zip = QCheckBox("7-Zip")
        self.cb_vlc = QCheckBox("VLC Media Player")
        
        utils_layout.addWidget(self.cb_bitvise, 0, 0)
        utils_layout.addWidget(self.cb_notepadpp, 0, 1)
        utils_layout.addWidget(self.cb_winrar, 1, 0)
        utils_layout.addWidget(self.cb_proxifier, 1, 1)
        utils_layout.addWidget(self.cb_7zip, 2, 0)
        utils_layout.addWidget(self.cb_vlc, 2, 1)
        
        utils_group.setLayout(utils_layout)
        
        # Installation options
        options_group = QGroupBox("Tùy chọn cài đặt")
        options_layout = QVBoxLayout()
        
        self.cb_silent_install = QCheckBox("Cài đặt im lặng (không hiển thị)")
        self.cb_silent_install.setChecked(True)
        self.cb_download_only = QCheckBox("Chỉ tải về (không cài đặt)")
        
        # Làm cho 2 checkbox hoạt động như radio buttons (chỉ chọn 1)
        self.cb_silent_install.stateChanged.connect(self.on_silent_install_changed)
        self.cb_download_only.stateChanged.connect(self.on_download_only_changed)
        
        options_layout.addWidget(self.cb_silent_install)
        options_layout.addWidget(self.cb_download_only)
        
        options_group.setLayout(options_layout)
        
        # Add to tab
        layout.addWidget(browsers_group)
        layout.addWidget(utils_group)
        layout.addWidget(options_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Cài đặt phần mềm")
    
    def create_system_tab(self):
        """Tạo tab System Configuration"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # System settings group
        system_group = QGroupBox("Cấu hình hệ thống")
        system_layout = QGridLayout()
        system_layout.setSpacing(6)
        
        # Cột trái
        self.cb_uac = QCheckBox("Tắt UAC (User Account Control)")
        self.cb_uac.setChecked(True)
        self.cb_winupdate = QCheckBox("Tắt Windows Update")
        self.cb_winupdate.setChecked(True)
        self.cb_smallicon = QCheckBox("Biểu tượng Taskbar nhỏ")
        
        # Cột phải
        self.cb_ieesc = QCheckBox("Tắt IE Enhanced Security")
        self.cb_ieesc.setChecked(True)
        self.cb_trayicon = QCheckBox("Hiển thị tất cả biểu tượng System Tray")
        self.cb_trayicon.setChecked(True)
        self.cb_firewall = QCheckBox("Tắt Windows Firewall")
        
        # Thêm vào grid layout
        system_layout.addWidget(self.cb_uac, 0, 0)
        system_layout.addWidget(self.cb_ieesc, 0, 1)
        system_layout.addWidget(self.cb_winupdate, 1, 0)
        system_layout.addWidget(self.cb_trayicon, 1, 1)
        system_layout.addWidget(self.cb_smallicon, 2, 0)
        system_layout.addWidget(self.cb_firewall, 2, 1)
        
        system_group.setLayout(system_layout)
        
        # Password group
        password_group = QGroupBox("Mật khẩu Windows")
        password_layout = QGridLayout()
        
        self.cb_change_password = QCheckBox("Thay đổi mật khẩu Windows")
        password_layout.addWidget(self.cb_change_password, 0, 0, 1, 2)
        
        password_layout.addWidget(QLabel("Mật khẩu mới:"), 1, 0)
        
        # Password input với show/hide button
        password_container = QHBoxLayout()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(25)  # Đồng đều với RDP port input
        
        # Show/Hide password button
        self.show_password_button = QPushButton("👁")
        self.show_password_button.setFixedSize(35, 25)  # Tăng kích thước và đồng đều chiều cao
        self.show_password_button.setToolTip("Hiển/Ẩn mật khẩu")
        self.show_password_button.setStyleSheet("""
            QPushButton {
                background-color: #f3f4f6;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e5e7eb;
            }
            QPushButton:pressed {
                background-color: #d1d5db;
            }
        """)
        self.show_password_button.clicked.connect(self.toggle_password_visibility)
        
        password_container.addWidget(self.password_input)
        password_container.addWidget(self.show_password_button)
        password_container.setSpacing(3)  # Giảm spacing để gọn gàng hơn
        password_container.setContentsMargins(0, 0, 0, 0)
        
        password_widget = QWidget()
        password_widget.setLayout(password_container)
        password_layout.addWidget(password_widget, 1, 1)
        
        self.password_strength_label = QLabel("")
        password_layout.addWidget(self.password_strength_label, 2, 1)
        
        self.password_input.textChanged.connect(self.validate_password_strength)
        
        password_group.setLayout(password_layout)
        
        # RDP Configuration group
        rdp_group = QGroupBox("Cấu hình RDP")
        rdp_layout = QGridLayout()
        
        self.cb_change_rdp_port = QCheckBox("Thay đổi Port RDP")
        rdp_layout.addWidget(self.cb_change_rdp_port, 0, 0, 1, 2)
        
        rdp_layout.addWidget(QLabel("Port RDP mới:"), 1, 0)
        self.rdp_port_input = QLineEdit()
        self.rdp_port_input.setText("3389")
        self.rdp_port_input.setPlaceholderText("Nhập port mới (1024-65535)")
        self.rdp_port_input.setMinimumHeight(25)  # Đồng đều với password input
        self.rdp_port_input.setEnabled(False)
        rdp_layout.addWidget(self.rdp_port_input, 1, 1)
        
        # Note label
        rdp_note_label = QLabel("Lưu ý: Port phải nằm trong khoảng 1-65535")
        rdp_note_label.setStyleSheet("font-style: italic; color: #6b7280; font-size: 9pt;")
        rdp_layout.addWidget(rdp_note_label, 2, 1)
        
        # Connect signal để enable/disable port input
        self.cb_change_rdp_port.stateChanged.connect(self.toggle_rdp_port_input)
        
        rdp_group.setLayout(rdp_layout)
        
        # Add to tab
        layout.addWidget(system_group)
        layout.addWidget(password_group)
        layout.addWidget(rdp_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Cấu hình hệ thống")
    
    def create_network_tab(self):
        """Tạo tab Network & Advanced"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Network configuration
        network_group = QGroupBox("Cấu hình mạng")
        network_layout = QGridLayout()
        
        self.cb_static_ip = QCheckBox("Cấu hình IP tĩnh & DNS")
        network_layout.addWidget(self.cb_static_ip, 0, 0, 1, 2)
        
        network_layout.addWidget(QLabel("IP | Subnet | Gateway:"), 1, 0)
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Ví dụ: 192.168.1.100|255.255.255.0|192.168.1.1")
        network_layout.addWidget(self.ip_input, 1, 1)
        
        network_layout.addWidget(QLabel("DNS Servers:"), 2, 0)
        self.dns_combo = QComboBox()
        self.dns_combo.addItems([
            "Google DNS (8.8.8.8)",
            "Cloudflare DNS (1.1.1.1)",
            "OpenDNS (208.67.222.222)",
            "Quad9 DNS (9.9.9.9)"
        ])
        network_layout.addWidget(self.dns_combo, 2, 1)
        
        self.cb_custom_dns = QCheckBox("DNS tùy chỉnh:")
        network_layout.addWidget(self.cb_custom_dns, 3, 0)
        self.custom_dns_input = QLineEdit()
        self.custom_dns_input.setEnabled(False)
        self.custom_dns_input.setPlaceholderText("Ví dụ: 1.1.1.1,1.0.0.1")
        network_layout.addWidget(self.custom_dns_input, 3, 1)
        
        # Connect signal để toggle giữa DNS combo và custom DNS input
        self.cb_custom_dns.stateChanged.connect(self.toggle_dns_input)
        
        network_group.setLayout(network_layout)
        
        # Advanced options
        advanced_group = QGroupBox("Tùy chọn nâng cao")
        advanced_layout = QVBoxLayout()
        
        self.cb_activate = QCheckBox("Kích hoạt Windows (180 ngày)")
        self.cb_extend_hdd = QCheckBox("Mở rộng ổ đĩa hệ thống")
        self.cb_extend_hdd.setChecked(True)
        
        advanced_layout.addWidget(self.cb_activate)
        advanced_layout.addWidget(self.cb_extend_hdd)
        
        advanced_group.setLayout(advanced_layout)
        
        # Windows Edition Conversion
        conversion_group = QGroupBox("Chuyển đổi Windows Edition (Evaluation → Standard)")
        conversion_layout = QGridLayout()
        
        self.cb_convert_2012 = QCheckBox("Windows Server 2012")
        self.cb_convert_2016 = QCheckBox("Windows Server 2016")
        self.cb_convert_2019 = QCheckBox("Windows Server 2019")
        self.cb_convert_2022 = QCheckBox("Windows Server 2022")
        
        conversion_layout.addWidget(self.cb_convert_2012, 0, 0)
        conversion_layout.addWidget(self.cb_convert_2016, 0, 1)
        conversion_layout.addWidget(self.cb_convert_2019, 1, 0)
        conversion_layout.addWidget(self.cb_convert_2022, 1, 1)
        
        note_label = QLabel("Lưu ý: Chỉ chọn phiên bản khớp với Windows hiện tại")
        note_label.setStyleSheet("font-style: italic; color: #6b7280;")
        conversion_layout.addWidget(note_label, 2, 0, 1, 2)
        
        conversion_group.setLayout(conversion_layout)
        
        # Add to tab
        layout.addWidget(network_group)
        layout.addWidget(advanced_group)
        layout.addWidget(conversion_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Mạng & Nâng cao")
    
    def create_logs_tab(self):
        """Tạo tab Logs & RDP History"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # RDP History
        rdp_group = QGroupBox("Lịch sử đăng nhập RDP")
        rdp_layout = QVBoxLayout()
        
        self.rdp_text = QTextEdit()
        self.rdp_text.setReadOnly(True)
        self.rdp_text.setFont(QFont("Consolas", 9))
        self.rdp_text.setPlainText("Nhấn 'Lấy lịch sử RDP' để xem các địa chỉ IP đã đăng nhập vào máy chủ này.")
        
        rdp_buttons = QHBoxLayout()
        
        self.rdp_refresh_button = QPushButton("Lấy lịch sử RDP")
        self.rdp_refresh_button.clicked.connect(self.refresh_rdp_history)
        
        self.rdp_clear_button = QPushButton("Xóa")
        self.rdp_clear_button.clicked.connect(lambda: self.rdp_text.clear())
        
        self.rdp_export_button = QPushButton("Xuất file")
        self.rdp_export_button.clicked.connect(self.export_rdp_history)
        
        rdp_buttons.addWidget(self.rdp_refresh_button)
        rdp_buttons.addWidget(self.rdp_clear_button)
        rdp_buttons.addWidget(self.rdp_export_button)
        rdp_buttons.addStretch()
        
        rdp_layout.addWidget(self.rdp_text)
        rdp_layout.addLayout(rdp_buttons)
        
        rdp_group.setLayout(rdp_layout)
        
        # Application logs
        log_group = QGroupBox("Nhật ký ứng dụng")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        
        log_buttons = QHBoxLayout()
        
        self.log_clear_button = QPushButton("Xóa log")
        self.log_clear_button.clicked.connect(lambda: self.log_text.clear())
        
        log_buttons.addStretch()
        log_buttons.addWidget(self.log_clear_button)
        
        log_layout.addWidget(self.log_text)
        log_layout.addLayout(log_buttons)
        
        log_group.setLayout(log_layout)
        
        # Add to tab
        layout.addWidget(rdp_group)
        layout.addWidget(log_group)
        
        self.tab_widget.addTab(tab, "Logs & RDP History")
    
    def on_silent_install_changed(self, state):
        """Khi tích 'Cài đặt im lặng' thì untick 'Chỉ tải về'"""
        if state == Qt.Checked and self.cb_download_only.isChecked():
            self.cb_download_only.setChecked(False)
    
    def on_download_only_changed(self, state):
        """Khi tích 'Chỉ tải về' thì untick 'Cài đặt im lặng'"""
        if state == Qt.Checked and self.cb_silent_install.isChecked():
            self.cb_silent_install.setChecked(False)
    
    def toggle_dns_input(self):
        """Toggle giữa DNS combo và custom DNS input"""
        if self.cb_custom_dns.isChecked():
            self.custom_dns_input.setEnabled(True)
            self.dns_combo.setEnabled(False)
        else:
            self.custom_dns_input.setEnabled(False)
            self.dns_combo.setEnabled(True)
    
    def toggle_rdp_port_input(self):
        """Toggle RDP port input khi checkbox được chọn"""
        if self.cb_change_rdp_port.isChecked():
            self.rdp_port_input.setEnabled(True)
            self.rdp_port_input.setFocus()
        else:
            self.rdp_port_input.setEnabled(False)
    
    def get_windows_display_name(self):
        """Lấy tên hiển thị của Windows"""
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
            product_name, _ = winreg.QueryValueEx(key, "ProductName")
            build, _ = winreg.QueryValueEx(key, "CurrentBuild")
            winreg.CloseKey(key)
            return f"{product_name} (Build {build})"
        except:
            return "Windows (Version Unknown)"
    
    def detect_windows_version(self):
        """Phát hiện phiên bản Windows (sử dụng ver command + registry)"""
        try:
            # Phương pháp 1: Sử dụng lệnh ver để lấy build number chính xác
            result = subprocess.run("ver", capture_output=True, text=True, shell=True)
            output = result.stdout
            
            # Parse output từ ver command: "Microsoft Windows [Version X.X.XXXXX.XXXXX]"
            import re as regex
            match = regex.search(r"Version ([0-9]+\.[0-9]+)", output)
            if match:
                version = match.group(1)
                self.log(f"Phát hiện Windows version từ ver command: {version}")
                return version
            
            # Phương pháp 2: Fallback vào registry
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
            version, _ = winreg.QueryValueEx(key, "CurrentVersion")
            winreg.CloseKey(key)
            self.log(f"Phát hiện Windows version từ registry: {version}")
            return version
        except Exception as e:
            self.log(f"Không thể phát hiện Windows version: {str(e)}")
            return "10.0"  # Default to Windows 10
    
    def detect_network_config(self):
        """Phát hiện cấu hình mạng hiện tại"""
        try:
            result = subprocess.run("ipconfig /all", capture_output=True, text=True, encoding='utf-8', errors='ignore', shell=True)
            output = result.stdout
            
            # Parse IP, subnet, gateway
            ip_match = re.search(r"IPv4 Address[.\s]+:\s+([\d.]+)", output)
            subnet_match = re.search(r"Subnet Mask[.\s]+:\s+([\d.]+)", output)
            gateway_match = re.search(r"Default Gateway[.\s]+:\s+([\d.]+)", output)
            
            if ip_match and subnet_match and gateway_match:
                ip = ip_match.group(1)
                subnet = subnet_match.group(1)
                gateway = gateway_match.group(1)
                
                # Bỏ qua loopback và APIPA
                if not (ip.startswith("127.") or ip.startswith("169.254.")):
                    config = f"{ip}|{subnet}|{gateway}"
                    self.ip_input.setText(config)
                    self.log(f"Phát hiện cấu hình mạng: {config}")
        except Exception as e:
            self.log(f"Không thể phát hiện cấu hình mạng: {str(e)}")
    
    def toggle_password_visibility(self):
        """Chuyển đổi hiển thị mật khẩu"""
        if self.password_input.echoMode() == QLineEdit.Password:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.show_password_button.setText("🙈")  # Ẩn mật khẩu
            self.show_password_button.setToolTip("Ẩn mật khẩu")
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.show_password_button.setText("👁")  # Hiển mật khẩu
            self.show_password_button.setToolTip("Hiển mật khẩu")
        
        # Đảm bảo icon luôn có size lớn
        self.show_password_button.setStyleSheet("""
            QPushButton {
                background-color: #f3f4f6;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e5e7eb;
            }
            QPushButton:pressed {
                background-color: #d1d5db;
            }
        """)
    
    def validate_password_strength(self):
        """Kiểm tra độ mạnh mật khẩu"""
        password = self.password_input.text()
        
        if not password:
            self.password_strength_label.setText("")
            return
        
        score = 0
        if len(password) >= 8:
            score += 1
        if re.search(r"[a-z]", password) and re.search(r"[A-Z]", password):
            score += 1
        if re.search(r"\d", password):
            score += 1
        if re.search(r"[!@#$%^&*()_+=\[\]{};':,.<>/?-]", password):
            score += 1
        
        if score == 0:
            strength = "Quá yếu"
            color = "#dc3545"
        elif score == 1:
            strength = "Yếu"
            color = "#ffc107"
        elif score == 2:
            strength = "Trung bình"
            color = "#ffeb3b"
        elif score == 3:
            strength = "Mạnh"
            color = "#8bc34a"
        else:
            strength = "Rất mạnh"
            color = "#4caf50"
        
        self.password_strength_label.setText(f"Độ mạnh: {strength}")
        self.password_strength_label.setStyleSheet(f"color: {color}; font-weight: bold;")
    
    def log(self, message):
        """Ghi log - thread-safe version"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        
        # Check if we're in the main thread
        if threading.current_thread() is threading.main_thread():
            self._append_log(log_message)
        else:
            # Use signal for thread-safe logging from worker threads
            self.log_signal.emit(log_message)
    
    def _append_log(self, log_message):
        """Actually append log to UI - must be called from main thread"""
        try:
            # Kiểm tra log_text đã được khởi tạo chưa
            if hasattr(self, 'log_text') and self.log_text is not None:
                # Hiển thị trong UI
                self.log_text.append(log_message)
                
                # Cuộn xuống cuối - simplified version without QTextCursor issues
                scrollbar = self.log_text.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
            
            # Ghi ra file (không phụ thuộc vào log_text)
            try:
                log_date = datetime.now().strftime("%Y-%m-%d")
                log_file = os.path.join(self.logs_dir, f"fastconfig_{log_date}.log")
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(log_message + "\n")
            except Exception as e:
                print(f"Lỗi ghi log: {str(e)}")
        except Exception as e:
            print(f"Lỗi append log: {str(e)}")
    
    def update_status(self, message):
        """Cập nhật trạng thái - thread-safe"""
        if threading.current_thread() is threading.main_thread():
            self._update_status_ui(message)
        else:
            self.status_signal.emit(message)
    
    @pyqtSlot(str)
    def _update_status_ui(self, message):
        """Cập nhật UI status (chạy trong main thread)"""
        self.status_label.setText(message)
    
    def update_progress(self, value):
        """Cập nhật progress bar - thread-safe"""
        if threading.current_thread() is threading.main_thread():
            self._update_progress_ui(value)
        else:
            self.progress_signal.emit(value)
    
    @pyqtSlot(int)
    def _update_progress_ui(self, value):
        """Cập nhật UI progress (chạy trong main thread)"""
        self.progress_bar.setValue(value)
    
    def count_selected_tasks(self):
        """Đếm số tác vụ được chọn"""
        count = 0
        
        # Software installations
        if self.cb_chrome.isChecked(): count += 1
        if self.cb_firefox.isChecked(): count += 1
        if self.cb_opera.isChecked(): count += 1
        if self.cb_edge.isChecked(): count += 1
        if self.cb_brave.isChecked(): count += 1
        if self.cb_centbrowser.isChecked(): count += 1
        if self.cb_bitvise.isChecked(): count += 1
        if self.cb_proxifier.isChecked(): count += 1
        if self.cb_notepadpp.isChecked(): count += 1
        if self.cb_7zip.isChecked(): count += 1
        if self.cb_winrar.isChecked(): count += 1
        if self.cb_vlc.isChecked(): count += 1
        
        # System configurations
        if self.cb_uac.isChecked(): count += 1
        if self.cb_ieesc.isChecked(): count += 1
        if self.cb_winupdate.isChecked(): count += 1
        if self.cb_trayicon.isChecked(): count += 1
        if self.cb_smallicon.isChecked(): count += 1
        if self.cb_firewall.isChecked(): count += 1
        if self.cb_change_password.isChecked(): count += 1
        if self.cb_change_rdp_port.isChecked(): count += 1
        
        # Network & Advanced
        if self.cb_static_ip.isChecked(): count += 1
        if self.cb_activate.isChecked(): count += 1
        if self.cb_extend_hdd.isChecked(): count += 1
        
        # Windows conversion
        if self.cb_convert_2012.isChecked(): count += 1
        if self.cb_convert_2016.isChecked(): count += 1
        if self.cb_convert_2019.isChecked(): count += 1
        if self.cb_convert_2022.isChecked(): count += 1
        
        return count
    
    def start_processing_mode(self):
        """Chuyển nút sang chế độ đang xử lý"""
        self.is_processing = True
        self.start_button.setText("⏳ Đang xử lý...")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                padding: 8px;
                border-radius: 5px;
                font-size: 13px;
                font-weight: 600;
                min-height: 38px;
            }
        """)
    
    def stop_processing_mode(self):
        """Khôi phục lại nút gốc - thread-safe"""
        if threading.current_thread() is threading.main_thread():
            self._stop_processing_ui()
        else:
            self.stop_processing_signal.emit()
    
    @pyqtSlot()
    def _stop_processing_ui(self):
        """Khôi phục UI nút (chạy trong main thread)"""
        self.is_processing = False
        self.start_button.setText("🚀 Bắt đầu cấu hình")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4f46e5;
                color: white;
                padding: 8px;
                border-radius: 5px;
                font-size: 13px;
                font-weight: 600;
                min-height: 38px;
            }
            QPushButton:hover {
                background-color: #4338ca;
            }
            QPushButton:pressed {
                background-color: #3730a3;
            }
        """)
    
    def start_configuration(self):
        """Bắt đầu quá trình cấu hình"""
        self.total_steps = self.count_selected_tasks()
        
        if self.total_steps == 0:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn ít nhất một tùy chọn để cấu hình!")
            return
        
        self.current_step = 0
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(5)  # Ngay lập tức lên 5% để phản ánh đã nhấn nút
        self.start_button.setEnabled(False)
        self.start_processing_mode()  # Chuyển sang chế độ processing
        
        self.log(f"Bắt đầu cấu hình với {self.total_steps} tác vụ...")
        self.update_status("Đang xử lý...")
        
        # Chạy cấu hình trong thread
        threading.Thread(target=self.run_configuration, daemon=True).start()
    
    def run_configuration(self):
        """Chạy các tác vụ cấu hình"""
        try:
            # Reset error flag và downloaded files list
            self.has_errors = False
            self.downloaded_files = []
            
            # System configurations
            self.process_system_configuration()
            
            # Network configuration
            self.process_network_configuration()
            
            # Advanced options
            self.process_advanced_options()
            
            # Software installations
            self.process_software_installation()
            
            # Nếu có file đã tải trong chế độ download-only, mở thư mục
            if self.downloaded_files and self.cb_download_only.isChecked():
                try:
                    # Mở thư mục Temp và highlight file đầu tiên
                    first_file = self.downloaded_files[0]
                    subprocess.run(f'explorer /select,"{first_file}"', shell=True)
                    self.log(f"📂 Đã mở thư mục chứa {len(self.downloaded_files)} file")
                except Exception as e:
                    self.log(f"⚠️ Không thể mở thư mục: {str(e)}")
            
            # Hoàn thành
            self.update_progress(100)
            self.update_status("Cấu hình hoàn tất!")
            
            # Thông báo kết quả tùy theo có lỗi hay không
            if self.has_errors:
                self.log("⚠️ Cấu hình hoàn tất nhưng có một số lỗi. Kiểm tra log để biết thêm chi tiết.")
                QMetaObject.invokeMethod(
                    self,
                    '_show_warning_message',
                    Qt.QueuedConnection
                )
            else:
                self.log("✓ Cấu hình đã hoàn thành thành công!")
                QMetaObject.invokeMethod(
                    self,
                    '_show_success_message',
                    Qt.QueuedConnection
                )
        
        except Exception as e:
            self.log(f"✗ Lỗi trong quá trình cấu hình: {str(e)}")
            # Hiển thị popup lỗi trong main thread
            error_msg = str(e)
            QMetaObject.invokeMethod(
                self,
                '_show_error_message',
                Qt.QueuedConnection,
                Q_ARG(str, error_msg)
            )
        
        finally:
            # Thread-safe enable button và khôi phục UI
            self.enable_button_signal.emit(True)
            self.stop_processing_mode()
    
    def increment_progress(self, task_name):
        """Tăng progress và cập nhật trạng thái"""
        self.current_step += 1
        progress = int((self.current_step / self.total_steps) * 100)
        self.update_progress(progress)
        self.update_status(f"{task_name} ({self.current_step}/{self.total_steps})")
    
    @pyqtSlot()
    def _show_success_message(self):
        """Hiển thị popup thành công (chạy trong main thread)"""
        QMessageBox.information(self, "Thành công", 
            "Cấu hình đã hoàn thành!\n\nMột số thay đổi có thể cần khởi động lại hệ thống.")
    
    @pyqtSlot()
    def _show_warning_message(self):
        """Hiển thị popup cảnh báo (chạy trong main thread)"""
        QMessageBox.warning(self, "Hoàn tất với lỗi", 
            "Cấu hình đã hoàn tất nhưng có một số lỗi.\n\n"
            "Kiểm tra tab 'Logs & RDP History' để xem chi tiết.\n\n"
            "Một số thay đổi có thể cần khởi động lại hệ thống.")
    
    @pyqtSlot(str)
    def _show_error_message(self, error_msg):
        """Hiển thị popup lỗi (chạy trong main thread)"""
        QMessageBox.critical(self, "Lỗi", f"Đã xảy ra lỗi:\n{error_msg}")
    
    def process_system_configuration(self):
        """Xử lý cấu hình hệ thống"""
        try:
            # UAC
            if self.cb_uac.isChecked():
                self.update_status("Đang tắt UAC...")
                self.set_registry_value(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System",
                    "EnableLUA",
                    0,
                    winreg.REG_DWORD
                )
                self.log("✓ Đã tắt UAC")
                self.increment_progress("Tắt UAC")
            
            # IE ESC
            if self.cb_ieesc.isChecked():
                self.update_status("Đang tắt IE Enhanced Security...")
                self.set_registry_value(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Active Setup\Installed Components\{A509B1A7-37EF-4b3f-8CFC-4F3A74704073}",
                    "IsInstalled",
                    0,
                    winreg.REG_DWORD
                )
                self.log("✓ Đã tắt IE Enhanced Security")
                self.increment_progress("Tắt IE ESC")
            
            # Windows Update
            if self.cb_winupdate.isChecked():
                self.update_status("Đang tắt Windows Update...")
                self.set_registry_value(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update",
                    "AUOptions",
                    1,
                    winreg.REG_DWORD
                )
                self.log("✓ Đã tắt Windows Update")
                self.increment_progress("Tắt Windows Update")
            
            # System Tray Icons
            if self.cb_trayicon.isChecked():
                self.update_status("Đang cấu hình System Tray...")
                self.set_registry_value(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Explorer",
                    "EnableAutoTray",
                    0,
                    winreg.REG_DWORD
                )
                self.log("✓ Đã cấu hình hiển thị tất cả biểu tượng System Tray")
                self.increment_progress("Cấu hình System Tray")
            
            # Taskbar Small Icons
            if self.cb_smallicon.isChecked():
                self.update_status("Đang cấu hình Taskbar...")
                self.set_registry_value(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
                    "TaskbarSmallIcons",
                    1,
                    winreg.REG_DWORD
                )
                self.log("✓ Đã cấu hình Taskbar sử dụng biểu tượng nhỏ")
                self.increment_progress("Cấu hình Taskbar")
            
            # Windows Firewall
            if self.cb_firewall.isChecked():
                self.update_status("Đang tắt Windows Firewall...")
                result = subprocess.run("NetSh Advfirewall set allprofiles state off", 
                                      capture_output=True, shell=True)
                if result.returncode == 0:
                    self.log("✓ Đã tắt Windows Firewall")
                else:
                    self.log(f"✗ Không thể tắt Firewall (code: {result.returncode})")
                self.increment_progress("Tắt Firewall")
            
            # Change Password
            if self.cb_change_password.isChecked():
                password = self.password_input.text()
                if password:
                    self.update_status("Đang thay đổi mật khẩu...")
                    result = subprocess.run(f'net user "%USERNAME%" "{password}"',
                                          capture_output=True, shell=True)
                    if result.returncode == 0:
                        self.log("✓ Đã thay đổi mật khẩu Windows")
                    else:
                        self.log("✗ Không thể thay đổi mật khẩu")
                    self.increment_progress("Thay đổi mật khẩu")
            
            # Change RDP Port
            if self.cb_change_rdp_port.isChecked():
                rdp_port = self.rdp_port_input.text().strip()
                if rdp_port and rdp_port.isdigit():
                    port_num = int(rdp_port)
                    if 1 <= port_num <= 65535:
                        self.update_status(f"Đang thay đổi RDP port thành {rdp_port}...")
                        
                        # Thay đổi port trong registry
                        success1 = self.set_registry_value(
                            winreg.HKEY_LOCAL_MACHINE,
                            r"SYSTEM\CurrentControlSet\Control\Terminal Server\Wds\rdpwd\Tds\tcp",
                            "PortNumber",
                            port_num,
                            winreg.REG_DWORD
                        )
                        
                        success2 = self.set_registry_value(
                            winreg.HKEY_LOCAL_MACHINE,
                            r"SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp",
                            "PortNumber",
                            port_num,
                            winreg.REG_DWORD
                        )
                        
                        if success1 and success2:
                            # Thêm rule firewall cho port mới
                            firewall_cmd = f'netsh advfirewall firewall add rule name="RDP-Custom-{rdp_port}" dir=in action=allow protocol=TCP localport={rdp_port}'
                            subprocess.run(firewall_cmd, capture_output=True, shell=True)
                            
                            self.log(f"✓ Đã thay đổi RDP port thành {rdp_port}")
                            self.log(f"✓ Đã thêm rule firewall cho port {rdp_port}")
                            self.log("⚠️  Cần khởi động lại để áp dụng thay đổi RDP port")
                        else:
                            self.log("✗ Không thể thay đổi RDP port")
                    else:
                        self.log("✗ RDP port không hợp lệ (phải từ 1-65535)")
                else:
                    self.log("✗ RDP port không hợp lệ")
                    
                self.increment_progress("Thay đổi RDP Port")
        
        except Exception as e:
            self.log(f"✗ Lỗi khi cấu hình hệ thống: {str(e)}")
    
    def process_network_configuration(self):
        """Xử lý cấu hình mạng"""
        try:
            if not self.cb_static_ip.isChecked():
                return
            
            self.update_status("Đang cấu hình mạng...")
            
            ip_config = self.ip_input.text()
            parts = ip_config.split("|")
            
            if len(parts) != 3:
                self.log("✗ Định dạng IP không hợp lệ")
                return
            
            ip, subnet, gateway = parts
            
            # Get DNS
            if self.cb_custom_dns.isChecked():
                dns_servers = self.custom_dns_input.text()
            else:
                dns_map = {
                    "Google DNS (8.8.8.8)": "8.8.8.8,8.8.4.4",
                    "Cloudflare DNS (1.1.1.1)": "1.1.1.1,1.0.0.1",
                    "OpenDNS (208.67.222.222)": "208.67.222.222,208.67.220.220",
                    "Quad9 DNS (9.9.9.9)": "9.9.9.9,149.112.112.112"
                }
                dns_servers = dns_map.get(self.dns_combo.currentText(), "8.8.8.8,8.8.4.4")
            
            dns_list = dns_servers.split(",")
            
            # Find network adapter name
            result = subprocess.run("netsh interface show interface", 
                                  capture_output=True, text=True, shell=True)
            
            # Simple parsing - get first connected adapter
            adapter_name = None
            for line in result.stdout.split("\n"):
                if "Connected" in line and "Dedicated" in line:
                    parts = line.split()
                    adapter_name = " ".join(parts[3:])
                    break
            
            if not adapter_name:
                adapter_name = "Ethernet"  # Default fallback
            
            self.log(f"Đang cấu hình adapter: {adapter_name}")
            
            # Set static IP
            cmd = f'netsh interface ip set address "{adapter_name}" static {ip} {subnet} {gateway} 1'
            result = subprocess.run(cmd, capture_output=True, shell=True)
            
            if result.returncode == 0:
                self.log(f"✓ Đã cấu hình IP: {ip}/{subnet}, Gateway: {gateway}")
                
                # Set DNS
                if len(dns_list) > 0:
                    cmd = f'netsh interface ip set dns "{adapter_name}" static {dns_list[0].strip()}'
                    subprocess.run(cmd, capture_output=True, shell=True)
                    self.log(f"✓ Đã cấu hình DNS chính: {dns_list[0].strip()}")
                    
                    if len(dns_list) > 1:
                        cmd = f'netsh interface ip add dns "{adapter_name}" {dns_list[1].strip()} index=2'
                        subprocess.run(cmd, capture_output=True, shell=True)
                        self.log(f"✓ Đã cấu hình DNS phụ: {dns_list[1].strip()}")
            else:
                self.log("✗ Không thể cấu hình IP")
            
            self.increment_progress("Cấu hình mạng")
        
        except Exception as e:
            self.log(f"✗ Lỗi khi cấu hình mạng: {str(e)}")
    
    def process_advanced_options(self):
        """Xử lý tùy chọn nâng cao"""
        try:
            # Windows Activation
            if self.cb_activate.isChecked():
                self.update_status("Đang kích hoạt Windows...")
                result = subprocess.run('cscript //nologo "%SystemRoot%\\system32\\slmgr.vbs" /ato',
                                      capture_output=True, shell=True)
                if result.returncode == 0:
                    self.log("✓ Đã kích hoạt Windows")
                else:
                    self.log("✗ Không thể kích hoạt Windows")
                self.increment_progress("Kích hoạt Windows")
            
            # Extend HDD
            if self.cb_extend_hdd.isChecked():
                self.update_status("Đang mở rộng ổ đĩa...")
                diskpart_commands = "select volume C\nextend\nexit\n"
                result = subprocess.run("diskpart", input=diskpart_commands,
                                      capture_output=True, text=True, shell=True)
                if result.returncode == 0:
                    self.log("✓ Đã mở rộng ổ đĩa hệ thống")
                else:
                    self.log("✗ Không thể mở rộng ổ đĩa")
                self.increment_progress("Mở rộng ổ đĩa")
            
            # Windows Edition Conversion
            conversion_map = {
                self.cb_convert_2012: ("2012", "D2N9P-3P6X9-2R39C-7RTCD-MDVJX"),
                self.cb_convert_2016: ("2016", "WC2BQ-8NRM3-FDDYY-2BFGV-KHKQY"),
                self.cb_convert_2019: ("2019", "N69G4-B89J2-4G8F4-WWYCC-J464C"),
                self.cb_convert_2022: ("2022", "VDYBN-27WPP-V4HQT-9VMD4-VMK7H")
            }
            
            for checkbox, (version, key) in conversion_map.items():
                if checkbox.isChecked():
                    self.update_status(f"Đang chuyển đổi Windows {version}...")
                    cmd = f'DISM /online /Set-Edition:ServerStandard /ProductKey:{key} /AcceptEula'
                    result = subprocess.run(cmd, capture_output=True, shell=True)
                    if result.returncode == 0:
                        self.log(f"✓ Đã chuyển đổi Windows {version} Edition")
                    else:
                        self.log(f"✗ Không thể chuyển đổi Windows {version} (code: {result.returncode})")
                    self.increment_progress(f"Chuyển đổi Windows {version}")
        
        except Exception as e:
            self.log(f"✗ Lỗi khi xử lý tùy chọn nâng cao: {str(e)}")
    
    def process_software_installation(self):
        """Xử lý cài đặt phần mềm"""
        software_map = {
            self.cb_chrome: "Chrome",
            self.cb_firefox: "Firefox",
            self.cb_opera: "Opera",
            self.cb_edge: "Edge",
            self.cb_brave: "Brave",
            self.cb_centbrowser: "Centbrowser",
            self.cb_bitvise: "Bitvise SSH",
            self.cb_proxifier: "Proxifier",
            self.cb_notepadpp: "Notepad++",
            self.cb_7zip: "7-Zip",
            self.cb_winrar: "WinRAR",
            self.cb_vlc: "VLC"
        }
        
        for checkbox, software_name in software_map.items():
            if checkbox.isChecked():
                self.install_software(software_name)
    
    def install_software(self, software_name):
        """Cài đặt một phần mềm - synchronous version for worker thread"""
        try:
            self.update_status(f"Đang chuẩn bị cài đặt {software_name}...")
            
            # Get URL based on Windows version
            software_info = self.SOFTWARE_URLS.get(software_name)
            if not software_info:
                self.log(f"✗ Không tìm thấy thông tin cho {software_name}")
                self.increment_progress(f"Cài đặt {software_name}")
                return
            
            url = software_info.get(self.windows_version, software_info.get("10.0"))
            if not url:
                # Kiểm tra fallback theo version trước
                fallback_key = f"fallback_{self.windows_version}"
                url = software_info.get(fallback_key, software_info.get("fallback"))
            
            filename = software_info.get("filename")
            filepath = os.path.join(tempfile.gettempdir(), filename)
            
            # Bước 1: Tải file
            self.update_status(f"Đang tải {software_name}...")
            self.log(f"📥 Bắt đầu tải {software_name} từ {url}...")
            
            # Download file directly (synchronous) with fallback retry
            download_success = False
            urls_to_try = [url]
            
            # Thêm fallback URLs
            fallback_key = f"fallback_{self.windows_version}"
            if fallback_key in software_info:
                urls_to_try.append(software_info[fallback_key])
            if "fallback" in software_info:
                urls_to_try.append(software_info["fallback"])
            
            for attempt, try_url in enumerate(urls_to_try):
                try:
                    if attempt > 0:
                        self.log(f"🔄 Thử URL dự phòng #{attempt}: {try_url}")
                    
                    # Create SSL context that bypasses certificate verification
                    ssl_context = ssl.create_default_context()
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                    
                    # Tạo request với browser headers để bypass 403
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1'
                    }
                    
                    req = urllib.request.Request(try_url, headers=headers)
                    
                    if try_url.startswith('https://'):
                        opener = urllib.request.build_opener(
                            urllib.request.HTTPSHandler(context=ssl_context)
                        )
                        urllib.request.install_opener(opener)
                    
                    # Tải file với headers
                    with urllib.request.urlopen(req) as response:
                        with open(filepath, 'wb') as out_file:
                            out_file.write(response.read())
                    
                    if os.path.exists(filepath):
                        download_success = True
                        break
                        
                except Exception as download_error:
                    self.log(f"✗ Lỗi tải từ {try_url}: {str(download_error)}")
                    if attempt < len(urls_to_try) - 1:
                        continue
            
            if not download_success or not os.path.exists(filepath):
                self.log(f"✗ Không thể tải {software_name} từ tất cả các URL")
                self.has_errors = True
                # Phải tăng progress trước khi return sớm
                self.current_step += 1.0  # +1.0 vì skip cả download và install
                progress = int((self.current_step / self.total_steps) * 100)
                self.update_progress(progress)
                return
            
            try:
                
                size = os.path.getsize(filepath)
                self.log(f"✓ Tải {software_name} hoàn tất ({size:,} bytes)")
                
                # Cập nhật progress sau khi tải xong (50%)
                self.current_step += 0.5
                progress = int((self.current_step / self.total_steps) * 100)
                self.update_progress(progress)
                self.update_status(f"Đang cài đặt {software_name}...")
                
                # Kiểm tra và đổi tên file MSI nếu cần (cho Chrome)
                if software_name == "Chrome":
                    filepath = self._check_and_rename_msi_file(filepath)
                
                # Bước 2: Cài đặt
                if not self.cb_download_only.isChecked():
                    self.update_status(f"Đang cài đặt {software_name}...")
                    self.log(f"🔧 Bắt đầu cài đặt {software_name}...")
                    
                    # Sử dụng logic cài đặt cải tiến cho Chrome
                    if software_name == "Chrome":
                        success = self._install_chrome_sync(filepath)
                        if success:
                            self.log(f"✓ Cài đặt {software_name} thành công")
                        else:
                            self.log(f"✗ Cài đặt {software_name} thất bại")
                            self.has_errors = True
                    else:
                        # Logic cho các phần mềm khác
                        if software_name == "Firefox":
                            params = "-ms" if self.cb_silent_install.isChecked() else ""
                        elif software_name == "Edge":
                            params = "/silent /install" if self.cb_silent_install.isChecked() else ""
                        elif software_name == "Opera":
                            # Opera silent install (không launch sau khi cài)
                            params = "--silent --launchopera=0" if self.cb_silent_install.isChecked() else ""
                        elif software_name == "Brave":
                            # Brave - test không tham số (giống click đúp)
                            params = ""
                        elif software_name == "Centbrowser":
                            # Centbrowser dùng parameters đặc biệt
                            params = "--cb-auto-update --do-not-launch-chrome --system-level" if self.cb_silent_install.isChecked() else ""
                        elif software_name == "Bitvise SSH":
                            # Bitvise SSH (Inno Setup)
                            params = "-acceptEULA" if self.cb_silent_install.isChecked() else ""
                        elif software_name == "Proxifier":
                            # Proxifier (Inno Setup)
                            params = "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-" if self.cb_silent_install.isChecked() else ""
                        elif software_name == "VLC":
                            # VLC (NSIS)
                            params = "/S" if self.cb_silent_install.isChecked() else ""
                        else:
                            # Default cho NSIS installers (WinRAR, 7-Zip, Notepad++)
                            params = "/S" if self.cb_silent_install.isChecked() else ""
                        
                        # Browser cần timeout lâu hơn
                        is_browser = software_name in ["Chrome", "Firefox", "Edge", "Opera", "Brave", "Centbrowser"]
                        timeout_seconds = 600 if software_name == "Brave" else (450 if is_browser else 300)

                        # VLC và Brave chạy không chờ (Popen - giống click đúp)
                        if software_name == "VLC" or software_name == "Brave":
                            cmd = f'"{filepath}"'
                            self.log(f"   Lệnh: {cmd} (không chờ)")
                            try:
                                subprocess.Popen(cmd, shell=True)
                                time.sleep(3)  # Chờ installer khởi động
                                self.log(f"   ✓ Đã khởi chạy {software_name} installer.")
                            except Exception as e:
                                self.log(f"✗ Không thể khởi chạy {software_name}: {str(e)}")
                                self.has_errors = True
                        else:
                            cmd = f'"{filepath}" {params}'
                            self.log(f"   Lệnh: {cmd}")
                            result = subprocess.run(cmd, shell=True, capture_output=True, timeout=timeout_seconds)

                            if result.returncode == 0:
                                self.log(f"✓ Cài đặt {software_name} thành công")
                                
                                # Chờ thêm cho browser hoàn tất (một số installer spawn process con)
                                if is_browser:
                                    self.log(f"   ⏳ Chờ {software_name} hoàn tất cài đặt...")
                                    time.sleep(3)  # Chờ 3s cho process con hoàn tất
                            else:
                                self.log(f"✗ Cài đặt {software_name} thất bại (exit code: {result.returncode})")
                                self.has_errors = True
                    
                    # Không xóa file tạm ngay - để installer hoàn tất
                    # File nằm trong %TEMP% sẽ tự động dọn dẹp bởi Windows
                    self.log(f"ℹ️ File cài đặt để tại: {filepath}")
                    self.log("ℹ️ Windows sẽ tự động dọn dẹp thư mục Temp.")
                else:
                    self.log(f"📦 Chế độ chỉ tải - bỏ qua cài đặt {software_name}")
                    self.log(f"   File lưu tại: {filepath}")
                    # Thêm vào danh sách file đã tải
                    self.downloaded_files.append(filepath)
                    
            except Exception as e:
                self.log(f"✗ Lỗi khi cài {software_name}: {str(e)}")
                self.has_errors = True
            
        except Exception as e:
            self.log(f"✗ Lỗi khi cài đặt {software_name}: {str(e)}")
            self.has_errors = True
        
        finally:
            # Luôn increment progress để hoàn tất task
            self.current_step += 0.5
            progress = int((self.current_step / self.total_steps) * 100)
            self.update_progress(progress)
    def _check_and_rename_msi_file(self, filepath):
        """Kiểm tra file header và đổi tên nếu là MSI (cho main thread)"""
        try:
            with open(filepath, 'rb') as f:
                header = f.read(8)
            
            # MSI file signature: D0 CF 11 E0 A1 B1 1A E1
            if header[:8] == b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1':
                self.log("🔍 Phát hiện file MSI (header: D0CF11E0)")
                
                if filepath.endswith('.exe'):
                    new_filepath = filepath[:-4] + '.msi'
                    
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            if os.path.exists(new_filepath):
                                os.remove(new_filepath)
                            os.rename(filepath, new_filepath)
                            self.log(f"✓ Đã đổi tên file thành {os.path.basename(new_filepath)}")
                            return new_filepath
                        except Exception as e:
                            if attempt < max_retries - 1:
                                time.sleep(0.5)
                            else:
                                self.log(f"⚠️ Không thể đổi tên file: {str(e)}")
                                return filepath
            
            return filepath
        
        except Exception as e:
            self.log(f"⚠️ Lỗi khi kiểm tra file header: {str(e)}")
            return filepath
    
    def _install_chrome_sync(self, filepath):
        """Cài đặt Chrome với logic cải tiến (cho main thread)"""
        is_msi = filepath.lower().endswith('.msi')
        
        if is_msi:
            methods = [
                ('msiexec /qn', f'msiexec /i "{filepath}" /qn /norestart'),
                ('msiexec /passive', f'msiexec /i "{filepath}" /passive /norestart')
            ]
        else:
            methods = [
                ('AutoIt (/silent /install)', f'"{filepath}" /silent /install'),
                ('Interactive (no params)', f'"{filepath}"')
            ]
        
        for method_name, cmd in methods:
            try:
                self.log(f"🔧 Thử phương pháp: {method_name}")
                self.log(f"   Lệnh: {cmd}")
                
                result = subprocess.run(
                    cmd, 
                    shell=True, 
                    capture_output=True, 
                    text=True, 
                    timeout=300
                )
                
                self.log(f"   Exit code: {result.returncode}")
                
                # Kiểm tra Chrome có thực sự được cài
                chrome_paths = [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
                ]
                
                chrome_found = any(os.path.exists(path) for path in chrome_paths)
                
                if result.returncode == 0:
                    if chrome_found:
                        self.log(f"✓ {method_name} thành công - Chrome đã được cài đặt")
                        return True
                    else:
                        self.log(f"⚠️ Exit code 0 nhưng Chrome không được cài - thử phương pháp tiếp theo")
                else:
                    self.log(f"✗ Phương pháp {method_name} thất bại (exit code: {result.returncode})")
                    if result.stderr:
                        error_msg = result.stderr.strip()
                        if error_msg:
                            self.log(f"   Error: {error_msg[:200]}")
                
            except subprocess.TimeoutExpired:
                self.log(f"⚠️ Timeout - Phương pháp {method_name} chạy quá lâu")
                continue
            except Exception as e:
                self.log(f"✗ Lỗi với phương pháp {method_name}: {str(e)}")
                continue
        
        self.log("✗ Tất cả các phương pháp cài đặt Chrome đều thất bại")
        return False
    
    def on_check_update_click(self):
        """Kiểm tra cập nhật từ GitHub Releases (chạy nền)"""
        threading.Thread(target=self.check_github_update, daemon=True).start()

    def check_github_update(self):
        """Kiểm tra và tải cập nhật từ GitHub Releases"""
        try:
            # Cấu hình GitHub
            GITHUB_REPO = "minhhungtsbd/Fastconfig"
            GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            
            self.update_button.setEnabled(False)
            self.update_status("Đang kiểm tra cập nhật từ GitHub...")
            self.log(f"🔍 Kiểm tra phiên bản mới từ {GITHUB_REPO}...")
            
            # Gọi GitHub API để lấy thông tin release mới nhất
            import urllib.request
            import json
            
            req = urllib.request.Request(GITHUB_API)
            req.add_header('User-Agent', 'FastConfigVPS-Updater')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
            
            latest_version = data.get('tag_name', '').lstrip('v')
            release_url = data.get('html_url', '')
            assets = data.get('assets', [])
            
            self.log(f"ℹ️ Phiên bản hiện tại: {self.VERSION}")
            self.log(f"ℹ️ Phiên bản mới nhất: {latest_version}")
            
            # So sánh phiên bản
            if latest_version == self.VERSION:
                self.log("✓ Bạn đang dùng phiên bản mới nhất.")
                self.show_message_signal.emit(
                    "Cập nhật",
                    f"Bạn đang dùng phiên bản mới nhất ({self.VERSION}).",
                    "info"
                )
                return
            
            # Tìm file EXE trong assets
            exe_asset = None
            for asset in assets:
                if asset['name'].endswith('.exe'):
                    exe_asset = asset
                    break
            
            if not exe_asset:
                self.log("✗ Không tìm thấy file EXE trong bản phát hành mới.")
                self.show_message_signal.emit(
                    "Cập nhật",
                    "Không tìm thấy file cài đặt.",
                    "warning"
                )
                return
            
            # Yêu cầu xác nhận từ main thread và đợi kết quả
            download_url = exe_asset['browser_download_url']
            size_mb = exe_asset['size'] / 1024 / 1024
            
            # Lưu thông tin để dialog handler xử lý
            self.pending_update_url = download_url
            self.pending_update_filename = exe_asset['name']
            
            # Hiển thị dialog từ main thread
            self.show_update_dialog_signal.emit(latest_version, str(size_mb), download_url)
            return  # Function sẽ được tiếp tục từ _download_and_install_update
            
        except urllib.error.URLError as e:
            self.log(f"✗ Lỗi kết nối: {e}")
            self.show_message_signal.emit(
                "Lỗi",
                "Không thể kết nối đến GitHub. Kiểm tra kết nối mạng.",
                "warning"
            )
            self.update_button.setEnabled(True)
        except Exception as e:
            self.log(f"✗ Lỗi cập nhật: {e}")
            import traceback
            self.log(traceback.format_exc())
            self.show_message_signal.emit(
                "Lỗi",
                f"Lỗi cập nhật: {e}",
                "error"
            )
            self.update_button.setEnabled(True)
        finally:
            self.update_status("Sẵn sàng...")

    @pyqtSlot(str, str, str)
    def _show_message_box(self, title, message, msg_type):
        """Hiển thị message box trong main thread"""
        if msg_type == "info":
            QMessageBox.information(self, title, message)
        elif msg_type == "warning":
            QMessageBox.warning(self, title, message)
        elif msg_type == "error":
            QMessageBox.critical(self, title, message)
    
    @pyqtSlot(str, str, float)
    def _show_update_dialog(self, version, size_mb, download_url):
        """Hiển thị dialog xác nhận cập nhật trong main thread"""
        reply = QMessageBox.question(
            self,
            "Cập nhật mới",
            f"Có phiên bản mới: {version}\n\n"
            f"Kích thước: {size_mb} MB\n\n"
            f"Bạn có muốn tải và cài đặt không?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Chạy download trong thread mới
            threading.Thread(
                target=self._download_and_install_update,
                args=(download_url, self.pending_update_filename),
                daemon=True
            ).start()
        else:
            self.log("ℹ️ Người dùng hủy cập nhật.")
            self.update_button.setEnabled(True)
    
    def _download_and_install_update(self, download_url, filename):
        """Tải và cài đặt bản cập nhật"""
        try:
            temp_exe = os.path.join(tempfile.gettempdir(), filename)
            
            self.log(f"📥 Đang tải {filename}...")
            self.update_status(f"Đang tải cập nhật...")
            
            urllib.request.urlretrieve(download_url, temp_exe)
            
            if not os.path.exists(temp_exe):
                self.log("✗ Tải file thất bại.")
                self.show_message_signal.emit(
                    "Lỗi",
                    "Không thể tải file cập nhật.",
                    "error"
                )
                return
            
            self.log(f"✓ Tải thành công: {temp_exe}")
            
            # Tạo updater script
            current_exe = sys.executable if getattr(sys, 'frozen', False) else __file__
            updater_script = os.path.join(tempfile.gettempdir(), "fastconfig_updater.bat")
            
            with open(updater_script, 'w') as f:
                f.write('@echo off\n')
                f.write('echo Đang cập nhật FastConfigVPS...\n')
                f.write('timeout /t 2 /nobreak >nul\n')
                f.write(f'move /Y "{temp_exe}" "{current_exe}" >nul\n')
                f.write(f'start "" "{current_exe}"\n')
                f.write(f'del "{updater_script}"\n')
                f.write('exit\n')
            
            self.log("🔄 Khởi động lại để cài đặt cập nhật...")
            
            # Chạy updater và thoát
            subprocess.Popen([updater_script], shell=True)
            QApplication.quit()
            
        except Exception as e:
            self.log(f"✗ Lỗi tải cập nhật: {e}")
            self.show_message_signal.emit(
                "Lỗi",
                f"Lỗi tải cập nhật: {e}",
                "error"
            )
        finally:
            self.update_button.setEnabled(True)

    def set_registry_value(self, hkey, path, name, value, value_type):
        """Thiết lập giá trị registry"""
        try:
            key = winreg.CreateKeyEx(hkey, path, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, name, 0, value_type, value)
            winreg.CloseKey(key)
            return True
        except Exception as e:
            self.log(f"✗ Lỗi registry: {str(e)}")
            return False
    
    def _set_rdp_text(self, text):
        """Cập nhật nội dung RDP text theo cách thread-safe từ worker thread"""
        try:
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(0, lambda t=text: self.rdp_text.setPlainText(t))
        except Exception:
            # Fallback nếu vì lý do nào đó QTimer không khả dụng
            try:
                self.rdp_text.setPlainText(text)
            except Exception:
                pass
    
    def _log_debug(self, message: str):
        """Ghi log debug an toàn từ worker thread (hiển thị trong Nhật ký ứng dụng)."""
        try:
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(0, lambda m=message: self.log(f"[DEBUG RDP] {m}"))
        except Exception:
            # Nếu không thể, bỏ qua để không làm treo app
            pass
    
    def refresh_rdp_history(self):
        """Lấy lịch sử đăng nhập RDP"""
        self.rdp_text.clear()
        self.rdp_text.append("Đang lấy lịch sử đăng nhập RDP...\n")
        
        # Run in thread
        threading.Thread(target=self.get_rdp_history, daemon=True).start()
    
    def get_rdp_history(self):
        """Lấy danh sách IP addresses đã RDP vào VPS - Support Windows 10 & Server"""
        try:
            import ctypes
            
            self.log("=== BẮT ĐẦU LẤY LỊCH SỬ RDP ===")
            self.log(f"Hệ điều hành: {self.get_windows_display_name()}")
            
            history_text = "🌍 Lịch sử đăng nhập RDP (30 ngày qua)\n"
            history_text += "=" * 70 + "\n\n"
            
            # Kiểm tra quyền Administrator
            try:
                is_admin = ctypes.windll.shell32.IsUserAnAdmin()
                self.log(f"Admin rights: {is_admin}")
            except:
                is_admin = False
                self.log("Cannot check admin rights")
            
            # Lấy các IP đã RDP vào từ nhiều nguồn
            self.log("Gọi _get_rdp_events_aggregate()...")
            rdp_ips = self._get_rdp_events_aggregate()
            self.log(f"Nhận được {len(rdp_ips) if rdp_ips else 0} IP addresses")
            
            if rdp_ips:
                # Lọc bỏ IP local và invalid
                valid_ips = {ip: info for ip, info in rdp_ips.items() 
                           if ip and ip not in ['-', '127.0.0.1', '::1', 'localhost', '0.0.0.0']}
                
                self.log(f"IP hợp lệ: {len(valid_ips)}")
                
                if valid_ips:
                    history_text += f"🎯 Tìm thấy {len(valid_ips)} IP addresses duy nhất đã RDP:\n\n"
                    
                    # Sắp xếp theo số lần kết nối
                    sorted_ips = sorted(valid_ips.items(), key=lambda x: x[1]['count'], reverse=True)
                    
                    history_text += f"{'IP Address':<18} {'Số lần':<8} {'Lần cuối':<20} {'Tài khoản'}\n"
                    history_text += "-" * 70 + "\n"
                    
                    for ip, info in sorted_ips:
                        count = info['count']
                        last_time = info['last_time']
                        accounts = ', '.join(list(set(info['accounts']))[:3])  # Unique accounts, max 3
                        if len(set(info['accounts'])) > 3:
                            accounts += '...'
                        
                        history_text += f"{ip:<18} {count:<8} {last_time:<20} {accounts}\n"
                    
                    history_text += "-" * 70 + "\n"
                    
                    # Thống kê
                    total_connections = sum(info['count'] for info in valid_ips.values())
                    history_text += f"\n📊 Thống kê:\n"
                    history_text += f"• Tổng số lần RDP: {total_connections}\n"
                    history_text += f"• IP addresses duy nhất: {len(valid_ips)}\n"
                    
                    # Top IP
                    if sorted_ips:
                        top_ip = sorted_ips[0]
                        history_text += f"• IP kết nối nhiều nhất: {top_ip[0]} ({top_ip[1]['count']} lần)\n"
                    
                else:
                    history_text += "❌ Không tìm thấy IP từ xa nào đã RDP vào VPS.\n"
            else:
                history_text += "❌ Không tìm thấy sự kiện RDP nào trong 30 ngày qua.\n\n"
                if not is_admin:
                    history_text += "⚠️ Cần quyền Administrator để đọc Event Log.\n"
                else:
                    history_text += "💡 Lý do có thể:\n"
                    history_text += "  • Chưa có RDP connection nào trong 30 ngày qua\n"
                    history_text += "  • Audit Policy chưa được bật\n\n"
                    history_text += "Để bật Audit Policy (chạy cmd as Admin):\n"
                    history_text += "  auditpol /set /subcategory:'Logon' /success:enable\n"
            
            self.log("=== KẾT THÚC LẤY LỊCH SỬ RDP ===")
            
            # Update UI thread-safe
            QMetaObject.invokeMethod(
                self.rdp_text,
                "setPlainText",
                Qt.QueuedConnection,
                Q_ARG(str, history_text)
            )
        
        except Exception as e:
            import traceback
            self.log(f"❌ LỖI: {str(e)}")
            self.log(f"Traceback:\n{traceback.format_exc()}")
            
            error_text = f"❌ Lỗi khi lấy lịch sử RDP: {str(e)}\n"
            
            QMetaObject.invokeMethod(
                self.rdp_text,
                "setPlainText",
                Qt.QueuedConnection,
                Q_ARG(str, error_text)
            )
    
    def _get_rdp_events_aggregate(self):
        """Lấy RDP events từ nhiều nguồn - Support Windows 10 & Server"""
        rdp_ips = {}
        all_events = []
        
        try:
            # Thu thập từ nhiều nguồn
            self.log("Lấy events từ Security log (4624, 4648)...")
            events = self._get_security_events_wevtutil()
            if events:
                all_events.extend(events)
                self.log(f"  → Security: {len(events)} events")
            
            self.log("Lấy events từ TerminalServices logs...")
            ts_events = self._get_terminalservices_events()
            if ts_events:
                all_events.extend(ts_events)
                self.log(f"  → TerminalServices: {len(ts_events)} events")
            
            self.log(f"Tổng cộng: {len(all_events)} events")
            
            # Aggregate theo IP
            for event in all_events:
                ip = event.get('ip_address', '').strip()
                account = event.get('account', 'N/A').strip()
                time = event.get('time')
                
                if ip and ip != '-' and ip not in ['127.0.0.1', '::1']:
                    if ip not in rdp_ips:
                        rdp_ips[ip] = {
                            'count': 0,
                            'accounts': [],
                            'last_time': None
                        }
                    
                    rdp_ips[ip]['count'] += 1
                    if account and account not in rdp_ips[ip]['accounts']:
                        rdp_ips[ip]['accounts'].append(account)
                    
                    # Cập nhật thời gian gần nhất
                    if time:
                        time_str = time.strftime('%m/%d/%Y %H:%M')
                        if not rdp_ips[ip]['last_time'] or time_str > rdp_ips[ip]['last_time']:
                            rdp_ips[ip]['last_time'] = time_str
            
        except Exception as e:
            self.log(f"Lỗi trong _get_rdp_events_aggregate: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            
        return rdp_ips
    
    def _get_security_events_wevtutil(self):
        """Lấy Security events (4624, 4648) bằng wevtutil - Chứa IP"""
        events = []
        try:
            # Lấy Event 4624 và 4648 (cả hai đều có thể chứa IP RDP)
            for event_id in [4624, 4648]:
                cmd = [
                    'wevtutil', 'qe', 'Security',
                    f'/q:*[System[EventID={event_id}]]',
                    '/f:text', '/rd:true', '/c:100'
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    timeout=15,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
                
                if result.returncode == 0 and result.stdout:
                    parsed = self._parse_security_events_text(result.stdout, event_id)
                    events.extend(parsed)
        
        except Exception as e:
            self.log(f"  Lỗi _get_security_events: {str(e)}")
        
        return events
    
    def _get_terminalservices_events(self):
        """Lấy TerminalServices events (1149, 21, 24) - Chứa IP"""
        events = []
        
        # TerminalServices-RemoteConnectionManager Event 1149
        try:
            cmd = [
                'wevtutil', 'qe',
                'Microsoft-Windows-TerminalServices-RemoteConnectionManager/Operational',
                '/q:*[System[EventID=1149]]',
                '/f:text', '/rd:true', '/c:50'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            if result.returncode == 0 and result.stdout:
                parsed = self._parse_ts_events_text(result.stdout, 'RCM-1149')
                events.extend(parsed)
        except:
            pass
        
        # TerminalServices-LocalSessionManager Events 21, 24
        try:
            cmd = [
                'wevtutil', 'qe',
                'Microsoft-Windows-TerminalServices-LocalSessionManager/Operational',
                '/q:*[System[(EventID=21 or EventID=24)]]',
                '/f:text', '/rd:true', '/c:50'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            if result.returncode == 0 and result.stdout:
                parsed = self._parse_ts_events_text(result.stdout, 'LSM')
                events.extend(parsed)
        except:
            pass
        
        return events
    
    def _extract_ip_from_text(self, text):
        """Trích xuất IPv4 từ text"""
        if not text:
            return None
        
        # IPv4 pattern
        ipv4_pattern = r'((25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)){3})'
        match = re.search(ipv4_pattern, text)
        if match:
            return match.group(1)
        return None
    
    def _parse_security_events_text(self, output, event_id):
        """Parse Security event text output từ wevtutil"""
        events = []
        current_event = {}
        
        for line in output.split('\n'):
            line = line.strip()
            
            if line.startswith('Date:'):
                # Lưu event trước
                if 'time' in current_event and current_event.get('ip_address'):
                    events.append(current_event.copy())
                
                # Event mới
                current_event = {'event_id': event_id}
                date_str = line.replace('Date:', '').strip()
                try:
                    current_event['time'] = datetime.strptime(date_str[:19], "%Y-%m-%dT%H:%M:%S")
                except:
                    pass
            
            elif 'Account Name:' in line and 'account' not in current_event:
                parts = line.split(':', 1)
                if len(parts) > 1:
                    account = parts[1].strip()
                    if account and account.upper() not in ['SYSTEM', 'ANONYMOUS LOGON']:
                        current_event['account'] = account
            
            elif 'Network Address:' in line or 'Source Network Address:' in line:
                # Trích xuất IP
                ip = self._extract_ip_from_text(line)
                if ip:
                    current_event['ip_address'] = ip
        
        # Lưu event cuối
        if 'time' in current_event and current_event.get('ip_address'):
            events.append(current_event.copy())
        
        return events
    
    def _parse_ts_events_text(self, output, source):
        """Parse TerminalServices event text output"""
        events = []
        current_event = {}
        
        for line in output.split('\n'):
            line = line.strip()
            
            if line.startswith('Date:'):
                # Lưu event trước
                if 'time' in current_event and current_event.get('ip_address'):
                    events.append(current_event.copy())
                
                # Event mới
                current_event = {'source': source}
                date_str = line.replace('Date:', '').strip()
                try:
                    current_event['time'] = datetime.strptime(date_str[:19], "%Y-%m-%dT%H:%M:%S")
                except:
                    pass
            
            elif 'User:' in line:
                # Trích xuất username
                parts = line.split('User:', 1)
                if len(parts) > 1:
                    user_part = parts[1].strip()
                    # Format: DOMAIN\Username
                    if '\\' in user_part:
                        current_event['account'] = user_part.split('\\')[-1]
                    else:
                        current_event['account'] = user_part
            
            # Trích xuất IP từ bất kỳ dòng nào
            ip = self._extract_ip_from_text(line)
            if ip and 'ip_address' not in current_event:
                current_event['ip_address'] = ip
        
        # Lưu event cuối
        if 'time' in current_event and current_event.get('ip_address'):
            events.append(current_event.copy())
        
        return events
    
    # Giữ các phương thức cũ để tương thích (nếu cần)
    def _get_rdp_ip_addresses(self):
        """Legacy method - giữ để tương thích"""
        return self._get_rdp_events_aggregate()
    
    def _get_rdp_events_win32(self):
        """Lấy RDP events bằng Win32 Event Log (chỉ Logon Type 10)"""
        try:
            import win32evtlog
            import win32evtlogutil
            import win32con
        except ImportError:
            self.log("pywin32 không được cài đặt")
            return []
        
        events = []
        
        try:
            # Mở Security event log
            log_handle = win32evtlog.OpenEventLog(None, "Security")
            self.log("  → Đã mở Security Event Log")
            
            # Tính thời gian 30 ngày trước
            start_time = datetime.now() - timedelta(days=30)
            
            # Đọc events từ mới nhất
            flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
            
            event_records = win32evtlog.ReadEventLog(log_handle, flags, 0)
            
            for event in event_records:
                # Chỉ xem xét Event ID 4624 (Logon)
                if event.EventID != 4624:
                    continue
                    
                # Kiểm tra thời gian
                try:
                    event_time = datetime.fromtimestamp(event.TimeGenerated.timestamp())
                except:
                    continue
                    
                if event_time < start_time:
                    break  # Đã đọc hết events trong 30 ngày
                
                # Parse event data
                try:
                    event_data = event.StringInserts
                    if not event_data or len(event_data) < 20:
                        continue
                        
                    logon_type = event_data[8] if len(event_data) > 8 else None
                    
                    # Chỉ lấy RDP login (Logon Type = 10)
                    if logon_type != '10':
                        continue
                    
                    account = event_data[5] if len(event_data) > 5 else "Unknown"
                    domain = event_data[6] if len(event_data) > 6 else ""
                    ip_address = event_data[18] if len(event_data) > 18 else "-"
                    
                    # Bỏ qua tài khoản hệ thống
                    if account.upper() in ['SYSTEM', 'ANONYMOUS LOGON', 'DWM-1', 'DWM-2']:
                        continue
                    
                    events.append({
                        'time': event_time,
                        'account': account,
                        'domain': domain,
                        'ip_address': ip_address,
                        'login_type': '10',
                        'login_type_name': 'RDP'
                    })
                    
                except (IndexError, ValueError, AttributeError):
                    continue
                    
            win32evtlog.CloseEventLog(log_handle)
            self.log(f"  → Win32: Tìm thấy {len(events)} RDP events")
            
        except Exception as e:
            self.log(f"  → Win32 Error: {str(e)}")
            
        return events
    
    def _get_rdp_events_wevtutil(self):
        """Lấy RDP events bằng wevtutil command"""
        try:
            # Chỉ lấy RDP events (Logon Type 10) trong 30 ngày
            cmd = [
                "wevtutil", "qe", "Security", 
                "/q:*[System[EventID=4624] and EventData[Data[@Name='LogonType']='10']]",
                "/f:text", "/rd:true", "/c:100"
            ]
            
            self.log(f"  → Chạy: {' '.join(cmd[:4])}...")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout:
                events = self._parse_rdp_wevtutil_output(result.stdout)
                self.log(f"  → wevtutil: Tìm thấy {len(events)} RDP events")
                return events
            else:
                self.log(f"  → wevtutil failed: code {result.returncode}")
            
        except Exception as e:
            self.log(f"  → wevtutil Error: {str(e)}")
            
        return []
    
    def _get_rdp_events_powershell(self):
        """Lấy RDP events bằng PowerShell"""
        try:
            # Chỉ lấy RDP events (Logon Type 10)
            ps_script = r'''
            $startTime = (Get-Date).AddDays(-30)
            Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4624; StartTime=$startTime} -MaxEvents 100 | 
            Where-Object { 
                $_.Message -match 'Logon Type:\s+10' -and 
                $_.Message -notmatch 'Account Name:\s+(SYSTEM|ANONYMOUS LOGON|DWM-)' 
            } |
            ForEach-Object {
                $message = $_.Message
                $account = if ($message -match 'Account Name:\s+([^\r\n]+)') { $matches[1].Trim() } else { 'Unknown' }
                $ip = if ($message -match 'Source Network Address:\s+([^\r\n]+)') { $matches[1].Trim() } else { '-' }
                
                "$($_.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss'))|$account|$ip|RDP"
            }
            '''
            
            self.log("  → Chạy PowerShell script...")
            
            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                events = []
                for line in result.stdout.strip().split('\n'):
                    parts = line.strip().split('|')
                    if len(parts) >= 4:
                        try:
                            time_str = parts[0]
                            account = parts[1]
                            ip = parts[2]
                            
                            event_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                            
                            events.append({
                                'time': event_time,
                                'account': account,
                                'ip_address': ip,
                                'login_type': '10',
                                'login_type_name': 'RDP'
                            })
                        except:
                            continue
                
                self.log(f"  → PowerShell: Tìm thấy {len(events)} RDP events")
                return events
            else:
                self.log(f"  → PowerShell failed: code {result.returncode}")
        
        except Exception as e:
            self.log(f"  → PowerShell Error: {str(e)}")
            
        return []
    
    def _parse_rdp_wevtutil_output(self, output):
        """Parse wevtutil output cho RDP events"""
        events = []
        current_event = {}
        
        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            
            if line.startswith('Date:'):
                # Lưu event trước đó nếu hợp lệ
                if 'time' in current_event and current_event.get('is_rdp'):
                    events.append(current_event.copy())
                
                # Bắt đầu event mới
                current_event = {}
                date_str = line.replace('Date:', '').strip()
                try:
                    current_event['time'] = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
                except:
                    try:
                        current_event['time'] = datetime.strptime(date_str[:19], "%Y-%m-%dT%H:%M:%S")
                    except:
                        continue
            
            elif 'Logon Type:' in line and '10' in line:
                # Đây là RDP event
                current_event['is_rdp'] = True
                current_event['login_type'] = '10'
                current_event['login_type_name'] = 'RDP'
                
            elif 'Account Name:' in line and current_event.get('is_rdp'):
                account = line.split(':', 1)[1].strip()
                if account and account.upper() not in ['SYSTEM', 'ANONYMOUS LOGON', 'DWM-1', 'DWM-2']:
                    current_event['account'] = account
                
            elif 'Source Network Address:' in line and current_event.get('is_rdp'):
                ip = line.split(':', 1)[1].strip()
                current_event['ip_address'] = ip if ip != '-' else '-'
        
        # Thêm event cuối nếu hợp lệ
        if 'time' in current_event and current_event.get('is_rdp'):
            events.append(current_event.copy())
        
        # Sắp xếp theo thời gian mới nhất
        events.sort(key=lambda x: x.get('time', datetime.min), reverse=True)
        
        return events
    
    # Các phương thức cũ - giữ lại để tương thích
    def _get_rdp_via_powershell(self):
        """Phương pháp 1: Lấy RDP history bằng PowerShell inline (nhanh, không tạo file tạm)."""
        try:
            self.log("  → Chuẩn bị PowerShell command...")
            
            # PowerShell script tối ưu - inline, không cần file tạm
            ps_command = r"""
$ErrorActionPreference='SilentlyContinue';
$d=(Get-Date).AddDays(-30);
$e=Get-WinEvent -FilterHashtable @{LogName='Security';Id=4624;StartTime=$d} -MaxEvents 500 | Where-Object {
    $x=[xml]$_.ToXml();
    $lt=$x.Event.EventData.Data | Where-Object {$_.Name -eq 'LogonType'} | Select-Object -ExpandProperty '#text';
    $ip=$x.Event.EventData.Data | Where-Object {$_.Name -eq 'IpAddress'} | Select-Object -ExpandProperty '#text';
    ($lt -eq '10') -and ($ip -match '^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
} | Select-Object -First 30 | ForEach-Object {
    $x=[xml]$_.ToXml();
    $d=@{};
    $x.Event.EventData.Data | ForEach-Object {$d[$_.Name]=$_.'#text'};
    [PSCustomObject]@{
        Time=$_.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss');
        User=$d.TargetUserName;
        IP=$d.IpAddress;
        Host=$d.WorkstationName
    }
};
if($e){$e|ConvertTo-Json -Compress}else{'NO_EVENTS'}
"""
            
            self.log(f"  → PowerShell script length: {len(ps_command)} chars")
            self._log_debug("Chạy PowerShell inline query...")
            
            # Chạy PowerShell với command inline (không file tạm)
            cmd = ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_command]
            self.log(f"  → Executing: powershell.exe -NoProfile -ExecutionPolicy Bypass -Command [script]")
            
            self.log("  → Chờ PowerShell thực thi (timeout: 45s)...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=45,  # Tăng timeout lên 45s cho an toàn
                encoding='utf-8',
                errors='ignore',
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            output = result.stdout.strip()
            stderr = result.stderr.strip()
            
            self.log(f"  → PowerShell exit code: {result.returncode}")
            self.log(f"  → stdout length: {len(output)} chars")
            self.log(f"  → stderr length: {len(stderr)} chars")
            
            if stderr:
                self.log(f"  → stderr content: {stderr[:500]}")
            
            if output:
                self.log(f"  → stdout preview: {output[:200]}...")
            else:
                self.log("  → stdout is EMPTY")
            
            self._log_debug(f"PowerShell exit: {result.returncode}, stdout: {len(output)} chars")
            
            # Xử lý kết quả
            if result.returncode != 0:
                self.log(f"  ✗ PowerShell returned non-zero exit code: {result.returncode}")
                if 'UnauthorizedAccessException' in stderr or 'Access is denied' in stderr:
                    self.log("  → Detected ACCESS_DENIED")
                    return {'success': False, 'error': 'ACCESS_DENIED'}
            
            if output == 'NO_EVENTS':
                self.log("  → PowerShell returned 'NO_EVENTS' (no RDP events found)")
                return {'success': True, 'data': [], 'method': 'PowerShell'}
            
            if not output:
                self.log("  → PowerShell returned empty output")
                return {'success': True, 'data': [], 'method': 'PowerShell'}
            
            # Parse JSON
            self.log("  → Parsing JSON output...")
            try:
                import json
                data = json.loads(output)
                
                # Nếu là single object, chuyển thành list
                if isinstance(data, dict):
                    self.log("  → JSON is single object, converting to list")
                    data = [data]
                elif isinstance(data, list):
                    self.log(f"  → JSON is array with {len(data)} items")
                else:
                    self.log(f"  → JSON type: {type(data)}")
                
                self.log(f"  ✓ Successfully parsed {len(data)} RDP records")
                self._log_debug(f"Tìm thấy {len(data)} RDP sessions")
                return {'success': True, 'data': data, 'method': 'PowerShell Get-WinEvent'}
            
            except json.JSONDecodeError as e:
                self.log(f"  ✗ JSON parse error: {str(e)}")
                self.log(f"  → Failed at position: {e.pos if hasattr(e, 'pos') else 'unknown'}")
                self._log_debug(f"JSON parse error: {e}")
                return {'success': False, 'error': f'JSON_PARSE_ERROR: {str(e)}'}
        
        except subprocess.TimeoutExpired:
            self.log("  ✗ PowerShell TIMEOUT sau 45s")
            self._log_debug("PowerShell timeout sau 45s")
            return {'success': False, 'error': 'TIMEOUT'}
        
        except Exception as e:
            import traceback
            self.log(f"  ✗ PowerShell exception: {str(e)}")
            self.log(f"  → Traceback:\n{traceback.format_exc()}")
            self._log_debug(f"PowerShell exception: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _get_rdp_via_wevtutil(self):
        """Phương pháp 2 (Fallback): Dùng wevtutil.exe - tool native Windows, hoạt động trên tất cả versions."""
        try:
            from datetime import datetime, timedelta
            import xml.etree.ElementTree as ET
            
            self.log("  → Chuẩn bị wevtutil query...")
            self._log_debug("Chạy wevtutil query...")
            
            # Tính start time (30 ngày trước)
            start_time = datetime.now() - timedelta(days=30)
            start_str = start_time.strftime('%Y-%m-%dT%H:%M:%S')
            self.log(f"  → Start time filter: {start_str}")
            
            # Query wevtutil với XPath filter
            # Event ID 4624 (Logon), LogonType=10 (RemoteInteractive/RDP)
            query = (
                f"*[System[(EventID=4624) and TimeCreated[@SystemTime>='{start_str}']]] and "
                f"*[EventData[Data[@Name='LogonType']='10']]"
            )
            
            self.log(f"  → XPath query: {query[:100]}...")
            
            cmd = [
                'wevtutil.exe', 'qe', 'Security',
                '/q:' + query,
                '/f:xml',
                '/c:30',  # Lấy tối đa 30 events
                '/rd:true'  # Reverse direction (mới nhất trước)
            ]
            
            self.log(f"  → Executing: {' '.join(cmd[:3])} [query] [options]")
            self.log("  → Chờ wevtutil thực thi (timeout: 30s)...")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8',
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            output = result.stdout.strip()
            stderr = result.stderr.strip()
            
            self.log(f"  → wevtutil exit code: {result.returncode}")
            self.log(f"  → stdout length: {len(output)} chars")
            self.log(f"  → stderr length: {len(stderr)} chars")
            
            if stderr:
                self.log(f"  → stderr content: {stderr[:500]}")
            
            self._log_debug(f"wevtutil exit: {result.returncode}, output: {len(output)} chars")
            
            if result.returncode != 0:
                self.log(f"  ✗ wevtutil returned non-zero exit code: {result.returncode}")
                if 'Access is denied' in stderr or 'access denied' in stderr.lower():
                    self.log("  → Detected ACCESS_DENIED")
                    return {'success': False, 'error': 'ACCESS_DENIED'}
                return {'success': False, 'error': stderr or 'wevtutil failed'}
            
            if not output or len(output) < 100:
                self.log("  → wevtutil returned empty or too short output")
                return {'success': True, 'data': [], 'method': 'wevtutil'}
            
            # Parse XML output
            self.log("  → Parsing XML output...")
            if output:
                self.log(f"  → XML preview: {output[:200]}...")
            
            data = self._parse_wevtutil_xml(output)
            
            if data:
                self.log(f"  ✓ Successfully parsed {len(data)} RDP records from wevtutil")
                self._log_debug(f"wevtutil tìm thấy {len(data)} RDP sessions")
                return {'success': True, 'data': data, 'method': 'wevtutil (Native Windows Tool)'}
            else:
                self.log("  → XML parsing returned no data")
                return {'success': True, 'data': [], 'method': 'wevtutil'}
        
        except subprocess.TimeoutExpired:
            self.log("  ✗ wevtutil TIMEOUT sau 30s")
            self._log_debug("wevtutil timeout sau 30s")
            return {'success': False, 'error': 'TIMEOUT'}
        
        except Exception as e:
            import traceback
            self.log(f"  ✗ wevtutil exception: {str(e)}")
            self.log(f"  → Traceback:\n{traceback.format_exc()}")
            self._log_debug(f"wevtutil exception: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _parse_wevtutil_xml(self, xml_output):
        """Parse XML output từ wevtutil."""
        try:
            import xml.etree.ElementTree as ET
            from datetime import datetime
            import re
            
            self.log("    → Starting XML parsing...")
            results = []
            
            # Wrap in root element nếu có nhiều events
            if not xml_output.startswith('<?xml'):
                self.log("    → Wrapping XML in root element")
                xml_output = '<?xml version="1.0"?><Events>' + xml_output + '</Events>'
            
            self.log("    → Parsing XML string...")
            root = ET.fromstring(xml_output)
            self.log(f"    → Root tag: {root.tag}")
            
            # Namespace cho Windows Event Log XML
            ns = {'ns': 'http://schemas.microsoft.com/win/2004/08/events/event'}
            
            events = root.findall('.//ns:Event', ns) if root.tag.endswith('Events') else [root]
            self.log(f"    → Found {len(events)} Event elements")
            
            for idx, event in enumerate(events):
                self.log(f"    → Processing event {idx+1}/{len(events)}...")
                try:
                    # Lấy TimeCreated
                    time_elem = event.find('.//ns:TimeCreated', ns)
                    time_str = ''
                    if time_elem is not None:
                        system_time = time_elem.get('SystemTime', '')
                        if system_time:
                            dt = datetime.fromisoformat(system_time.replace('Z', '+00:00'))
                            time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Parse EventData
                    event_data = {}
                    for data_elem in event.findall('.//ns:Data', ns):
                        name = data_elem.get('Name', '')
                        value = data_elem.text or ''
                        event_data[name] = value
                    
                    # Lọc LogonType=10 và IPv4
                    logon_type = event_data.get('LogonType', '')
                    ip_address = event_data.get('IpAddress', '')
                    
                    if logon_type == '10' and re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip_address):
                        results.append({
                            'Time': time_str,
                            'User': event_data.get('TargetUserName', ''),
                            'IP': ip_address,
                            'Host': event_data.get('WorkstationName', '')
                        })
                
                except Exception as e:
                    self._log_debug(f"Error parsing event: {str(e)}")
                    continue
            
            return results
        
        except Exception as e:
            self._log_debug(f"XML parse error: {str(e)}")
            return []
    
    def _display_rdp_results(self, data, method):
        """Hiển thị kết quả RDP history."""
        history_text = "Lịch sử đăng nhập RDP (30 ngày gần nhất)\n" + "=" * 80 + "\n\n"
        
        if not data:
            history_text += "⚠️ Không tìm thấy sự kiện đăng nhập RDP nào.\n\n"
            history_text += "Lý do có thể:\n"
            history_text += "• Không có kết nối RDP nào trong 30 ngày qua\n"
            history_text += "• Security Audit chưa được bật\n"
            history_text += "• Event log đã bị xóa hoặc rotate\n\n"
            history_text += "Để bật audit:\n"
            history_text += "  auditpol /set /subcategory:'Logon' /success:enable\n"
        else:
            history_text += f"Tìm thấy {len(data)} phiên đăng nhập\n\n"
            history_text += f"{'Thời gian':<20} {'Tài khoản':<20} {'Địa chỉ IP':<16} {'Workstation':<20}\n"
            history_text += "-" * 80 + "\n"
            
            for item in data:
                time_str = item.get('Time', '')[:19].ljust(20)
                user = item.get('User', '')[:20].ljust(20)
                ip = item.get('IP', '')[:16].ljust(16)
                host = item.get('Host', '')[:20]
                history_text += f"{time_str}{user}{ip}{host}\n"
            
            history_text += f"\n✓ Hiển thị thành công {len(data)} phiên đăng nhập RDP mới nhất\n"
        
        history_text += "\n" + "-" * 80 + "\n"
        history_text += f"Phương thức: {method}\n"
        history_text += f"Nguồn: Security Event Log (Event ID 4624, LogonType=10)\n"
        history_text += f"Hệ điều hành: {self.get_windows_display_name()}\n"
        
        self._set_rdp_text(history_text)
    
    def _display_error_message(self, error):
        """Hiển thị thông báo lỗi."""
        history_text = "Lịch sử đăng nhập RDP\n" + "=" * 80 + "\n\n"
        
        if error == 'ACCESS_DENIED':
            history_text += "❌ Không có quyền truy cập Security Event Log\n\n"
            history_text += "Giải pháp:\n"
            history_text += "1. Chạy ứng dụng với quyền Administrator (Run as Administrator)\n"
            history_text += "2. Hoặc bấm chuột phải vào file .exe → Properties → Compatibility\n"
            history_text += "   → ✓ Run this program as an administrator\n"
        elif error == 'TIMEOUT':
            history_text += "⏱️ Timeout: Truy vấn Event Log quá lâu\n\n"
            history_text += "Lý do có thể:\n"
            history_text += "• Event Log quá lớn (hàng triệu events)\n"
            history_text += "• Hệ thống đang bận\n\n"
            history_text += "Giải pháp:\n"
            history_text += "• Thử lại sau vài phút\n"
            history_text += "• Hoặc xóa bớt Event Log cũ\n"
        else:
            history_text += f"❌ Lỗi: {error}\n\n"
            history_text += "Vui lòng kiểm tra:\n"
            history_text += "• Quyền Administrator\n"
            history_text += "• Security Event Log service đang chạy\n"
        
        self._set_rdp_text(history_text)
    
    def export_rdp_history(self):
        """Xuất lịch sử RDP ra file"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Xuất lịch sử RDP",
            f"rdp_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt)"
        )
        
        if filename:
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(self.rdp_text.toPlainText())
                QMessageBox.information(self, "Thành công", f"Đã xuất lịch sử RDP ra:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể xuất file:\n{str(e)}")
    
    def toggle_theme(self):
        """Chuyển đổi chế độ sáng/tối"""
        if self.current_theme == "light":
            self.current_theme = "dark"
            self.theme_button.setText("🌙")
            self.theme_button.setToolTip("Chuyển sang chế độ sáng")
        else:
            self.current_theme = "light"
            self.theme_button.setText("☀")
            self.theme_button.setToolTip("Chuyển sang chế độ tối")
        
        self.apply_theme()
    
    def apply_theme(self):
        """Áp dụng theme"""
        # Set default font cho toàn bộ app
        app_font = QFont("Segoe UI", 9)
        app_font.setWeight(QFont.Normal)
        QApplication.instance().setFont(app_font)
        
        if self.current_theme == "dark":
            # Update theme button style for dark mode
            if hasattr(self, 'theme_button'):
                self.theme_button.setStyleSheet("""
                    QPushButton {
                        background-color: #1e293b;
                        border: 2px solid #475569;
                        border-radius: 18px;
                        font-size: 20px;
                        padding: 0px;
                        color: #fbbf24;
                    }
                    QPushButton:hover {
                        background-color: #334155;
                        border-color: #64748b;
                    }
                """)
            self.setStyleSheet("""
                QMainWindow, QWidget, QGroupBox {
                    background-color: #1e293b;
                    color: #f8fafc;
                    font-family: 'Segoe UI', 'Roboto', sans-serif;
                }
                QLineEdit, QTextEdit, QComboBox {
                    background-color: #334155;
                    color: #f8fafc;
                    border: 1px solid #475569;
                    border-radius: 4px;
                    padding: 5px;
                    font-family: 'Segoe UI', 'Roboto', sans-serif;
                }
                QGroupBox {
                    border: 1px solid #475569;
                    border-radius: 5px;
                    margin-top: 8px;
                    padding: 8px;
                    font-weight: 600;
                }
                QGroupBox::title {
                    color: #94a3b8;
                    font-weight: 600;
                    font-size: 10pt;
                }
                QCheckBox {
                    color: #f8fafc;
                    font-weight: 500;
                }
                QPushButton {
                    background-color: #4f46e5;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #4338ca;
                }
                QTabWidget::pane {
                    border: 1px solid #475569;
                    background-color: #334155;
                }
                QTabBar::tab {
                    background-color: #1e293b;
                    color: #94a3b8;
                    padding: 8px 16px;
                    border: 1px solid #475569;
                    font-weight: 500;
                }
                QTabBar::tab:selected {
                    background-color: #334155;
                    color: #f8fafc;
                    font-weight: 600;
                }
                QProgressBar {
                    border: 1px solid #475569;
                    border-radius: 4px;
                    text-align: center;
                    background-color: #334155;
                    font-weight: 500;
                }
                QProgressBar::chunk {
                    background-color: #4f46e5;
                }
                QLabel {
                    font-weight: 500;
                }
            """)
        else:
            # Update theme button style for light mode
            if hasattr(self, 'theme_button'):
                self.theme_button.setStyleSheet("""
                    QPushButton {
                        background-color: #ffffff;
                        border: 2px solid #d1d5db;
                        border-radius: 18px;
                        font-size: 20px;
                        padding: 0px;
                        color: #f59e0b;
                    }
                    QPushButton:hover {
                        background-color: #f9fafb;
                        border-color: #9ca3af;
                    }
                """)
            
            self.setStyleSheet("""
                QMainWindow, QWidget, QGroupBox {
                    background-color: #f8fafc;
                    color: #1e293b;
                    font-family: 'Segoe UI', 'Roboto', sans-serif;
                }
                QLineEdit, QTextEdit, QComboBox {
                    background-color: #ffffff;
                    color: #1e293b;
                    border: 1px solid #d1d5db;
                    border-radius: 4px;
                    padding: 5px;
                    font-family: 'Segoe UI', 'Roboto', sans-serif;
                }
                QGroupBox {
                    border: 1px solid #e5e7eb;
                    border-radius: 5px;
                    margin-top: 8px;
                    padding: 8px;
                    font-weight: 600;
                }
                QGroupBox::title {
                    color: #4b5563;
                    font-weight: 600;
                    font-size: 10pt;
                }
                QCheckBox {
                    color: #1e293b;
                    font-weight: 500;
                }
                QPushButton {
                    background-color: #4f46e5;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #4338ca;
                }
                QTabWidget::pane {
                    border: 1px solid #e5e7eb;
                    background-color: #ffffff;
                }
                QTabBar::tab {
                    background-color: #f1f5f9;
                    color: #64748b;
                    padding: 8px 16px;
                    border: 1px solid #e5e7eb;
                    font-weight: 500;
                }
                QTabBar::tab:selected {
                    background-color: #ffffff;
                    color: #1e293b;
                    font-weight: 600;
                }
                QProgressBar {
                    border: 1px solid #e5e7eb;
                    border-radius: 4px;
                    text-align: center;
                    background-color: #f1f5f9;
                    font-weight: 500;
                }
                QProgressBar::chunk {
                    background-color: #4f46e5;
                }
                QLabel {
                    font-weight: 500;
                }
            """)


def main():
    """Hàm main"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = FastConfigVPS()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()