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
    """Panel for running automated tests with template/data selection and execution queue."""

    def __init__(self, parent, logic: AutomationLogic, shared_vars: dict):
        super().__init__(parent, padding=10)
        self.logic = logic
        self.shared = shared_vars
        self._queue_items = []  # list of dicts: {template, data, sheet, page_id, url, mode}
        self._is_running = False

        self._build_config_section()
        self._build_add_to_queue_section()
        self._build_queue_section()
        self._build_log_section()
        self._refresh_all()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_config_section(self):
        cfg = ttk.LabelFrame(self, text=" 1. Cau hinh chay test ", padding=10)
        cfg.pack(fill="x", pady=(0, 5))

        ttk.Label(cfg, text="Thu muc du an:").grid(row=0, column=0, sticky="w")
        ttk.Entry(cfg, textvariable=self.shared["project_path"], width=55, state="readonly").grid(
            row=0, column=1, padx=5, columnspan=3
        )

        ttk.Label(cfg, text="Trinh duyet:").grid(row=0, column=4, sticky="w", padx=10)
        browser_combo = ttk.Combobox(cfg, textvariable=self.shared["browser_var"], width=12)
        browser_combo["values"] = ("chromium", "firefox", "webkit")
        browser_combo.grid(row=0, column=5, sticky="w", padx=5)

    def _build_add_to_queue_section(self):
        add_frame = ttk.LabelFrame(self, text=" 2. Chon Template & Du lieu ", padding=10)
        add_frame.pack(fill="x", pady=5)

        # Row 0: test mode selector
        ttk.Label(add_frame, text="Che do:").grid(row=0, column=0, sticky="w")
        mode_frame = ttk.Frame(add_frame)
        mode_frame.grid(row=0, column=1, padx=5, sticky="w", columnspan=3)

        self.mode_var = tk.StringVar(value="single")
        ttk.Radiobutton(mode_frame, text="Don trang", variable=self.mode_var,
                        value="single", command=self._on_mode_changed).pack(side="left", padx=(0, 15))
        ttk.Radiobutton(mode_frame, text="E2E (Da trang)", variable=self.mode_var,
                        value="e2e", command=self._on_mode_changed).pack(side="left")

        # Row 1: template / e2e workflow
        ttk.Label(add_frame, text="Template:").grid(row=1, column=0, sticky="w", pady=5)
        self.template_combo = ttk.Combobox(add_frame, width=45)
        self.template_combo.grid(row=1, column=1, padx=5, sticky="w", columnspan=2)
        self.template_combo.bind("<<ComboboxSelected>>", self._on_template_selected)

        # Row 2: data file + sheet
        ttk.Label(add_frame, text="Du lieu test:").grid(row=2, column=0, sticky="w")
        self.data_combo = ttk.Combobox(add_frame, width=35)
        self.data_combo.grid(row=2, column=1, padx=5, sticky="w")

        ttk.Label(add_frame, text="Sheet:").grid(row=2, column=2, sticky="w", padx=10)
        self.sheet_var = tk.StringVar(value="Sheet1")
        ttk.Entry(add_frame, textvariable=self.sheet_var, width=15).grid(row=2, column=3)

        # Row 3: buttons
        btn_frame = ttk.Frame(add_frame)
        btn_frame.grid(row=3, column=0, columnspan=4, pady=8)

        ttk.Button(btn_frame, text="Them vao hang doi", command=self._add_to_queue).pack(
            side="left", padx=5
        )
        ttk.Button(btn_frame, text="Nhap Data (Excel)", command=self._import_data).pack(
            side="left", padx=5
        )
        ttk.Button(btn_frame, text="Lam moi danh sach", command=self._refresh_all).pack(
            side="left", padx=5
        )

    def _build_queue_section(self):
        q_frame = ttk.LabelFrame(self, text=" 3. Hang doi thuc thi ", padding=10)
        q_frame.pack(fill="x", pady=5)

        # Queue treeview
        columns = ("STT", "Loai", "Template", "Data", "Sheet", "PageID", "URL")
        self.queue_tree = ttk.Treeview(q_frame, columns=columns, show="headings", height=6)
        self.queue_tree.heading("STT", text="#")
        self.queue_tree.heading("Loai", text="Loai")
        self.queue_tree.heading("Template", text="Template")
        self.queue_tree.heading("Data", text="Du lieu")
        self.queue_tree.heading("Sheet", text="Sheet")
        self.queue_tree.heading("PageID", text="Page ID")
        self.queue_tree.heading("URL", text="URL")

        self.queue_tree.column("STT", width=30)
        self.queue_tree.column("Loai", width=55)
        self.queue_tree.column("Template", width=180)
        self.queue_tree.column("Data", width=140)
        self.queue_tree.column("Sheet", width=55)
        self.queue_tree.column("PageID", width=75)
        self.queue_tree.column("URL", width=180)

        self.queue_tree.pack(fill="x", side="top")

        scrollbar = ttk.Scrollbar(q_frame, orient="vertical", command=self.queue_tree.yview)
        self.queue_tree.configure(yscrollcommand=scrollbar.set)

        # Queue control buttons
        qbtn_frame = ttk.Frame(q_frame)
        qbtn_frame.pack(fill="x", pady=5)

        ttk.Button(qbtn_frame, text="Len", command=self._move_up).pack(side="left", padx=3)
        ttk.Button(qbtn_frame, text="Xuong", command=self._move_down).pack(side="left", padx=3)
        ttk.Button(qbtn_frame, text="Xoa muc chon", command=self._remove_selected).pack(
            side="left", padx=3
        )
        ttk.Button(qbtn_frame, text="Xoa tat ca", command=self._clear_queue).pack(
            side="left", padx=3
        )

        self.run_btn = ttk.Button(qbtn_frame, text="CHAY TAT CA", command=self._run_queue)
        self.run_btn.pack(side="right", padx=10)

        self.run_single_btn = ttk.Button(qbtn_frame, text="CHAY MUC CHON", command=self._run_selected)
        self.run_single_btn.pack(side="right", padx=3)

    def _build_log_section(self):
        log_frame = ttk.LabelFrame(self, text=" Nhat ky chay test ", padding=5)
        log_frame.pack(fill="both", expand=True, pady=5)

        self.log_text = tk.Text(log_frame, height=12, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 10))
        self.log_text.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    # Mode switching
    # ------------------------------------------------------------------

    def _on_mode_changed(self):
        """Refresh template list when mode changes between single-page and E2E."""
        self._refresh_template_list()

    # ------------------------------------------------------------------
    # Template / data selection
    # ------------------------------------------------------------------

    def _on_template_selected(self, event=None):
        """When a template is selected, auto-fill related fields."""
        template_rel = self.template_combo.get()
        if not template_rel:
            return
        proj = self.shared["project_path"].get()
        info = self.logic.get_template_info(proj, template_rel)
        if info:
            url = info.get("url") or info.get("start_url", "")
            page_id = info.get("page_id", "")
            if url:
                self.shared["url_path"].set(url)
            if page_id:
                self.shared["page_id_var"].set(page_id)
            # Try to auto-select matching data files for this site
            site_folder = str(Path(template_rel).parent)
            data_files = self.logic.get_all_data_files(proj)
            matching = [d for d in data_files if d.startswith(site_folder + "/") or d.startswith(site_folder + "\\")]
            if matching:
                self.data_combo["values"] = matching
                self.data_combo.set(matching[0])
            else:
                self.data_combo["values"] = data_files
                if data_files:
                    self.data_combo.set(data_files[0])

    # ------------------------------------------------------------------
    # Queue management
    # ------------------------------------------------------------------

    def _add_to_queue(self):
        template = self.template_combo.get()
        data = self.data_combo.get()
        sheet = self.sheet_var.get()
        mode = self.mode_var.get()

        if not template:
            messagebox.showwarning("Chu y", "Vui long chon template")
            return

        proj = self.shared["project_path"].get()
        info = self.logic.get_template_info(proj, template)

        if mode == "e2e":
            page_id = ", ".join(info.get("pages", [])) if info else ""
            url = info.get("start_url", "") if info else ""
        else:
            page_id = info.get("page_id", "") if info else ""
            url = info.get("url", "") if info else ""

        item = {
            "template": template,
            "data": data,
            "sheet": sheet,
            "page_id": page_id,
            "url": url,
            "mode": mode,
        }
        self._queue_items.append(item)
        self._refresh_queue_tree()
        mode_label = "E2E" if mode == "e2e" else "Don trang"
        self._append_log(f"Da them [{mode_label}]: {template} + {data}")

    def _refresh_queue_tree(self):
        for child in self.queue_tree.get_children():
            self.queue_tree.delete(child)
        for i, item in enumerate(self._queue_items, 1):
            mode_label = "E2E" if item.get("mode") == "e2e" else "Don trang"
            self.queue_tree.insert(
                "",
                "end",
                values=(
                    i,
                    mode_label,
                    item["template"],
                    item["data"],
                    item["sheet"],
                    item["page_id"],
                    item["url"],
                ),
            )

    def _move_up(self):
        sel = self.queue_tree.selection()
        if not sel:
            return
        idx = self.queue_tree.index(sel[0])
        if idx > 0:
            self._queue_items[idx], self._queue_items[idx - 1] = (
                self._queue_items[idx - 1],
                self._queue_items[idx],
            )
            self._refresh_queue_tree()
            children = self.queue_tree.get_children()
            self.queue_tree.selection_set(children[idx - 1])

    def _move_down(self):
        sel = self.queue_tree.selection()
        if not sel:
            return
        idx = self.queue_tree.index(sel[0])
        if idx < len(self._queue_items) - 1:
            self._queue_items[idx], self._queue_items[idx + 1] = (
                self._queue_items[idx + 1],
                self._queue_items[idx],
            )
            self._refresh_queue_tree()
            children = self.queue_tree.get_children()
            self.queue_tree.selection_set(children[idx + 1])

    def _remove_selected(self):
        sel = self.queue_tree.selection()
        if not sel:
            return
        idx = self.queue_tree.index(sel[0])
        removed = self._queue_items.pop(idx)
        self._refresh_queue_tree()
        self._append_log(f"Da xoa: {removed['template']}")

    def _clear_queue(self):
        self._queue_items.clear()
        self._refresh_queue_tree()
        self._append_log("Da xoa tat ca hang doi.")

    # ------------------------------------------------------------------
    # Test execution
    # ------------------------------------------------------------------

    def _run_selected(self):
        """Run only the selected queue item."""
        sel = self.queue_tree.selection()
        if not sel:
            messagebox.showwarning("Chu y", "Vui long chon mot muc trong hang doi")
            return
        idx = self.queue_tree.index(sel[0])
        items_to_run = [self._queue_items[idx]]
        self._execute_items(items_to_run)

    def _run_queue(self):
        """Run all items in the queue sequentially."""
        if not self._queue_items:
            messagebox.showwarning("Chu y", "Hang doi trong. Vui long them template truoc.")
            return
        self._execute_items(list(self._queue_items))

    def _execute_items(self, items):
        if self._is_running:
            messagebox.showwarning("Chu y", "Dang chay test, vui long doi.")
            return

        self._is_running = True
        self.run_btn.config(state="disabled")
        self.run_single_btn.config(state="disabled")
        self.log_text.delete(1.0, tk.END)

        total = len(items)
        self._append_log(f"Bat dau chay {total} muc trong hang doi...\n")

        def run():
            for i, item in enumerate(items, 1):
                template = item["template"]
                data = item["data"]
                sheet = item["sheet"]
                page_id = item["page_id"]
                url = item["url"]
                mode = item.get("mode", "single")

                mode_label = "E2E" if mode == "e2e" else "Don trang"
                self.after(
                    0,
                    lambda t=template, n=i, ml=mode_label: self._append_log(
                        f"{'='*50}\n[{n}/{total}] [{ml}] Dang chay: {t}\n{'='*50}"
                    ),
                )

                python_exe = sys.executable
                proj_path = self.shared["project_path"].get()

                # Choose test file and env vars based on mode
                if mode == "e2e":
                    test_file = "tests/test_e2e.py"
                    workflow_path = str(Path(proj_path) / "templates" / template)
                else:
                    test_file = "tests/test_main.py"
                    workflow_path = ""

                cmd = [python_exe, "-m", "pytest", test_file, "-v", "-s"]

                env = os.environ.copy()
                env["PYTHONPATH"] = proj_path
                env["BASE_URL"] = url
                env["SELECTED_TEST_DATA"] = Path(data).name if data else ""
                env["SHEET_NAME"] = sheet
                env["PAGE_ID"] = page_id
                env["BROWSER"] = self.shared["browser_var"].get()
                env.update({"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"})

                if mode == "e2e":
                    env["E2E_WORKFLOW"] = workflow_path

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

                    rc = process.returncode
                    status = "THANH CONG" if rc == 0 else f"THAT BAI (code={rc})"
                    self.after(
                        0,
                        lambda s=status, t=template: self._append_log(
                            f"\nKet qua [{t}]: {s}\n"
                        ),
                    )
                except Exception:
                    err = traceback.format_exc()
                    self.after(
                        0,
                        lambda m=err: self._append_log(f"\nLoi he thong:\n{m}\n"),
                    )

            self.after(
                0,
                lambda: self._append_log(
                    f"\n{'='*50}\nHoan thanh tat ca {total} muc.\n{'='*50}"
                ),
            )
            self.after(0, self._on_run_finished)

        threading.Thread(target=run, daemon=True).start()

    def _on_run_finished(self):
        self._is_running = False
        self.run_btn.config(state="normal")
        self.run_single_btn.config(state="normal")

    # ------------------------------------------------------------------
    # Data import
    # ------------------------------------------------------------------

    def _import_data(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if not file_path:
            return
        url = self.shared["url_path"].get()
        if not url:
            messagebox.showwarning("Chu y", "Vui long chon template truoc de xac dinh site")
            return
        new_name = self.logic.import_test_data(self.shared["project_path"].get(), url, file_path)
        self._append_log(f"Da nhap file du lieu: {new_name}")
        self._refresh_data_list()

    # ------------------------------------------------------------------
    # Refresh helpers
    # ------------------------------------------------------------------

    def _refresh_all(self):
        self.refresh_test_list()
        self._refresh_template_list()
        self._refresh_data_list()

    def refresh_test_list(self):
        p = Path(self.shared["project_path"].get()) / "tests"
        if p.exists():
            tests = [
                str(f.relative_to(self.shared["project_path"].get()))
                for f in p.glob("test_*.py")
            ]

    def _refresh_template_list(self):
        proj = self.shared["project_path"].get()
        mode = self.mode_var.get()
        if mode == "e2e":
            templates = self.logic.get_e2e_workflow_files(proj)
        else:
            templates = self.logic.get_template_files(proj)
        self.template_combo["values"] = templates
        if templates:
            self.template_combo.set(templates[0])
            self._on_template_selected()
        else:
            self.template_combo.set("")

    def _refresh_data_list(self):
        proj = self.shared["project_path"].get()
        data_files = self.logic.get_all_data_files(proj)
        self.data_combo["values"] = data_files
        if data_files:
            self.data_combo.set(data_files[0])

    def update_data_list(self):
        self._refresh_data_list()

    def _append_log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
