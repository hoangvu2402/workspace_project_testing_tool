"""Test History Dashboard Panel: display test result trends."""

import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from pathlib import Path
from core.test_history import TestHistory
from core.report_generator import ReportGenerator


class HistoryPanel(ttk.Frame):
    """Tab for viewing test history and trends."""

    def __init__(self, parent, logic, shared_vars):
        super().__init__(parent, padding=10)
        self.logic = logic
        self.shared = shared_vars
        proj = shared_vars["project_path"].get()
        self.history = TestHistory(proj)
        self.history.load()
        self.report_gen = ReportGenerator(str(Path(proj) / "reports"))

        self._build_summary_section()
        self._build_trend_section()
        self._build_failing_section()
        self._build_actions_section()
        self._refresh_all()

    def _build_summary_section(self):
        s = ttk.LabelFrame(self, text=" Tong quan ", padding=8)
        s.pack(fill="x", pady=(0, 5))

        self.summary_labels = {}
        labels = [
            ("total_runs", "Tong so lan chay:"),
            ("avg_pass_rate", "Ty le pass TB:"),
            ("total_tests_executed", "Tong test da chay:"),
            ("total_passed", "Tong pass:"),
            ("total_failed", "Tong fail:"),
            ("last_run", "Lan chay cuoi:"),
        ]

        for i, (key, text) in enumerate(labels):
            ttk.Label(s, text=text).grid(row=i // 3, column=(i % 3) * 2, sticky="w", padx=5)
            lbl = ttk.Label(s, text="-", font=("Segoe UI", 10, "bold"))
            lbl.grid(row=i // 3, column=(i % 3) * 2 + 1, sticky="w", padx=(0, 20))
            self.summary_labels[key] = lbl

    def _build_trend_section(self):
        t = ttk.LabelFrame(self, text=" Lich su chay test (gan nhat) ", padding=8)
        t.pack(fill="x", pady=5)

        cols = ("Thoi gian", "Suite", "Pass", "Fail", "Ty le", "Thoi gian chay")
        self.trend_tree = ttk.Treeview(t, columns=cols, show="headings", height=8)
        for c in cols:
            self.trend_tree.heading(c, text=c)
        self.trend_tree.column("Thoi gian", width=130)
        self.trend_tree.column("Suite", width=150)
        self.trend_tree.column("Pass", width=60)
        self.trend_tree.column("Fail", width=60)
        self.trend_tree.column("Ty le", width=70)
        self.trend_tree.column("Thoi gian chay", width=90)

        scroll = ttk.Scrollbar(t, orient="vertical", command=self.trend_tree.yview)
        self.trend_tree.configure(yscrollcommand=scroll.set)
        self.trend_tree.pack(side="left", fill="x", expand=True)
        scroll.pack(side="right", fill="y")

    def _build_failing_section(self):
        f = ttk.LabelFrame(self, text=" Test case hay fail ", padding=8)
        f.pack(fill="x", pady=5)

        cols = ("Test name", "So lan fail")
        self.fail_tree = ttk.Treeview(f, columns=cols, show="headings", height=4)
        self.fail_tree.heading("Test name", text="Ten test")
        self.fail_tree.heading("So lan fail", text="So lan fail")
        self.fail_tree.column("Test name", width=400)
        self.fail_tree.column("So lan fail", width=100)
        self.fail_tree.pack(fill="x")

    def _build_actions_section(self):
        a = ttk.Frame(self)
        a.pack(fill="x", pady=5)
        ttk.Button(a, text="Lam moi", command=self._refresh_all).pack(side="left", padx=5)
        ttk.Button(a, text="Tao bao cao HTML", command=self._generate_report).pack(side="left", padx=5)
        ttk.Button(a, text="Xoa lich su", command=self._clear_history).pack(side="left", padx=5)

    def _refresh_all(self):
        self.history.load()

        # Summary
        summary = self.history.get_summary()
        for key, lbl in self.summary_labels.items():
            val = summary.get(key, "-")
            if key == "avg_pass_rate":
                val = f"{val}%"
            lbl.config(text=str(val))

        # Trend
        for child in self.trend_tree.get_children():
            self.trend_tree.delete(child)
        for entry in reversed(self.history.get_trend(20)):
            self.trend_tree.insert("", "end", values=(
                entry["timestamp"][:16],
                entry["suite_name"],
                entry["passed"],
                entry["failed"],
                f"{entry['pass_rate']}%",
                f"{entry['duration_ms']}ms",
            ))

        # Failing tests
        for child in self.fail_tree.get_children():
            self.fail_tree.delete(child)
        for item in self.history.get_failing_tests():
            self.fail_tree.insert("", "end", values=(item["name"], item["fail_count"]))

    def _generate_report(self):
        trend = self.history.get_trend(20)
        if not trend:
            messagebox.showinfo("Thong bao", "Chua co du lieu de tao bao cao.")
            return

        html = self.history.generate_trend_html()
        proj = self.shared["project_path"].get()
        report_dir = Path(proj) / "reports" / "html"
        report_dir.mkdir(parents=True, exist_ok=True)
        filepath = report_dir / "history_report.html"

        full_html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<title>Test History</title>
<style>
body {{ font-family: sans-serif; margin: 20px; }}
.history-table {{ width: 100%; border-collapse: collapse; }}
.history-table th {{ background: #34495e; color: white; padding: 10px; }}
.history-table td {{ padding: 8px; border-bottom: 1px solid #eee; }}
.passed {{ background: #eafaf1; }}
.failed {{ background: #fdedec; }}
.warning {{ background: #fef9e7; }}
</style></head><body>
<h1>Test History Dashboard</h1>
{html}
</body></html>"""

        filepath.write_text(full_html, encoding="utf-8")
        webbrowser.open(str(filepath))
        messagebox.showinfo("Bao cao", f"Da tao: {filepath}")

    def _clear_history(self):
        if messagebox.askyesno("Xac nhan", "Xoa toan bo lich su?"):
            self.history.entries.clear()
            self.history._save()
            self._refresh_all()
