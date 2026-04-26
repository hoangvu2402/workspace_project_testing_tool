import os
import pytest
import allure
from pathlib import Path
from config.config import Config
from core.e2e_runner import E2ERunner
from utils.helpers import Helpers
from utils.logger import log
from logic_manager import AutomationLogic

_logic = AutomationLogic()
_base_url = Config.get_base_url() or ""
SITE_NAME = _logic.get_site_folder_name(_base_url) if _base_url else "unknown_site"

# E2E workflow path is passed via environment variable
E2E_WORKFLOW = os.environ.get("E2E_WORKFLOW", "")
TEST_FILE = Config.get_selected_test_data()

log.info(f"E2E Test | Site: {SITE_NAME} | Workflow: {E2E_WORKFLOW} | Data: {TEST_FILE}")


@allure.feature("E2E Multi-Page Workflow Testing")
class TestE2EWorkflow:

    @allure.story(f"E2E Workflow: {E2E_WORKFLOW}")
    @pytest.mark.parametrize(
        "data",
        Helpers.read_excel_data(f"{TEST_FILE}", site_folder=SITE_NAME) if TEST_FILE else [{}]
    )
    def test_run_e2e_workflow(self, page, data):
        """Execute an E2E multi-page workflow."""
        workflow_path = Path(E2E_WORKFLOW) if E2E_WORKFLOW else None

        if not workflow_path or not workflow_path.exists():
            # Try relative to project
            workflow_path = Config.BASE_DIR / "templates" / SITE_NAME / E2E_WORKFLOW
            if not workflow_path.exists():
                workflow_path = Config.BASE_DIR / "templates" / E2E_WORKFLOW

        assert workflow_path and workflow_path.exists(), \
            f"Khong tim thay workflow E2E: {E2E_WORKFLOW}"

        runner = E2ERunner(page, SITE_NAME, str(workflow_path))
        success = runner.run_test(data)

        expected = data.get("expected_result", "success")
        if success:
            log.info(f"E2E Test Case hoan thanh: Trang thai phu hop voi ky vong ({expected})")
        else:
            pytest.fail("E2E Test Case that bai: Kich ban khong hoan thanh dung muc tieu.")
