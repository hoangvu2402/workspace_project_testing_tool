import os
from pathlib import Path
from dotenv import load_dotenv
from utils.logger import log

# Xác định thư mục gốc của dự án (Root Directory)
BASE_DIR = Path(__file__).resolve().parent.parent

# Load file .env nếu tồn tại
# File .env dùng để lưu các thông tin nhạy cảm (API Key) hoặc cấu hình thay đổi theo máy cá nhân
env_path = BASE_DIR / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    log.info(f"Loaded environment variables from {env_path}")
else:
    log.warning("No .env file found. Using default configurations.")

class Config:
    """
    Lớp quản lý tất cả cấu hình của dự án.
    Nguyên tắc: Ưu tiên biến môi trường (Environment Variable) > File .env > Giá trị mặc định (Default).
    """
    
    # --- Cấu hình Web ---
    # os.getenv("KEY", "DEFAULT") sẽ lấy giá trị của KEY, nếu không thấy sẽ dùng DEFAULT.
    BASE_URL = os.getenv("BASE_URL", "https://www.saucedemo.com")
    BROWSER = os.getenv("BROWSER", "chromium")  # Các tùy chọn: chromium, firefox, webkit
    HEADLESS = os.getenv("HEADLESS", "False").lower() == "true" # Chuyển text thành Boolean
    TIMEOUT = int(os.getenv("TIMEOUT", "30000"))  # Thời gian chờ tối đa (ms)

    # --- Cấu hình AI (Tạm thời để trống cho giai đoạn xây dựng Core Engine) ---
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    AI_MODEL = os.getenv("AI_MODEL", "gemini-1.5-flash")

    # --- Quản lý đường dẫn (Hệ thống tự xác định, không nên sửa qua .env) ---
    REPORTS_DIR = BASE_DIR / "reports"
    TEST_DATA_DIR = BASE_DIR / "test_data"
    SCREENSHOTS_DIR = REPORTS_DIR / "screenshots"

    @classmethod
    def validate_config(cls):
        """Kiểm tra và báo cáo trạng thái cấu hình trước khi bắt đầu test"""
        log.info("--- THÔNG TIN CẤU HÌNH HỆ THỐNG ---")
        log.info(f"Target URL: {cls.BASE_URL}")
        log.info(f"Browser: {cls.BROWSER} (Headless: {cls.HEADLESS})")
        
        if not cls.BASE_URL:
            log.error("CẢNH BÁO: BASE_URL đang trống. Vui lòng kiểm tra file .env hoặc biến môi trường!")

# Tự động thực thi kiểm tra cấu hình khi module này được gọi
Config.validate_config()