import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import subprocess
import sys
import os
import traceback
from pathlib import Path
from logic_manager import AutomationLogic


class TestRunnerPanel(ttk.Frame):
    """Panel for running automated tests."""

    def __init__(self, parent, logic: AutomationLogic, shared_vars: dict):
        super().__init__(parent, padding=10)
        self.logic = logic
        self.shared = shared_vars
        self._build_config_section()
        self._build_run_section()
        self._build_log_section()
        self.refresh_test_list()
        self.update_data_list()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_config_section(self):
        cfg = ttk.LabelFrame(self, text=" 1. Cau hinh chay test ", padding=10)
        cfg.pack(fill="x", pady=(0, 5))

        ttk.Label(cfg, text="Thu muc du an:").grid(row=0, column=0, sticky="w")
        ttk.Entry(cfg, textvariable=self.shared["project_path"], width=70, state="readonly").grid(
            row=0, column=1, padx=5, columnspan=3
        )

        ttk.Label(cfg, text="URL muc tieu:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(cfg, textvariable=self.shared["url_path"], width=70, state="readonly").grid(
            row=1, column=1, padx=5, columnspan=3
        )

    def _build_run_section(self):
        run_frame = ttk.LabelFrame(self, text=" 2. Thuc thi Test Case ", padding=10)
        run_frame.pack(fill="x", pady=5)

        ttk.Label(run_frame, text="Chon file test:").grid(row=0, column=0, sticky="w")
        self.test_combo = ttk.Combobox(run_frame, width=40)
        self.test_combo.grid(row=0, column=1, padx=5, sticky="w")

        ttk.Label(run_frame, text="Du lieu test:").grid(row=0, column=2, sticky="w", padx=10)
        self.data_combo = ttk.Combobox(run_frame, width=30)
        self.data_combo.grid(row=0, column=3, padx=5, sticky="w")

        ttk.Label(run_frame, text="Sheet:").grid(row=0, column=4, sticky="w", padx=10)
        self.sheet_var = tk.StringVar(value="Sheet1")
        ttk.Entry(run_frame, textvariable=self.sheet_var, width=15).grid(row=0, column=5)

        btn_frame = ttk.Frame(run_frame)
        btn_frame.grid(row=1, column=0, columnspan=6, pady=10)

        self.run_btn = ttk.Button(btn_frame, text="CHAY TEST", command=self._run_test)
        self.run_btn.pack(side="left", padx=5)

        ttk.Button(btn_frame, text="Nhap Data Test (Excel)", command=self._import_data).pack(
            side="left", padx=5
        )
        ttk.Button(btn_frame, text="Lam moi danh sach", command=self._refresh_all).pack(
            side="left", padx=5
        )

    def _build_log_section(self):
        log_frame = ttk.LabelFrame(self, text=" Nhat ky chay test ", padding=5)
        log_frame.pack(fill="both", expand=True, pady=5)

        self.log_text = tk.Text(log_frame, height=18, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 10))
        self.log_text.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _run_test(self):
        test_file = self.test_combo.get()
        data_file = self.data_combo.get()
        sheet_name = self.sheet_var.get()
        page_id = self.shared["page_id_var"].get()

        if not test_file:
            messagebox.showwarning("Chu y", "Vui long chon file test")
            return

        self.run_btn.config(state="disabled")
        self.log_text.delete(1.0, tk.END)
        self._append_log(f"Dang khoi chay: {test_file}...")

        def run():
            python_exe = sys.executable
            proj_path = self.shared["project_path"].get()

            cmd = [python_exe, "-m", "pytest", test_file, "-v", "-s"]

            env = os.environ.copy()
            env["PYTHONPATH"] = proj_path
            env["BASE_URL"] = self.shared["url_path"].get()
            env["SELECTED_TEST_DATA"] = data_file
            env["SHEET_NAME"] = sheet_name
            env["PAGE_ID"] = page_id
            env["BROWSER"] = self.shared["browser_var"].get()
            env.update({"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"})

            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    env=env,
                )

                if process.stdout:
                    for line in process.stdout:
                        self.after(0, lambda l=line: self._append_log(l))
                process.wait()
                self.after(0, lambda: self._append_log("\nHoan thanh luot chay.\n"))
            except Exception:
                err = traceback.format_exc()
                self.after(0, lambda m=err: self._append_log(f"\nLoi he thong:\n{m}\n"))
            finally:
                self.after(0, lambda: self.run_btn.config(state="normal"))

        threading.Thread(target=run, daemon=True).start()

    def _import_data(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if not file_path:
            return
        url = self.shared["url_path"].get()
        if not url:
            messagebox.showwarning("Chu y", "Vui long nhap URL truoc (tab Locator)")
            return
        new_name = self.logic.import_test_data(self.shared["project_path"].get(), url, file_path)
        self._append_log(f"Da nhap file du lieu: {new_name}")
        self.update_data_list()

    def _refresh_all(self):
        self.refresh_test_list()
        self.update_data_list()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def refresh_test_list(self):
        p = Path(self.shared["project_path"].get()) / "tests"
        if p.exists():
            tests = [str(f.relative_to(self.shared["project_path"].get())) for f in p.glob("test_*.py")]
            self.test_combo["values"] = tests
            if tests:
                self.test_combo.set(tests[0])

    def update_data_list(self):
        try:
            url = self.shared["url_path"].get()
            files = self.logic.get_data_files(self.shared["project_path"].get(), url)
            self.data_combo["values"] = files
            if files:
                self.data_combo.set(files[0])
        except Exception:
            pass

    def _append_log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
