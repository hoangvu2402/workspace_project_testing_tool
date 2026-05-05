import tkinter as tk
from tkinter import ttk
from logic_manager import AutomationLogic
from ui.locator_panel import LocatorPanel
from ui.test_runner_panel import TestRunnerPanel
from ui.action_manager_panel import ActionManagerPanel
from ui.api_testing_panel import APITestingPanel
from ui.db_panel import DBVerificationPanel
from ui.scheduler_panel import SchedulerPanel
from ui.history_panel import HistoryPanel
from ui.ai_tools_panel import AIToolsPanel


class AutomationGeneratorUI:
    """Main application window with multiple tabs for the full testing platform."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Automation Control Center")
        self.root.geometry("1200x950")

        self.logic = AutomationLogic()

        # Shared variables accessible by all panels
        self.shared_vars = {
            "project_path": tk.StringVar(value=str(self.logic.base_dir)),
            "url_path": tk.StringVar(),
            "page_id_var": tk.StringVar(value="login"),
            "browser_var": tk.StringVar(value="chromium"),
        }

        self._build_ui()

    def _build_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Tab 1 - Locator Scanner / Editor
        self.locator_panel = LocatorPanel(notebook, self.logic, self.shared_vars)
        notebook.add(self.locator_panel, text="  Locator Scanner  ")

        # Tab 2 - Test Runner
        self.test_runner_panel = TestRunnerPanel(notebook, self.logic, self.shared_vars)
        notebook.add(self.test_runner_panel, text="  Test Runner  ")

        # Tab 3 - Action Manager
        self.action_manager = ActionManagerPanel(notebook, self.logic, self.shared_vars)
        notebook.add(self.action_manager, text="  Action Manager  ")

        # Tab 4 - API Testing
        self.api_panel = APITestingPanel(notebook, self.logic, self.shared_vars)
        notebook.add(self.api_panel, text="  API Testing  ")

        # Tab 5 - DB Verification
        self.db_panel = DBVerificationPanel(notebook, self.logic, self.shared_vars)
        notebook.add(self.db_panel, text="  DB Verify  ")

        # Tab 6 - Scheduler
        self.scheduler_panel = SchedulerPanel(notebook, self.logic, self.shared_vars)
        notebook.add(self.scheduler_panel, text="  Scheduler  ")

        # Tab 7 - History Dashboard
        self.history_panel = HistoryPanel(notebook, self.logic, self.shared_vars)
        notebook.add(self.history_panel, text="  History  ")

        # Tab 8 - AI Tools
        self.ai_tools_panel = AIToolsPanel(notebook, self.logic, self.shared_vars)
        notebook.add(self.ai_tools_panel, text="  AI Tools  ")

        # When project path changes in locator panel, refresh test runner lists
        self.locator_panel.on_project_changed = self._on_project_changed

    def _on_project_changed(self):
        self.test_runner_panel.refresh_test_list()
        self.test_runner_panel.update_data_list()
