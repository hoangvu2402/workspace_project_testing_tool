from pages.base_page import BasePage
from utils.logger import log
from utils.helpers import Helpers
from config.config import Config


class E2ERunner:
    """
    Runner for multi-page E2E workflows.
    Unlike GenericRunner (single page_id), E2ERunner loads locators from
    multiple pages and each step specifies which page's locators to use.
    The browser session persists across page transitions.
    """

    def __init__(self, page, site_name, workflow_path):
        self.page = page
        self.site_name = site_name
        self.base_page = BasePage(page)
        base_dir = Config.BASE_DIR

        self.workflow = Helpers.load_json_config(workflow_path)

        # Load locators for ALL referenced pages
        self.page_locators = {}
        if self.workflow:
            pages = self.workflow.get("pages", [])
            for page_id in pages:
                locator_path = base_dir / "locators" / site_name / f"{page_id}.json"
                locators = Helpers.load_json_config(locator_path)
                if locators:
                    self.page_locators[page_id] = locators
                    log.info(f"Da tai locators cho trang: {page_id} ({len(locators)} phan tu)")
                else:
                    log.warning(f"Khong tim thay locators cho trang: {page_id}")

    def run_test(self, test_data: dict):
        """Execute the full E2E workflow with data from Excel."""
        if not self.workflow:
            log.error("Khong the bat dau test: Thieu file workflow E2E")
            return False

        if not self.page_locators:
            log.error("Khong the bat dau test: Khong co locators nao duoc tai")
            return False

        try:
            workflow_id = self.workflow.get("workflow_id", "unknown")
            log.info(f"Bat dau kich ban E2E: {workflow_id} cho site {self.site_name}")

            # Navigate to start URL
            start_url = self.workflow.get("start_url", "")
            if start_url:
                self.base_page.navigate(start_url)

            # Execute each step
            steps = self.workflow.get("steps", [])
            current_page_id = None

            for i, step in enumerate(steps, 1):
                step_page_id = step.get("page_id", current_page_id)

                # Log page transition
                if step_page_id != current_page_id:
                    log.info(f"{'='*40}")
                    log.info(f"Chuyen sang trang: {step_page_id}")
                    log.info(f"{'='*40}")
                    current_page_id = step_page_id

                    # Navigate if this step has a URL
                    step_url = step.get("url")
                    if step_url:
                        self.base_page.navigate(step_url)

                self._execute_step(step, test_data, step_page_id, i, len(steps))

            log.info(f"Hoan thanh kich ban E2E: {workflow_id} thanh cong.")
            return True

        except Exception as e:
            log.error(f"Kich ban E2E dung dot ngot do loi: {str(e)}")
            raise e

    def _execute_step(self, step: dict, test_data: dict, page_id: str, step_num: int, total: int):
        """Execute a single step, using locators from the specified page."""
        step_id = step.get("id")
        action = step.get("action")
        data_key = step.get("data_key")

        # Get locators for this step's page
        locators = self.page_locators.get(page_id, {})
        selector_info = locators.get(step_id, {})
        selector = selector_info.get("selector")
        step_name = selector_info.get("name", step_id)

        # Get value: priority from Excel (data_key), then default in step
        value = test_data.get(data_key) if data_key and data_key in test_data else step.get("value", "")
        log.info(f"[{step_num}/{total}] [{page_id}] Step '{step_id}' | action='{action}' | value='{value}'")

        if not selector and action not in ("wait", "verify_url", "navigate"):
            log.warning(f"Bo qua buoc '{step_id}': Khong tim thay Selector trong locators/{page_id}.json")
            return

        if action == "fill" or action == "fill_password":
            self.base_page.fill(selector, value, step_name)

        elif action == "click":
            self.base_page.click(selector, step_name)

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

        elif action == "select":
            self.page.select_option(selector, str(value))
            log.info(f"Da chon option '{value}' tai {step_name}")

        elif action == "navigate":
            nav_url = value or step.get("url", "")
            if nav_url:
                self.base_page.navigate(nav_url)

        elif action == "screenshot":
            path = str(value) if value else f"e2e_{page_id}_{step_id}.png"
            self.page.screenshot(path=path)
            log.info(f"Da chup man hinh: {path}")

        else:
            log.warning(f"Action khong duoc ho tro: '{action}'")
