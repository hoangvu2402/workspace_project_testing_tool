from pages.base_page import BasePage
from utils.logger import log
from utils.helpers import Helpers
from config.config import Config
from pathlib import Path

class GenericRunner:
    def __init__(self, page, site_name, page_id):
        self.page = page
        self.site_name = site_name
        self.page_id = page_id
        self.base_page = BasePage(page)
        
        # Đường dẫn gốc tới các thư mục cấu hình
        base_dir = Config.BASE_DIR
        
    
        self.locators = Helpers.load_json_config(base_dir / "locators" / site_name / f"{page_id}.json")
        self.workflow = Helpers.load_json_config(base_dir / "templates" / site_name / f"{page_id}_workflow.json")

    def run_test(self, test_data: dict):
        """
        Thực thi toàn bộ kịch bản dựa trên một dòng dữ liệu từ Excel.
        """
        if not self.locators or not self.workflow:
            log.error(f"❌ Không thể bắt đầu test: Thiếu file cấu hình JSON cho {self.page_id}")
            return False

        try:
            log.info(f"🚀 Bắt đầu kịch bản: {self.page_id} cho site {self.site_name}")
            
            # 1. Điều hướng đến URL được định nghĩa trong Workflow (nếu có)
            target_url = self.workflow.get("url")
            if target_url:
                self.base_page.navigate(target_url)

            # 2. Duyệt qua từng bước trong Workflow
            steps = self.workflow.get("steps", [])
            for step in steps:
                self._execute_step(step, test_data)

            log.info(f"✅ Hoàn thành kịch bản {self.page_id} thành công.")
            return True

        except Exception as e:
            log.error(f"💥 Kịch bản dừng đột ngột do lỗi: {str(e)}")
            raise e

    def _execute_step(self, step: dict, test_data: dict):
        """
        Thực thi một bước đơn lẻ trong kịch bản.
        """
        step_id = step.get("id")
        action = step.get("action")
        data_key = step.get("data_key") # Tên cột trong file Excel
        
        # Lấy Selector từ file locators dựa trên ID của bước
        selector_info = self.locators.get(step_id, {})
        selector = selector_info.get("selector")
        step_name = selector_info.get("name", step_id)

        # Lấy giá trị thực tế: Ưu tiên từ Excel (data_key), sau đó là giá trị mặc định trong step
        value = test_data.get(data_key) if data_key in test_data else step.get("value", "")
        log.info(f"🧩 Step '{step_id}' | data_key='{data_key}' | value='{value}'")
        log.info(f"🧪 TEST DATA KEYS: {list(test_data.keys())}")

        if not selector and action != "wait" and action != "verify_url":
            log.warning(f"⚠️ Bỏ qua bước '{step_id}': Không tìm thấy Selector.")
            return

        if action == "fill":
            self.base_page.fill(selector, value, step_name)
        
        if action == "fill_password":
            self.base_page.fill(selector, value, step_name)

            
        
        elif action == "click":
            self.base_page.click(selector, step_name)
        
        elif action == "verify_text":
            snapshot = self.base_page.get_element_snapshot(selector)
            actual_text = snapshot.get("text", "")
            tx2 = self.base_page.get_text(selector)

            log.info(f"🔍 Kiểm tra văn bản: Kỳ vọng chứa '{value}', thực tế có '{actual_text}'")

            # chặn pass giả nếu value rỗng nhưng thực tế có text (có thể do lỗi locator hoặc thay đổi giao diện)
            if not value and actual_text.strip() != "":
                raise AssertionError(
                    f"❌ Step '{step_id}' không có value (data_key='{data_key}') dù thực tế có text: '{actual_text}'"
                )

            assert str(value).lower() in actual_text.lower(), \
                f"❌ Lỗi nội dung: không chứa '{value}'"

        elif action == "verify_visible":
            is_visible = self.base_page.is_visible(selector)
            if not is_visible:
                self.base_page.get_element_snapshot(selector)
            assert is_visible, f"❌ Lỗi hiển thị: Không tìm thấy phần tử '{step_name}'"

        elif action == "verify_url":
            self.base_page.verify_url(value)

        elif action == "wait":
            wait_time = int(value) if str(value).isdigit() else 2000
            log.info(f"⏱️ Chờ trong {wait_time}ms...")
            self.page.wait_for_timeout(wait_time)

        elif action == "select":
            self.page.select_option(selector, str(value))
            log.info(f"✅ Đã chọn option '{value}' tại {step_name}")