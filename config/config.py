import os
from pathlib import Path
from dotenv import load_dotenv
from utils.logger import log

BASE_DIR = Path(__file__).resolve().parent.parent

# Load file .env nếu tồn tại
env_path = BASE_DIR / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=False) 
    log.info(f"Loaded environment variables from {env_path}")
else:
    log.warning("No .env file found. Using default configurations.")

class Config:

    BASE_DIR = BASE_DIR
 
    @staticmethod
    def get_base_url():
        return os.environ.get("BASE_URL")

    @staticmethod
    def get_base_browser():
        return os.environ.get("BROWSER", "chromium")

    @staticmethod
    def get_selected_test_data():
        return os.environ.get("SELECTED_TEST_DATA")

    @staticmethod
    def get_selected_sheet():
        return os.environ.get("SHEET_NAME", "Sheet1")

    @staticmethod
    def get_headless():
        return str(os.environ.get("HEADLESS", "False")).lower() == "true"

    @staticmethod
    def get_page_id():
        return os.environ.get("PAGE_ID", "default_page")


    try:
        TIMEOUT = int(os.getenv("TIMEOUT", "30000"))
    except ValueError:
        TIMEOUT = 30000

    # AI later
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    AI_MODEL = os.getenv("AI_MODEL", "gemini-1.5-flash")

    REPORTS_DIR = BASE_DIR / "reports"
    TEST_DATA_DIR = BASE_DIR / "test_data"
    SCREENSHOTS_DIR = REPORTS_DIR / "screenshots"
    

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

Config.validate_config()