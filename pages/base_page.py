from playwright.sync_api import Page, expect
from utils.logger import log
from config.config import Config

class BasePage:
    """
    Lớp cơ sở cho tất cả các trang trong ứng dụng.
    Cung cấp các phương thức tương tác trình duyệt cơ bản và trích xuất dữ liệu HTML.
    """

    def __init__(self, page: Page):
        self.page = page

    def navigate(self, url=""):
        """Điều hướng đến URL cụ thể hoặc URL mặc định từ Config."""
        target_url = url if url else Config.get_base_url()
        log.info(f"Điều hướng tới: {target_url}")
        self.page.goto(target_url)

    def click(self, selector: str, name: str = ""):
        """Thực hiện click vào phần tử dựa trên selector."""
        display_name = name if name else selector
        try:
            log.info(f"Click vào: {display_name}")
            self.page.click(selector)
        except Exception as e:
            log.error(f"Lỗi khi click vào {display_name}: {str(e)}")
            raise

    def fill(self, selector: str, value: str, name: str = ""):
        """Nhập liệu vào trường văn bản."""
        display_name = name if name else selector
        try:
            log.info(f"Nhập '{value}' vào: {display_name}")
            self.page.fill(selector, str(value))
        except Exception as e:
            log.error(f"Lỗi khi nhập liệu vào {display_name}: {str(e)}")
            raise

    def get_text(self, selector: str) -> str:
        """Lấy nội dung văn bản thuần túy của phần tử."""
        try:
            self.page.wait_for_selector(selector, state="attached", timeout=5000)
            return self.page.inner_text(selector).strip()
        except Exception as e:
            log.error(f"Không thể lấy text từ {selector}: {str(e)}")
            return ""

    def get_element_snapshot(self, selector: str) -> dict:
        """
        [MỚI] Chụp thông tin chi tiết của phần tử để ghi log.
        Lấy thông tin bao gồm: Tag Name, Inner Text, Class, ID và vị trí.
        """
        try:
            # Đảm bảo phần tử tồn tại trước khi lấy thông tin
            self.page.wait_for_selector(selector, state="attached", timeout=3000)
            
            # Thực thi JS để lấy dữ liệu chi tiết từ DOM
            info = self.page.evaluate(f"""
                (sel) => {{
                    const el = document.querySelector(sel);
                    if (!el) return null;
                    return {{
                        tag: el.tagName.toLowerCase(),
                        text: el.innerText || el.value || "",
                        class: el.className,
                        id: el.id,
                        is_visible: el.offsetWidth > 0 && el.offsetHeight > 0
                    }};
                }}
            """, selector)
            
            if info:
                return info
            return {}
        except Exception:
            # Trả về dict rỗng nếu phần tử không tồn tại hoặc có lỗi để không làm gãy luồng chạy
            return {}

    def is_visible(self, selector: str, timeout: int = 5000) -> bool:
        """Kiểm tra xem phần tử có hiển thị trên màn hình hay không."""
        try:
            self.page.wait_for_selector(selector, state="visible", timeout=timeout)
            return self.page.is_visible(selector)
        except:
            return False

    def wait_for_element(self, selector: str, timeout: int = 10000):
        """Chờ đợi phần tử xuất hiện trong DOM."""
        try:
            self.page.wait_for_selector(selector, timeout=timeout)
        except Exception as e:
            log.error(f"Hết thời gian chờ {selector}: {str(e)}")

    def verify_url(self, expected_url: str):
        """Xác nhận URL hiện tại có chứa chuỗi mong đợi."""
        current_url = self.page.url
        assert expected_url in current_url, f"Kỳ vọng URL chứa '{expected_url}' nhưng thực tế là '{current_url}'"