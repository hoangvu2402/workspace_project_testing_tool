from playwright.sync_api import Page, expect
from utils.logger import log
from config.config import Config

class BasePage:
    """
    Lớp cơ sở cho tất cả các trang trong ứng dụng.
    Chứa các hành động chung mà mọi trang đều có thể sử dụng.
    """

    def __init__(self, page: Page):
        self.page = page

    def navigate(self, url=""):
        """Điều hướng đến một URL cụ thể hoặc URL gốc."""
        target_url = url if url else Config.BASE_URL
        log.info(f"Điều hướng đến: {target_url}")
        self.page.goto(target_url)

    def click(self, selector: str, name: str = ""):
        """Click vào một phần tử sau khi chờ nó sẵn sàng."""
        element_name = name if name else selector
        try:
            log.info(f"Click vào phần tử: {element_name}")
            self.page.click(selector)
        except Exception as e:
            log.error(f"Lỗi khi click vào {element_name}: {str(e)}")
            raise

    def fill(self, selector: str, value: str, name: str = ""):
        """Nhập liệu vào một ô input."""
        element_name = name if name else selector
        try:
            log.info(f"Nhập '{value}' vào trường: {element_name}")
            self.page.fill(selector, value)
        except Exception as e:
            log.error(f"Lỗi khi nhập liệu vào {element_name}: {str(e)}")
            raise

    def get_text(self, selector: str) -> str:
        """Lấy nội dung văn bản của một phần tử."""
        try:
            text = self.page.inner_text(selector)
            log.info(f"Lấy text từ {selector}: {text}")
            return text
        except Exception as e:
            log.error(f"Không thể lấy text từ {selector}: {str(e)}")
            return ""

    def is_visible(self, selector: str, timeout: int = 5000) -> bool:
        """Kiểm tra một phần tử có hiển thị hay không."""
        try:
            return self.page.is_visible(selector, timeout=timeout)
        except:
            return False

    def wait_for_element(self, selector: str):
        """Chờ một phần tử xuất hiện trên DOM."""
        log.info(f"Chờ phần tử xuất hiện: {selector}")
        self.page.wait_for_selector(selector)

    def verify_url(self, expected_url: str):
        """Kiểm tra URL hiện tại có khớp với mong đợi không."""
        current_url = self.page.url
        log.info(f"Kiểm tra URL. Hiện tại: {current_url}, Mong đợi: {expected_url}")
        assert current_url == expected_url, f"URL không khớp! Mong đợi {expected_url} nhưng thấy {current_url}"