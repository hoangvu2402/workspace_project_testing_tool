"""Test Scheduler Panel: schedule automated test runs."""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from core.test_scheduler import TestScheduler, ScheduledTask


class SchedulerPanel(ttk.Frame):
    """Tab for scheduling automated test runs."""

    def __init__(self, parent, logic, shared_vars):
        super().__init__(parent, padding=10)
        self.logic = logic
        self.shared = shared_vars
        self.scheduler = TestScheduler(shared_vars["project_path"].get())
        self.scheduler.set_callback(self._on_task_complete)
        self.scheduler.load_config()

        self._build_add_section()
        self._build_tasks_section()
        self._build_log_section()
        self._refresh_tasks()

    def _build_add_section(self):
        add = ttk.LabelFrame(self, text=" 1. Them lich chay test ", padding=8)
        add.pack(fill="x", pady=(0, 5))

        # Row 0: Name + Schedule type
        ttk.Label(add, text="Ten:").grid(row=0, column=0, sticky="w")
        self.name_var = tk.StringVar(value="Daily Login Test")
        ttk.Entry(add, textvariable=self.name_var, width=25).grid(row=0, column=1, padx=5)

        ttk.Label(add, text="Loai:").grid(row=0, column=2, sticky="w", padx=(10, 0))
        self.schedule_type_var = tk.StringVar(value="interval")
        ttk.Combobox(add, textvariable=self.schedule_type_var, width=10,
                     values=("once", "interval", "daily")).grid(row=0, column=3, padx=5)

        ttk.Label(add, text="Interval (phut):").grid(row=0, column=4, sticky="w")
        self.interval_var = tk.StringVar(value="60")
        ttk.Entry(add, textvariable=self.interval_var, width=8).grid(row=0, column=5, padx=5)

        # Row 1: Template + Data
        ttk.Label(add, text="Template:").grid(row=1, column=0, sticky="w", pady=3)
        self.template_combo = ttk.Combobox(add, width=35)
        self.template_combo.grid(row=1, column=1, padx=5, columnspan=2)

        ttk.Label(add, text="Du lieu:").grid(row=1, column=3, sticky="w")
        self.data_combo = ttk.Combobox(add, width=25)
        self.data_combo.grid(row=1, column=4, padx=5, columnspan=2)

        # Row 2: URL + PageID + Browser
        ttk.Label(add, text="URL:").grid(row=2, column=0, sticky="w", pady=3)
        self.url_var = tk.StringVar()
        ttk.Entry(add, textvariable=self.url_var, width=35).grid(row=2, column=1, padx=5, columnspan=2)

        ttk.Label(add, text="Page ID:").grid(row=2, column=3, sticky="w")
        self.page_id_var = tk.StringVar()
        ttk.Entry(add, textvariable=self.page_id_var, width=15).grid(row=2, column=4, padx=5)

        ttk.Label(add, text="Run at (HH:MM):").grid(row=2, column=5, sticky="w")
        self.run_at_var = tk.StringVar(value="08:00")
        ttk.Entry(add, textvariable=self.run_at_var, width=8).grid(row=2, column=6, padx=5)

        # Row 3: Buttons
        btn = ttk.Frame(add)
        btn.grid(row=3, column=0, columnspan=7, pady=5)
        ttk.Button(btn, text="Them lich", command=self._add_task).pack(side="left", padx=5)
        ttk.Button(btn, text="Lam moi DS", command=self._refresh_dropdowns).pack(side="left", padx=5)

        self._refresh_dropdowns()

    def _build_tasks_section(self):
        tasks = ttk.LabelFrame(self, text=" 2. Danh sach lich ", padding=8)
        tasks.pack(fill="x", pady=5)

        cols = ("STT", "Ten", "Loai", "Template", "Trang thai", "Lan chay cuoi", "Ket qua")
        self.tasks_tree = ttk.Treeview(tasks, columns=cols, show="headings", height=5)
        for c in cols:
            self.tasks_tree.heading(c, text=c)
        self.tasks_tree.column("STT", width=30)
        self.tasks_tree.column("Ten", width=130)
        self.tasks_tree.column("Loai", width=70)
        self.tasks_tree.column("Template", width=150)
        self.tasks_tree.column("Trang thai", width=70)
        self.tasks_tree.column("Lan chay cuoi", width=120)
        self.tasks_tree.column("Ket qua", width=70)
        self.tasks_tree.pack(fill="x")

        btn = ttk.Frame(tasks)
        btn.pack(fill="x", pady=5)
        ttk.Button(btn, text="Xoa", command=self._remove_task).pack(side="left", padx=3)
        ttk.Button(btn, text="Bat/Tat", command=self._toggle_task).pack(side="left", padx=3)
        self.start_btn = ttk.Button(btn, text="BAT DAU SCHEDULER", command=self._start_scheduler)
        self.start_btn.pack(side="right", padx=10)
        self.stop_btn = ttk.Button(btn, text="DUNG SCHEDULER", command=self._stop_scheduler, state="disabled")
        self.stop_btn.pack(side="right", padx=3)

    def _build_log_section(self):
        log = ttk.LabelFrame(self, text=" Log ", padding=5)
        log.pack(fill="both", expand=True, pady=5)

        self.log_text = tk.Text(log, height=6, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True)

    # --- Actions ---

    def _refresh_dropdowns(self):
        proj = self.shared["project_path"].get()
        templates = self.logic.get_template_files(proj) + self.logic.get_e2e_workflow_files(proj)
        self.template_combo["values"] = templates
        data_files = self.logic.get_all_data_files(proj)
        self.data_combo["values"] = data_files

    def _add_task(self):
        interval = 60
        try:
            interval = int(self.interval_var.get())
        except ValueError:
            pass

        task = ScheduledTask(
            name=self.name_var.get(),
            template=self.template_combo.get(),
            data_file=self.data_combo.get(),
            page_id=self.page_id_var.get(),
            url=self.url_var.get(),
            schedule_type=self.schedule_type_var.get(),
            interval_minutes=interval,
            run_at=self.run_at_var.get(),
            browser=self.shared.get("browser_var", tk.StringVar(value="chromium")).get(),
        )
        self.scheduler.add_task(task)
        self._refresh_tasks()
        self._log(f"Da them lich: {task.name}")

    def _remove_task(self):
        sel = self.tasks_tree.selection()
        if sel:
            idx = self.tasks_tree.index(sel[0])
            self.scheduler.remove_task(idx)
            self._refresh_tasks()

    def _toggle_task(self):
        sel = self.tasks_tree.selection()
        if sel:
            idx = self.tasks_tree.index(sel[0])
            self.scheduler.toggle_task(idx)
            self._refresh_tasks()

    def _start_scheduler(self):
        self.scheduler.project_path = self.shared["project_path"].get()
        self.scheduler.start()
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self._log("Scheduler da bat dau chay.")

    def _stop_scheduler(self):
        self.scheduler.stop()
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self._log("Scheduler da dung.")

    def _refresh_tasks(self):
        for child in self.tasks_tree.get_children():
            self.tasks_tree.delete(child)
        for i, t in enumerate(self.scheduler.tasks, 1):
            status = "Bat" if t.enabled else "Tat"
            last_run = t.last_run.strftime("%Y-%m-%d %H:%M") if t.last_run else "-"
            self.tasks_tree.insert("", "end", values=(
                i, t.name, t.schedule_type, t.template, status, last_run, t.last_status or "-"
            ))

    def _on_task_complete(self, task, status, output):
        self.after(0, lambda: self._log(f"[{task.name}] {status}\n{output[:500]}"))
        self.after(0, self._refresh_tasks)

    def _log(self, text):
        self.log_text.insert("end", text + "\n\n")
        self.log_text.see("end")
