"""
SetupRunner: Execute setup scripts (JSON or Python) on a Playwright page
before scanning or running tests.

JSON scripts define steps with action/selector/value fields.
Python scripts expose a run(page) function.
"""

import json
import importlib.util
from pathlib import Path
from utils.logger import log


class SetupRunner:
    """Runs setup scripts to prepare a browser page (login, dismiss banners, etc.)."""

    SUPPORTED_ACTIONS = {
        "navigate", "click", "fill", "fill_password",
        "wait", "select", "check", "uncheck",
        "press", "hover",
    }

    @staticmethod
    def list_scripts(project_path):
        """Return list of available setup scripts (relative paths under scripts/setup/)."""
        setup_dir = Path(project_path) / "scripts" / "setup"
        if not setup_dir.exists():
            return []
        results = []
        for f in sorted(setup_dir.iterdir()):
            if f.suffix in (".json", ".py") and not f.name.startswith("_"):
                results.append(f.name)
        return results

    @staticmethod
    def run(page, script_path):
        """Execute a setup script on the given Playwright page.

        Args:
            page: Playwright Page object.
            script_path: Absolute path to the setup script file.
        """
        script_path = Path(script_path)
        if not script_path.exists():
            log.error(f"Setup script khong ton tai: {script_path}")
            return False

        log.info(f"Chay setup script: {script_path.name}")

        if script_path.suffix == ".json":
            return SetupRunner._run_json(page, script_path)
        elif script_path.suffix == ".py":
            return SetupRunner._run_python(page, script_path)
        else:
            log.error(f"Dinh dang khong ho tro: {script_path.suffix}")
            return False

    @staticmethod
    def _run_json(page, script_path):
        """Execute a JSON setup script."""
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            name = data.get("name", script_path.stem)
            log.info(f"Setup JSON: {name}")

            steps = data.get("steps", [])
            for i, step in enumerate(steps, 1):
                action = step.get("action", "")
                selector = step.get("selector", "")
                value = step.get("value", "")

                log.info(f"  [{i}/{len(steps)}] {action} | {selector} | {value}")

                if action == "navigate":
                    page.goto(value, timeout=60000)

                elif action == "fill" or action == "fill_password":
                    if selector:
                        page.wait_for_selector(selector, state="attached", timeout=10000)
                        page.fill(selector, str(value))

                elif action == "click":
                    if selector:
                        page.wait_for_selector(selector, state="attached", timeout=10000)
                        page.click(selector)

                elif action == "wait":
                    wait_ms = int(value) if str(value).isdigit() else 2000
                    page.wait_for_timeout(wait_ms)

                elif action == "select":
                    if selector:
                        page.select_option(selector, str(value))

                elif action == "check":
                    if selector:
                        page.check(selector)

                elif action == "uncheck":
                    if selector:
                        page.uncheck(selector)

                elif action == "press":
                    if selector:
                        page.press(selector, str(value))
                    else:
                        page.keyboard.press(str(value))

                elif action == "hover":
                    if selector:
                        page.hover(selector)

                else:
                    log.warning(f"  Action khong ho tro: {action}")

            log.info(f"Setup JSON hoan thanh: {name}")
            return True

        except Exception as e:
            log.error(f"Loi khi chay setup JSON: {e}")
            return False

    @staticmethod
    def _run_python(page, script_path):
        """Execute a Python setup script by calling its run(page) function."""
        try:
            spec = importlib.util.spec_from_file_location(
                script_path.stem, str(script_path)
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if not hasattr(module, "run"):
                log.error(f"Setup script thieu ham run(page): {script_path.name}")
                return False

            module.run(page)
            log.info(f"Setup Python hoan thanh: {script_path.name}")
            return True

        except Exception as e:
            log.error(f"Loi khi chay setup Python: {e}")
            return False
