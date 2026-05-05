"""AI Tools Panel: Auto-Heal, Test Suggestion, Natural Language Test."""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import json
from core.ai_auto_heal import AIAutoHeal
from core.ai_test_suggestion import AITestSuggestion
from core.ai_natural_language import AINaturalLanguage


class AIToolsPanel(ttk.Frame):
    """Tab for AI-powered testing tools."""

    def __init__(self, parent, logic, shared_vars):
        super().__init__(parent, padding=10)
        self.logic = logic
        self.shared = shared_vars

        self.auto_heal = AIAutoHeal()
        self.test_suggest = AITestSuggestion()
        self.natural_lang = AINaturalLanguage()

        self._build_api_key_section()
        self._build_notebook()

    def _build_api_key_section(self):
        key_frame = ttk.LabelFrame(self, text=" API Key ", padding=5)
        key_frame.pack(fill="x", pady=(0, 5))

        ttk.Label(key_frame, text="Gemini API Key:").pack(side="left")
        self.api_key_var = tk.StringVar()
        ttk.Entry(key_frame, textvariable=self.api_key_var, width=45, show="*").pack(side="left", padx=5)
        ttk.Button(key_frame, text="Cau hinh", command=self._set_api_key).pack(side="left", padx=5)

    def _build_notebook(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, pady=5)

        # Sub-tab 1: Natural Language Test
        self.nl_frame = ttk.Frame(nb, padding=10)
        nb.add(self.nl_frame, text=" Viet test tu nhien ")
        self._build_natural_lang_tab()

        # Sub-tab 2: Test Suggestion
        self.ts_frame = ttk.Frame(nb, padding=10)
        nb.add(self.ts_frame, text=" Goi y test tu Git ")

        self._build_test_suggest_tab()

        # Sub-tab 3: Auto-Heal Log
        self.ah_frame = ttk.Frame(nb, padding=10)
        nb.add(self.ah_frame, text=" Auto-Heal Log ")
        self._build_auto_heal_tab()

    def _build_natural_lang_tab(self):
        f = self.nl_frame

        ttk.Label(f, text="Mo ta test bang tieng Viet/Anh:").pack(anchor="w")
        self.nl_text = scrolledtext.ScrolledText(f, height=6, font=("Consolas", 10))
        self.nl_text.pack(fill="x", pady=3)
        self.nl_text.insert("1.0",
            "1. Mo trang dang nhap\n"
            "2. Nhap username 'standard_user'\n"
            "3. Nhap password 'secret_sauce'\n"
            "4. Click nut Login\n"
            "5. Kiem tra trang inventory hien thi"
        )

        row = ttk.Frame(f)
        row.pack(fill="x", pady=3)
        ttk.Label(row, text="URL:").pack(side="left")
        self.nl_url_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.nl_url_var, width=40).pack(side="left", padx=5)
        ttk.Label(row, text="Page ID:").pack(side="left")
        self.nl_page_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.nl_page_var, width=15).pack(side="left", padx=5)

        btn = ttk.Frame(f)
        btn.pack(fill="x", pady=3)
        ttk.Button(btn, text="CHUYEN DOI BANG AI", command=self._convert_natural_lang).pack(side="left", padx=5)
        ttk.Button(btn, text="Kiem tra chat luong", command=self._check_quality).pack(side="left", padx=5)

        ttk.Label(f, text="Ket qua:").pack(anchor="w", pady=(5, 0))
        self.nl_result = scrolledtext.ScrolledText(f, height=12, font=("Consolas", 9),
                                                    bg="#1e1e1e", fg="#d4d4d4")
        self.nl_result.pack(fill="both", expand=True)

    def _build_test_suggest_tab(self):
        f = self.ts_frame

        ttk.Label(f, text="Phan tich git diff va goi y test can chay lai:").pack(anchor="w")

        row = ttk.Frame(f)
        row.pack(fill="x", pady=5)
        ttk.Label(row, text="Base branch:").pack(side="left")
        self.base_branch_var = tk.StringVar(value="main")
        ttk.Entry(row, textvariable=self.base_branch_var, width=20).pack(side="left", padx=5)
        ttk.Button(row, text="PHAN TICH (Rule-based)", command=self._analyze_changes).pack(side="left", padx=5)
        ttk.Button(row, text="PHAN TICH (AI)", command=self._suggest_ai).pack(side="left", padx=5)

        self.ts_result = scrolledtext.ScrolledText(f, height=18, font=("Consolas", 9),
                                                    bg="#1e1e1e", fg="#d4d4d4")
        self.ts_result.pack(fill="both", expand=True, pady=5)

    def _build_auto_heal_tab(self):
        f = self.ah_frame

        ttk.Label(f, text="Nhat ky tu sua locator (Auto-Heal):").pack(anchor="w")
        ttk.Label(f, text="Auto-Heal tu dong chay khi test gap loi 'element not found'.",
                  foreground="gray").pack(anchor="w")

        self.ah_tree = ttk.Treeview(
            f, columns=("Time", "Step", "Old", "New", "Method"),
            show="headings", height=10
        )
        self.ah_tree.heading("Time", text="Thoi gian")
        self.ah_tree.heading("Step", text="Step ID")
        self.ah_tree.heading("Old", text="Selector cu")
        self.ah_tree.heading("New", text="Selector moi")
        self.ah_tree.heading("Method", text="Phuong phap")
        self.ah_tree.column("Time", width=130)
        self.ah_tree.column("Step", width=100)
        self.ah_tree.column("Old", width=170)
        self.ah_tree.column("New", width=170)
        self.ah_tree.column("Method", width=80)
        self.ah_tree.pack(fill="both", expand=True, pady=5)

        ttk.Button(f, text="Lam moi", command=self._refresh_heal_log).pack(anchor="w")

    # --- Actions ---

    def _set_api_key(self):
        key = self.api_key_var.get().strip()
        if not key:
            messagebox.showwarning("Chu y", "Nhap API key.")
            return
        self.auto_heal.configure(key)
        self.test_suggest.configure(key)
        self.natural_lang.configure(key)
        messagebox.showinfo("OK", "Da cau hinh API key cho AI Tools.")

    def _convert_natural_lang(self):
        text = self.nl_text.get("1.0", "end").strip()
        if not text:
            return

        self.nl_result.delete("1.0", "end")
        self.nl_result.insert("end", "Dang chuyen doi...\n")

        def run():
            try:
                result = self.natural_lang.convert_to_template(
                    text, self.nl_url_var.get(), self.nl_page_var.get()
                )
                output = json.dumps(result, indent=2, ensure_ascii=False)
                self.after(0, lambda: self._show_nl_result(output))
            except Exception as e:
                self.after(0, lambda: self._show_nl_result(f"Loi: {e}"))

        threading.Thread(target=run, daemon=True).start()

    def _check_quality(self):
        text = self.nl_text.get("1.0", "end").strip()
        if not text:
            return

        self.nl_result.delete("1.0", "end")
        self.nl_result.insert("end", "Dang kiem tra chat luong...\n")

        def run():
            try:
                result = self.natural_lang.suggest_improvements(text)
                output = json.dumps(result, indent=2, ensure_ascii=False)
                self.after(0, lambda: self._show_nl_result(output))
            except Exception as e:
                self.after(0, lambda: self._show_nl_result(f"Loi: {e}"))

        threading.Thread(target=run, daemon=True).start()

    def _show_nl_result(self, text):
        self.nl_result.delete("1.0", "end")
        self.nl_result.insert("end", text)

    def _analyze_changes(self):
        proj = self.shared["project_path"].get()
        self.ts_result.delete("1.0", "end")
        self.ts_result.insert("end", "Dang phan tich...\n")

        def run():
            try:
                diff = self.test_suggest.get_git_diff(proj, self.base_branch_var.get())
                result = self.test_suggest.analyze_changes(proj, diff)
                output = json.dumps(result, indent=2, ensure_ascii=False)
                self.after(0, lambda: self._show_ts_result(
                    f"Git diff:\n{diff[:1000]}\n\nPhan tich:\n{output}"
                ))
            except Exception as e:
                self.after(0, lambda: self._show_ts_result(f"Loi: {e}"))

        threading.Thread(target=run, daemon=True).start()

    def _suggest_ai(self):
        proj = self.shared["project_path"].get()
        self.ts_result.delete("1.0", "end")
        self.ts_result.insert("end", "Dang phan tich bang AI...\n")

        def run():
            try:
                diff = self.test_suggest.get_git_diff(proj, self.base_branch_var.get())
                result = self.test_suggest.suggest_with_ai(proj, diff)
                output = json.dumps(result, indent=2, ensure_ascii=False)
                self.after(0, lambda: self._show_ts_result(output))
            except Exception as e:
                self.after(0, lambda: self._show_ts_result(f"Loi: {e}"))

        threading.Thread(target=run, daemon=True).start()

    def _show_ts_result(self, text):
        self.ts_result.delete("1.0", "end")
        self.ts_result.insert("end", text)

    def _refresh_heal_log(self):
        for child in self.ah_tree.get_children():
            self.ah_tree.delete(child)
        for entry in self.auto_heal.get_heal_report():
            self.ah_tree.insert("", "end", values=(
                entry.get("timestamp", ""),
                entry.get("step_id", ""),
                entry.get("old_selector", ""),
                entry.get("new_selector", ""),
                entry.get("method", ""),
            ))
