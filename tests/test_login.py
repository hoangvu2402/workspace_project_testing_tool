import pytest
import allure
import pandas as pd  # <--- Đã thêm để kiểm tra dữ liệu trống (NaN)
from config.config import Config
from pages.login_page import LoginPage
from utils.helpers import Helpers
from utils.logger import log

@allure.feature("Chức năng Đăng nhập")
class TestLogin:
    """
    Tập hợp các test cases cho chức năng Đăng nhập.
    Sử dụng dữ liệu từ file Excel để thực hiện Data-driven testing.
    """

    @allure.story("Đăng nhập với các tập dữ liệu từ Excel")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.parametrize("data", Helpers.read_excel_data("login_data.xlsx", "LoginTests"))
    def test_login_from_excel(self, page, data):
        """
        Test case tổng quát: Đọc user/pass và kết quả mong đợi từ Excel.
        """
        login_page = LoginPage(page)
        
        # --- PHẦN ĐÃ SỬA: Xử lý dữ liệu trống (NaN) để tránh crash trình duyệt ---
        # Kiểm tra nếu ô Excel trống, chuyển thành chuỗi rỗng "" thay vì để giá trị NaN
        username = str(data['username']) if pd.notna(data['username']) else ""
        password = str(data['password']) if pd.notna(data['password']) else ""
        expected_result = data['expected_result']
        # -----------------------------------------------------------------------

        allure.dynamic.title(f"Test Login với User: '{username}'")
        log.info(f"Bắt đầu test case cho user: '{username}'")

        # Bước 1: Điều hướng đến trang web
        login_page.navigate()

        # Bước 2: Thực hiện đăng nhập
        login_page.login(username, password)

        # Bước 3: Kiểm tra kết quả (Assertions)
        if expected_result == "success":
            with allure.step("Kiểm tra đăng nhập thành công"):
                assert login_page.check_successful_login() is True, f"Lẽ ra phải đăng nhập thành công với user {username}"
                log.info(f"Đăng nhập thành công với user: {username}")
        else:
            with allure.step("Kiểm tra thông báo lỗi hiển thị"):
                error_msg = login_page.get_error_message()
                # Kiểm tra xem có lỗi hiển thị không (đối với trường hợp nhập sai hoặc bỏ trống)
                assert len(error_msg) > 0, "Không tìm thấy thông báo lỗi khi thông tin không hợp lệ"
                log.info(f"Đăng nhập thất bại (đúng kỳ vọng) với lỗi: {error_msg}")

    @allure.story("Kiểm tra giao diện trang login")
    def test_login_ui_elements(self, page):
        """Kiểm tra sự hiện diện của các thành phần cơ cả trên trang login."""
        login_page = LoginPage(page)
        login_page.navigate()
        
        allure.step("Kiểm tra nút Login hiển thị")
        assert login_page.is_login_button_visible() is True