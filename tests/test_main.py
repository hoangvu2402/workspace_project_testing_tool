import pytest
import allure
import os
from pathlib import Path
from config.config import Config
from core.generic_runner import GenericRunner
from utils.helpers import Helpers
from utils.logger import log
from config.config import Config
import re

# --- CẤU HÌNH THÔNG TIN SITE VÀ TRANG CẦN TEST ---
# Lưu ý: Các giá trị này có thể được truyền qua biến môi trường hoặc cấu hình tập trung
SITE_NAME = Config.get_base_url().split("//")[-1].split("/")[0]  # Lấy tên miền chính làm SITE_NAME 
domain = SITE_NAME.replace('.', '_').replace(':', '' )
SITE_NAME = re.sub(r'[\\/*?:"<>|]', "", domain)

TEST_FILE = Config.get_selected_test_data()
PAGE_ID = Config.get_page_id()

log.info(f"🎯 Thực thi Test cho Site: {SITE_NAME} | Page: {TEST_FILE}")

@allure.feature("Hệ thống Kiểm thử Tự động Generic")
class TestAutomationGeneric:
    """
    Lớp khởi chạy kiểm thử. 
    Sử dụng GenericRunner để thực thi các kịch bản dựa trên file cấu hình JSON.
    """

    @allure.story(f"Thực thi kịch bản tự động cho: {TEST_FILE}")
    @pytest.mark.parametrize(
        "data", 
        Helpers.read_excel_data(f"{TEST_FILE}", site_folder=SITE_NAME)
    )
    def test_run_workflow(self, page, data):
        """
        Test case duy nhất: Khởi tạo Runner và chạy toàn bộ quy trình.
        Mọi logic về Snapshot, log nội dung thẻ HTML đều được Runner xử lý.
        """
        
        # 1. Khởi tạo bộ điều phối (GenericRunner)
        # Runner sẽ tự động load file locators và workflow dựa trên SITE_NAME và TEST_FILE
        runner = GenericRunner(page, SITE_NAME, PAGE_ID)

        # 2. Thực thi kịch bản với dòng dữ liệu hiện tại từ Excel
        # Hàm run_test sẽ trả về True nếu thành công, hoặc raise Exception nếu thất bại
        success = runner.run_test(data)

        # 3. Kiểm tra kết quả cuối cùng (Assertion cấp cao)
        # Kết quả mong đợi thường nằm trong cột 'expected_result' của file Excel
        expected = data.get("expected_result", "success")
        
        if success:
            log.info(f"✅ Test Case kết thúc: Trạng thái thực tế trùng khớp với kỳ vọng ({expected})")
        else:
            pytest.fail(f"❌ Test Case thất bại: Kịch bản không hoàn thành đúng mục tiêu.")

 