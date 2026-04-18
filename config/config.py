import os
from pathlib import Path
from dotenv import load_dotenv
from utils.logger import log

# Xác định thư mục gốc của dự án (Root Directory)
BASE_DIR = Path(__file__).resolve().parent.parent

# Load file .env nếu tồn tại
env_path = BASE_DIR / '.env'
if env_path.exists():
    # Thêm override=False để đảm bảo biến từ UI (os.environ) không bị file .env ghi đè
    load_dotenv(dotenv_path=env_path, override=False) 
    log.info(f"Loaded environment variables from {env_path}")
else:
    log.warning("No .env file found. Using default configurations.")

class Config:
    """
    Lớp quản lý tất cả cấu hình của dự án.
    Nguyên tắc: Biến môi trường > File .env > Giá trị mặc định.
    """
    BASE_DIR = BASE_DIR
    # --- Cấu hình Web ---
    # Lấy URL từ UI truyền vào, nếu không có mới lấy .env, cuối cùng mới là default
    @staticmethod
    def get_base_url():
        return os.environ.get("BASE_URL") or os.getenv("BASE_URL", "https://www.saucedemo.com")
   
    def get_base_browser():
        return os.environ.get("BROWSER") or os.getenv("BROWSER", "chromium")    
    
    def get_selected_test_data():
        return os.environ.get("SELECTED_TEST_DATA") or os.getenv("SELECTED_TEST_DATA", "")
    
    def get_selected_sheet():
        return os.environ.get("SHEET_NAME") or os.getenv("SHEET_NAME", "Sheet1")

    
    def get_headless():
        return str(os.environ.get("HEADLESS") or os.getenv("HEADLESS", "False")).lower() == "true"
    
    def get_page_id():
        return os.environ.get("PAGE_ID") or os.getenv("PAGE_ID", "default_page")

    
    # Thêm ép kiểu an toàn cho TIMEOUT
    try:
        TIMEOUT = int(os.getenv("TIMEOUT", "30000"))
    except ValueError:
        TIMEOUT = 30000

    # --- Cấu hình AI ---
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    AI_MODEL = os.getenv("AI_MODEL", "gemini-1.5-flash")

    # --- Quản lý đường dẫn (Cập nhật để hỗ trợ Generic Framework) ---
    REPORTS_DIR = BASE_DIR / "reports"
    TEST_DATA_DIR = BASE_DIR / "test_data"
    SCREENSHOTS_DIR = REPORTS_DIR / "screenshots"
    
    # sua...
    # Thêm các đường dẫn phục vụ cho việc load JSON linh hoạt
    LOCATORS_DIR = BASE_DIR / "locators"
    TEMPLATES_DIR = BASE_DIR / "templates"
    # sua xong

    @classmethod
    def validate_config(cls):
        """Kiểm tra và báo cáo trạng thái cấu hình trước khi bắt đầu test"""
        log.info("="*50)
        log.info("      THÔNG TIN CẤU HÌNH HỆ THỐNG")
        log.info(f"  > URL Mục tiêu : {cls.get_base_url()}")
        log.info(f"  > Trình duyệt : {cls.get_base_browser()} (Headless: {cls.get_headless()})")
        log.info(f"  > Timeout     : {cls.TIMEOUT} ms")
        log.info("="*50)
        
        if not cls.get_base_url():
            log.error("CẢNH BÁO: BASE_URL đang trống!")

# Tự động thực thi kiểm tra cấu hình
Config.validate_config()