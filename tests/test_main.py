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

SITE_NAME = Config.get_base_url().split("//")[-1].split("/")[0]  # Lấy tên miền chính làm SITE_NAME 
domain = SITE_NAME.replace('.', '_').replace(':', '' )
SITE_NAME = re.sub(r'[\\/*?:"<>|]', "", domain)

TEST_FILE = Config.get_selected_test_data()
PAGE_ID = Config.get_page_id()

log.info(f"🎯 Thực thi Test cho Site: {SITE_NAME} | Page: {TEST_FILE}")

@allure.feature("Hệ thống Kiểm thử Tự động Generic")
class TestAutomationGeneric:


    @allure.story(f"Thực thi kịch bản tự động cho: {TEST_FILE}")
    @pytest.mark.parametrize(
        "data", 
        Helpers.read_excel_data(f"{TEST_FILE}", site_folder=SITE_NAME)
    )
    def test_run_workflow(self, page, data):

        runner = GenericRunner(page, SITE_NAME, PAGE_ID)

        success = runner.run_test(data)

        expected = data.get("expected_result", "success")
        
        if success:
            log.info(f"✅ Test Case kết thúc: Trạng thái thực tế trùng khớp với kỳ vọng ({expected})")
        else:
            pytest.fail(f"❌ Test Case thất bại: Kịch bản không hoàn thành đúng mục tiêu.")

 