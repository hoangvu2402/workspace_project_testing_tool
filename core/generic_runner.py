from pages.base_page import BasePage
from utils.logger import log
from utils.helpers import Helpers
from config.config import Config
from core.screenshot_manager import ScreenshotManager
from core.performance_monitor import PerformanceMonitor
from pathlib import Path


class GenericRunner:
    def __init__(self, page, site_name, page_id):
        self.page = page
        self.site_name = site_name
        self.page_id = page_id
        self.base_page = BasePage(page)
        self.screenshot_mgr = ScreenshotManager(str(Config.REPORTS_DIR))
        self.perf_monitor = PerformanceMonitor()
        self.auto_heal = None  # set externally if AI key available
        self.step_results = []  # track per-step results

        base_dir = Config.BASE_DIR

        self.locators = Helpers.load_json_config(base_dir / "locators" / site_name / f"{page_id}.json")
        self.workflow = Helpers.load_json_config(base_dir / "templates" / site_name / f"{page_id}_workflow.json")

    def run_test(self, test_data: dict):
        """Thuc thi toan bo kich ban dua tren mot dong du lieu tu Excel."""
        if not self.locators or not self.workflow:
            log.error(f"Khong the bat dau test: Thieu file cau hinh JSON cho {self.page_id}")
            return False

        self.step_results = []

        try:
            log.info(f"Bat dau kich ban: {self.page_id} cho site {self.site_name}")

            target_url = self.workflow.get("url")
            if target_url:
                self.base_page.navigate(target_url)
                self.perf_monitor.measure_page_load(self.page, target_url)

            steps = self.workflow.get("steps", [])
            for step in steps:
                self._execute_step(step, test_data)

            log.info(f"Hoan thanh kich ban {self.page_id} thanh cong.")
            return True

        except Exception as e:
            log.error(f"Kich ban dung dot ngot do loi: {str(e)}")
            self.screenshot_mgr.capture_on_failure(
                self.page, "final", self.page_id, str(e)
            )
            raise e

    def _execute_step(self, step: dict, test_data: dict):
        """Thuc thi mot buoc don le trong kich ban."""
        step_id = step.get("id")
        action = step.get("action")
        data_key = step.get("data_key")

        selector_info = self.locators.get(step_id, {})
        selector = selector_info.get("selector")
        step_name = selector_info.get("name", step_id)

        value = test_data.get(data_key) if data_key in test_data else step.get("value", "")
        log.info(f"Step '{step_id}' | data_key='{data_key}' | value='{value}'")

        if not selector and action not in ("wait", "verify_url", "navigate"):
            log.warning(f"Bo qua buoc '{step_id}': Khong tim thay Selector.")
            return

        self.perf_monitor.start_step(step_id, action)

        try:
            self._dispatch_action(action, selector, value, step_name, step_id, data_key, test_data)
            self.perf_monitor.end_step(step_id, success=True)
            self.step_results.append({
                "step_id": step_id, "action": action, "status": "passed", "error": ""
            })
        except Exception as e:
            self.perf_monitor.end_step(step_id, success=False)

            # Capture screenshot on failure
            screenshot = self.screenshot_mgr.capture_on_failure(
                self.page, step_id, self.page_id, str(e)
            )

            # Try auto-heal if available
            if self.auto_heal and "Khong tim thay" in str(e) or "Timeout" in str(e):
                heal_result = self.auto_heal.try_heal(
                    self.page, step_id, selector, selector_info
                )
                if heal_result["healed"]:
                    log.info(f"[AutoHeal] Thu lai voi selector moi: {heal_result['new_selector']}")
                    try:
                        self._dispatch_action(
                            action, heal_result["new_selector"], value,
                            step_name, step_id, data_key, test_data
                        )
                        self.step_results.append({
                            "step_id": step_id, "action": action,
                            "status": "healed", "error": "",
                            "new_selector": heal_result["new_selector"],
                        })
                        return
                    except Exception:
                        pass

            self.step_results.append({
                "step_id": step_id, "action": action, "status": "failed",
                "error": str(e), "screenshot": screenshot,
            })
            raise

    def _dispatch_action(self, action, selector, value, step_name, step_id, data_key, test_data):
        """Dispatch to the appropriate action handler."""
        if action == "click":
            self.base_page.click(selector, step_name)

        elif action == "dblclick":
            self.base_page.dblclick(selector, step_name)

        elif action == "fill":
            self.base_page.fill(selector, value, step_name)

        elif action == "fill_password":
            self.base_page.fill(selector, value, step_name)

        elif action == "check":
            self.base_page.check(selector, step_name)

        elif action == "uncheck":
            self.base_page.uncheck(selector, step_name)

        elif action == "hover":
            self.base_page.hover(selector, step_name)

        elif action == "press":
            self.base_page.press(selector, value, step_name)

        elif action == "type":
            self.base_page.type(selector, value, step_name)

        elif action == "select":
            self.page.select_option(selector, str(value))
            log.info(f"Da chon option '{value}' tai {step_name}")

        elif action == "set_input_files":
            self.base_page.set_input_files(selector, value, step_name)

        elif action == "verify_text":
            snapshot = self.base_page.get_element_snapshot(selector)
            actual_text = snapshot.get("text", "")
            log.info(f"Kiem tra van ban: Ky vong chua '{value}', thuc te co '{actual_text}'")
            if not value and actual_text.strip() != "":
                raise AssertionError(
                    f"Step '{step_id}' khong co value (data_key='{data_key}') du thuc te co text: '{actual_text}'"
                )
            assert str(value).lower() in actual_text.lower(), \
                f"Loi noi dung: khong chua '{value}'"

        elif action == "verify_visible":
            is_visible = self.base_page.is_visible(selector)
            if not is_visible:
                self.base_page.get_element_snapshot(selector)
            assert is_visible, f"Loi hien thi: Khong tim thay phan tu '{step_name}'"

        elif action == "verify_url":
            self.base_page.verify_url(value)

        elif action == "wait":
            wait_time = int(value) if str(value).isdigit() else 2000
            log.info(f"Cho trong {wait_time}ms...")
            self.page.wait_for_timeout(wait_time)

        elif action == "wait_for_selector":
            self.base_page.wait_for_selector(selector, step_name)

        elif action == "navigate":
            self.base_page.navigate(value)
