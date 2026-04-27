from playwright.sync_api import Page, expect
from utils.logger import log
from config.config import Config


class BasePage:
    def __init__(self, page: Page):
        self.page = page

    def navigate(self, url=""):
        target_url = url if url else Config.get_base_url()
        log.info(f"Dieu huong toi: {target_url}")
        self.page.goto(target_url)

    def click(self, selector: str, name: str = ""):
        """Auto-generated: Click"""
        display_name = name if name else selector
        try:
            log.info(f"Click vao: {display_name}")
            self.page.click(selector)
        except Exception as e:
            log.error(f"Loi khi click: {display_name}: {str(e)}")
            raise

    def dblclick(self, selector: str, name: str = ""):
        """Auto-generated: Double Click"""
        display_name = name if name else selector
        try:
            log.info(f"Double click vao: {display_name}")
            self.page.dblclick(selector)
        except Exception as e:
            log.error(f"Loi khi double click: {display_name}: {str(e)}")
            raise

    def fill(self, selector: str, value: str, name: str = ""):
        """Auto-generated: Fill (nhap text)"""
        display_name = name if name else selector
        try:
            log.info(f"Nhap '{value}' vao: {display_name}")
            self.page.fill(selector, str(value))
        except Exception as e:
            log.error(f"Loi khi fill (nhap text): {display_name}: {str(e)}")
            raise

    def check(self, selector: str, name: str = ""):
        """Auto-generated: Check (checkbox)"""
        display_name = name if name else selector
        try:
            log.info(f"Check: {display_name}")
            self.page.check(selector)
        except Exception as e:
            log.error(f"Loi khi check (checkbox): {display_name}: {str(e)}")
            raise

    def uncheck(self, selector: str, name: str = ""):
        """Auto-generated: Uncheck (checkbox)"""
        display_name = name if name else selector
        try:
            log.info(f"Uncheck: {display_name}")
            self.page.uncheck(selector)
        except Exception as e:
            log.error(f"Loi khi uncheck (checkbox): {display_name}: {str(e)}")
            raise

    def hover(self, selector: str, name: str = ""):
        """Auto-generated: Hover"""
        display_name = name if name else selector
        try:
            log.info(f"Hover len: {display_name}")
            self.page.hover(selector)
        except Exception as e:
            log.error(f"Loi khi hover: {display_name}: {str(e)}")
            raise

    def press(self, selector: str, value: str, name: str = ""):
        """Auto-generated: Press (nhan phim)"""
        display_name = name if name else selector
        try:
            log.info(f"Nhan phim '{value}' tai: {display_name}")
            self.page.press(selector, value)
        except Exception as e:
            log.error(f"Loi khi press (nhan phim): {display_name}: {str(e)}")
            raise

    def type(self, selector: str, value: str, name: str = ""):
        """Auto-generated: Type (go tung ky tu)"""
        display_name = name if name else selector
        try:
            log.info(f"Go '{value}' vao: {display_name}")
            self.page.type(selector, str(value))
        except Exception as e:
            log.error(f"Loi khi type (go tung ky tu): {display_name}: {str(e)}")
            raise

    def select_option(self, selector: str, value: str, name: str = ""):
        """Auto-generated: Select Option"""
        display_name = name if name else selector
        try:
            log.info(f"Chon option '{value}' tai: {display_name}")
            self.page.select_option(selector, str(value))
        except Exception as e:
            log.error(f"Loi khi select option: {display_name}: {str(e)}")
            raise

    def set_input_files(self, selector: str, value: str, name: str = ""):
        """Auto-generated: Upload file"""
        display_name = name if name else selector
        try:
            log.info(f"Upload file '{value}' tai: {display_name}")
            self.page.set_input_files(selector, value)
        except Exception as e:
            log.error(f"Loi khi upload file: {display_name}: {str(e)}")
            raise

    def inner_text(self, selector: str, value: str, name: str = ""):
        """Auto-generated: Verify Text (kiem tra noi dung)"""
        display_name = name if name else selector
        try:
            self.page.wait_for_selector(selector, state="attached", timeout=5000)
            actual = self.page.inner_text(selector).strip()
        except Exception:
            actual = ""
        log.info(f"Kiem tra van ban: Ky vong chua '{value}', thuc te co '{actual}'")
        assert str(value).lower() in actual.lower(), \
            f"Loi noi dung: khong chua '{value}'"

    def is_visible(self, selector: str, name: str = ""):
        """Auto-generated: Verify Visible (kiem tra hien thi)"""
        display_name = name if name else selector
        try:
            self.page.wait_for_selector(selector, state="visible", timeout=5000)
            result = self.page.is_visible(selector)
        except Exception:
            result = False
        log.info(f"Kiem tra hien thi: {display_name} -> {result}")
        assert result, f"Loi hien thi: Khong tim thay phan tu '{display_name}'"

    def wait_for_timeout(self, value: str, name: str = ""):
        """Auto-generated: Wait (cho)"""
        display_name = name
        try:
            log.info(f"Cho trong {value}ms...")
            self.page.wait_for_timeout(int(value) if str(value).isdigit() else 2000)
        except Exception as e:
            log.error(f"Loi khi wait (cho): {display_name}: {str(e)}")
            raise

    def wait_for_selector(self, selector: str, name: str = ""):
        """Auto-generated: Wait for Element"""
        display_name = name if name else selector
        try:
            log.info(f"Cho phan tu: {display_name}")
            self.page.wait_for_selector(selector)
        except Exception as e:
            log.error(f"Loi khi wait for element: {display_name}: {str(e)}")
            raise

    def get_text(self, selector: str) -> str:
        try:
            self.page.wait_for_selector(selector, state="attached", timeout=5000)
            return self.page.inner_text(selector).strip()
        except Exception as e:
            log.error(f"Khong the lay text tu {selector}: {str(e)}")
            return ""

    def get_element_snapshot(self, selector: str) -> dict:
        try:
            self.page.wait_for_selector(selector, state="attached", timeout=3000)
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
            return {}

    def wait_for_element(self, selector: str, timeout: int = 10000):
        try:
            self.page.wait_for_selector(selector, timeout=timeout)
        except Exception as e:
            log.error(f"Het thoi gian cho {selector}: {str(e)}")

    def verify_url(self, expected_url: str):
        current_url = self.page.url
        assert expected_url in current_url, \
            f"Ky vong URL chua '{expected_url}' nhung thuc te la '{current_url}'"
