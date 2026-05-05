"""Test Scheduler: schedule automated test runs with notifications."""

import json
import subprocess
import sys
import os
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from utils.logger import log


class ScheduledTask:
    """Represents a scheduled test run."""

    def __init__(self, name: str, template: str, data_file: str, sheet: str = "Sheet1",
                 page_id: str = "", url: str = "", mode: str = "single",
                 schedule_type: str = "once", interval_minutes: int = 60,
                 run_at: str = "", browser: str = "chromium",
                 setup_script: str = "", enabled: bool = True):
        self.name = name
        self.template = template
        self.data_file = data_file
        self.sheet = sheet
        self.page_id = page_id
        self.url = url
        self.mode = mode
        self.schedule_type = schedule_type  # once, interval, daily
        self.interval_minutes = interval_minutes
        self.run_at = run_at  # HH:MM for daily
        self.browser = browser
        self.setup_script = setup_script
        self.enabled = enabled
        self.last_run = None
        self.last_status = ""
        self.next_run = None
        self.run_count = 0

    def to_dict(self):
        return {
            "name": self.name,
            "template": self.template,
            "data_file": self.data_file,
            "sheet": self.sheet,
            "page_id": self.page_id,
            "url": self.url,
            "mode": self.mode,
            "schedule_type": self.schedule_type,
            "interval_minutes": self.interval_minutes,
            "run_at": self.run_at,
            "browser": self.browser,
            "setup_script": self.setup_script,
            "enabled": self.enabled,
            "last_run": self.last_run.isoformat() if self.last_run else "",
            "last_status": self.last_status,
            "run_count": self.run_count,
        }

    @classmethod
    def from_dict(cls, data: dict):
        task = cls(
            name=data.get("name", ""),
            template=data.get("template", ""),
            data_file=data.get("data_file", ""),
            sheet=data.get("sheet", "Sheet1"),
            page_id=data.get("page_id", ""),
            url=data.get("url", ""),
            mode=data.get("mode", "single"),
            schedule_type=data.get("schedule_type", "once"),
            interval_minutes=data.get("interval_minutes", 60),
            run_at=data.get("run_at", ""),
            browser=data.get("browser", "chromium"),
            setup_script=data.get("setup_script", ""),
            enabled=data.get("enabled", True),
        )
        if data.get("last_run"):
            try:
                task.last_run = datetime.fromisoformat(data["last_run"])
            except ValueError:
                pass
        task.last_status = data.get("last_status", "")
        task.run_count = data.get("run_count", 0)
        return task


class TestScheduler:
    """Manages scheduled test runs."""

    def __init__(self, project_path: str = ""):
        self.project_path = project_path
        self.tasks = []
        self._running = False
        self._thread = None
        self._config_path = Path(project_path) / "config" / "schedules.json" if project_path else None
        self._on_task_complete = None  # callback(task, status, output)

    def set_callback(self, callback):
        """Set callback for task completion: callback(task, status, output)."""
        self._on_task_complete = callback

    def add_task(self, task: ScheduledTask):
        """Add a scheduled task."""
        self._calculate_next_run(task)
        self.tasks.append(task)
        self._save_config()
        log.info(f"[Scheduler] Da them task: {task.name} ({task.schedule_type})")

    def remove_task(self, index: int):
        """Remove a task by index."""
        if 0 <= index < len(self.tasks):
            removed = self.tasks.pop(index)
            self._save_config()
            log.info(f"[Scheduler] Da xoa task: {removed.name}")

    def toggle_task(self, index: int):
        """Enable/disable a task."""
        if 0 <= index < len(self.tasks):
            self.tasks[index].enabled = not self.tasks[index].enabled
            self._save_config()

    def start(self):
        """Start the scheduler loop."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._thread.start()
        log.info("[Scheduler] Da bat dau scheduler.")

    def stop(self):
        """Stop the scheduler loop."""
        self._running = False
        log.info("[Scheduler] Da dung scheduler.")

    def _scheduler_loop(self):
        """Main scheduler loop - checks every 30 seconds."""
        while self._running:
            now = datetime.now()
            for task in self.tasks:
                if not task.enabled:
                    continue
                if task.next_run and now >= task.next_run:
                    self._execute_task(task)
                    self._calculate_next_run(task)
            time.sleep(30)

    def _calculate_next_run(self, task: ScheduledTask):
        """Calculate the next run time for a task."""
        now = datetime.now()

        if task.schedule_type == "once":
            if task.run_count == 0:
                task.next_run = now
            else:
                task.next_run = None

        elif task.schedule_type == "interval":
            if task.last_run:
                task.next_run = task.last_run + timedelta(minutes=task.interval_minutes)
            else:
                task.next_run = now

        elif task.schedule_type == "daily":
            if task.run_at:
                try:
                    hour, minute = map(int, task.run_at.split(":"))
                    next_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if next_time <= now:
                        next_time += timedelta(days=1)
                    task.next_run = next_time
                except ValueError:
                    task.next_run = now + timedelta(hours=24)
            else:
                task.next_run = now + timedelta(hours=24)

    def _execute_task(self, task: ScheduledTask):
        """Execute a scheduled task."""
        log.info(f"[Scheduler] Dang chay task: {task.name}")

        test_file = "tests/test_e2e.py" if task.mode == "e2e" else "tests/test_main.py"
        cmd = [sys.executable, "-m", "pytest", test_file, "-v", "-s"]

        env = os.environ.copy()
        env["PYTHONPATH"] = self.project_path
        env["BASE_URL"] = task.url
        env["SELECTED_TEST_DATA"] = Path(task.data_file).name if task.data_file else ""
        env["SHEET_NAME"] = task.sheet
        env["PAGE_ID"] = task.page_id
        env["BROWSER"] = task.browser
        env.update({"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"})

        if task.setup_script:
            env["SETUP_SCRIPT"] = task.setup_script

        if task.mode == "e2e":
            env["E2E_WORKFLOW"] = str(Path(self.project_path) / "templates" / task.template)

        try:
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=env,
                cwd=self.project_path,
                timeout=300,
            )
            task.last_status = "PASSED" if process.returncode == 0 else "FAILED"
            output = process.stdout + process.stderr
        except subprocess.TimeoutExpired:
            task.last_status = "TIMEOUT"
            output = "Test chay qua 5 phut, da bi huy."
        except Exception as e:
            task.last_status = "ERROR"
            output = str(e)

        task.last_run = datetime.now()
        task.run_count += 1
        self._save_config()

        log.info(f"[Scheduler] Task '{task.name}' hoan thanh: {task.last_status}")

        if self._on_task_complete:
            self._on_task_complete(task, task.last_status, output)

    def _save_config(self):
        """Save scheduler config to JSON."""
        if not self._config_path:
            return
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        data = [t.to_dict() for t in self.tasks]
        with open(self._config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_config(self):
        """Load scheduler config from JSON."""
        if not self._config_path or not self._config_path.exists():
            return
        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.tasks = [ScheduledTask.from_dict(d) for d in data]
            for task in self.tasks:
                self._calculate_next_run(task)
            log.info(f"[Scheduler] Da tai {len(self.tasks)} tasks tu config.")
        except Exception as e:
            log.error(f"[Scheduler] Loi tai config: {e}")
