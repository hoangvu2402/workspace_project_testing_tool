from pages.base_page import BasePage
from locators.login_locators import LoginLocators
from utils.logger import log

class LoginPage(BasePage):
    """
    Quản lý logic nghiệp vụ cho trang Đăng nhập.
    Sử dụng các Locators được định nghĩa sẵn để thực hiện hành động.
    """

    def login(self, username, password):
        """
        Thực hiện quy trình đăng nhập đầy đủ:
        1. Nhập username
        2. Nhập password
        3. Click nút Login
        """
        log.info(f"Bắt đầu quy trình đăng nhập với user: {username}")
        
        # Sử dụng hàm fill và click đã bọc lại ở BasePage
        self.fill(LoginLocators.USERNAME_INPUT, username, "Trường Username")
        self.fill(LoginLocators.PASSWORD_INPUT, password, "Trường Password")
        self.click(LoginLocators.LOGIN_BUTTON, "Nút Đăng nhập")

    def get_error_message(self):
        """Lấy thông báo lỗi hiển thị trên màn hình khi đăng nhập thất bại."""
        return self.get_text(LoginLocators.ERROR_MESSAGE)

    def is_login_button_visible(self):
        """Kiểm tra xem nút đăng nhập có hiển thị không (dùng cho Assertions)."""
        return self.is_visible(LoginLocators.LOGIN_BUTTON)
        
    def check_successful_login(self):
        """Kiểm tra xem đã vào được trang chủ sau login chưa."""
        return self.is_visible(LoginLocators.APP_LOGO)