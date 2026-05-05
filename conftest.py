import os
from datetime import datetime

import pytest
import allure
from playwright.sync_api import sync_playwright
from config.config import Config
from utils.logger import log
from utils.helpers import Helpers
from core.setup_runner import SetupRunner

@pytest.fixture(scope="session")
def playwright_instance():
    """Khởi tạo instance Playwright dùng cho toàn bộ phiên chạy."""
    with sync_playwright() as playwright:
        yield playwright

@pytest.fixture(scope="session")
def browser(playwright_instance):
    """Khởi tạo trình duyệt dựa trên cấu hình trong Config."""
    browser_name = Config.get_base_browser()
    browser_type = getattr(playwright_instance, browser_name)
    headless = Config.get_headless()
    log.info(f"Khởi động trình duyệt: {browser_name} (headless={headless})")
    
    browser = browser_type.launch(headless=headless)
    yield browser
    
    log.info("Đóng trình duyệt.")
    browser.close()

@pytest.fixture(scope="function")
def page(browser):
    """Khởi tạo một trang (tab) mới cho mỗi test case."""
    context = browser.new_context()
    page = context.new_page()
    page.set_default_timeout(Config.TIMEOUT)
    
    log.info("Khởi tạo Page context mới.")

    # Run setup script if SETUP_SCRIPT env var is set
    setup_script = os.environ.get("SETUP_SCRIPT", "")
    if setup_script:
        log.info(f"Chay setup script truoc test: {setup_script}")
        SetupRunner.run(page, setup_script)
    
    yield page
    
    # Đóng context sau khi xong mỗi test case để giải phóng bộ nhớ
    context.close()

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook của Pytest để kiểm tra kết quả test.
    Nếu test fail, hệ thống sẽ tự động chụp ảnh màn hình và đính kèm vào Allure Report.
    """
    outcome = yield
    report = outcome.get_result()
    
    if report.when == "call" and report.failed:
        # Lấy fixture 'page' từ test case hiện tại
        page = item.funcargs.get("page")
        if page:
            timestamp = datetime.now().strftime("%H%M%S")
            screenshot_name = f"FAILED_{item.name}_{timestamp}"
            # Chụp ảnh và lưu vào thư mục local
            screenshot_path = Helpers.capture_screenshot(page, screenshot_name)
            
            # Đính kèm ảnh vào Allure Report
            if screenshot_path:
                allure.attach.file(
                    screenshot_path,
                    name=f"Screenshot_{item.name}",
                    attachment_type=allure.attachment_type.PNG
                )
                log.error(f"Test case '{item.name}' thất bại. Đã chụp ảnh màn hình.")