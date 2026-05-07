"""AI Tools Panel: Auto-Heal, Test Suggestion, Natural Language Test, AI Config.

Tich hop:
- VectorDB & Semantic Search
- AIConfig cho tuy chinh prompt/model/objectives
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import json
from core.ai_auto_heal import AIAutoHeal
from core.ai_test_suggestion import AITestSuggestion
from core.ai_natural_language import AINaturalLanguage
from core.ai_config import AIConfig
from core.vector_db import VectorDB
from ui.ai_config_panel import AIConfigPanel


class AIToolsPanel(ttk.Frame):
    """Tab for AI-powered testing tools with Vector DB and AI customization."""

    def __init__(self, parent, logic, shared_vars):
        super().__init__(parent, padding=10)
        self.logic = logic
        self.shared = shared_vars

        # Initialize AI Config and Vector DB
        project_path = self.shared["project_path"].get()
        self.ai_config = AIConfig(project_path)
        self.vector_db = VectorDB(project_path)

        # Initialize AI modules with ai_config
        self.auto_heal = AIAutoHeal(ai_config=self.ai_config)
        self.test_suggest = AITestSuggestion(ai_config=self.ai_config)
        self.natural_lang = AINaturalLanguage(ai_config=self.ai_config)

        self._build_api_key_section()
        self._build_notebook()

        # Initialize Vector DB in background
        self._init_vector_db_async()

    def _init_vector_db_async(self):
        """Khoi tao Vector DB trong background thread."""
        project_path = self.shared["project_path"].get()
        if not project_path:
            return

        def init():
            try:
                self.vector_db.initialize(project_path)
                stats = self.vector_db.get_stats()
                total = sum(stats.get("collections", {}).values())
                self.after(0, lambda: self._log_vdb_status(
                    f"[VectorDB] Khoi tao xong: {total} documents indexed."
                ))
            except Exception as e:
                self.after(0, lambda: self._log_vdb_status(
                    f"[VectorDB] Loi khoi tao: {e}"
                ))

        threading.Thread(target=init, daemon=True).start()

    def _log_vdb_status(self, msg):
        """Log VectorDB status (co the hien thi tren UI)."""
        from utils.logger import log
        log.info(msg)
        # Refresh AI Config panel nếu đã có
        if hasattr(self, "ai_config_panel"):
            self.ai_config_panel.set_vector_db(self.vector_db)

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

        # Sub-tab 4: Semantic Search
        self.ss_frame = ttk.Frame(nb, padding=10)
        nb.add(self.ss_frame, text=" Semantic Search ")
        self._build_semantic_search_tab()

        # Sub-tab 5: AI Config (Tuy chinh AI)
        self.ai_config_panel = AIConfigPanel(nb, self.ai_config, self.vector_db)
        nb.add(self.ai_config_panel, text=" Tuy chinh AI ")

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

    # ------------------------------------------------------------------
    # Sub-tab 4: Semantic Search
    # ------------------------------------------------------------------

    def _build_semantic_search_tab(self):
        f = self.ss_frame

        ttk.Label(f, text="Tim kiem ngu nghia trong du lieu du an:",
                  font=("", 10, "bold")).pack(anchor="w", pady=(0, 5))

        # Search controls
        search_row = ttk.Frame(f)
        search_row.pack(fill="x", pady=3)

        ttk.Label(search_row, text="Truy van:").pack(side="left")
        self.ss_query_var = tk.StringVar()
        ttk.Entry(search_row, textvariable=self.ss_query_var, width=45).pack(side="left", padx=5)

        ttk.Label(search_row, text="Collection:").pack(side="left", padx=(10, 0))
        self.ss_collection_var = tk.StringVar(value="locators")
        ttk.Combobox(
            search_row, textvariable=self.ss_collection_var,
            values=["locators", "templates", "test_data", "use_cases"],
            state="readonly", width=12
        ).pack(side="left", padx=5)

        ttk.Button(search_row, text="TIM KIEM", command=self._do_semantic_search).pack(side="left", padx=5)

        # Results
        ttk.Label(f, text="Ket qua:").pack(anchor="w", pady=(5, 2))
        self.ss_result = scrolledtext.ScrolledText(
            f, height=18, font=("Consolas", 9),
            bg="#1e1e1e", fg="#d4d4d4"
        )
        self.ss_result.pack(fill="both", expand=True, pady=3)

    def _do_semantic_search(self):
        query = self.ss_query_var.get().strip()
        if not query:
            messagebox.showwarning("Chu y", "Nhap truy van tim kiem.")
            return

        if not self.vector_db.is_initialized:
            messagebox.showwarning("Chu y", "Vector Database chua khoi tao. "
                                   "Chon project path va doi VectorDB khoi tao.")
            return

        collection = self.ss_collection_var.get()
        self.ss_result.delete("1.0", "end")
        self.ss_result.insert("end", "Dang tim kiem...\n")

        def search():
            try:
                results = self.vector_db.search(
                    query, collection=collection, top_k=15, min_score=0.2
                )
                output_lines = [f"Tim thay {len(results)} ket qua cho: '{query}'\n"]
                output_lines.append(f"Collection: {collection}\n")
                output_lines.append("=" * 60 + "\n")

                for i, r in enumerate(results, 1):
                    meta = r.get("metadata", {})
                    output_lines.append(f"\n--- Ket qua {i} (Score: {r['score']:.4f}) ---")
                    output_lines.append(f"ID: {r['id']}")
                    output_lines.append(f"Text: {r['text'][:200]}")
                    if meta:
                        output_lines.append(f"Metadata: {json.dumps(meta, ensure_ascii=False)}")

                if not results:
                    output_lines.append("\nKhong tim thay ket qua phu hop.")
                    output_lines.append("Thu: thay doi tu khoa, chon collection khac, "
                                       "hoac reindex Vector DB.")

                text = "\n".join(output_lines)
                self.after(0, lambda: self._show_ss_result(text))
            except Exception as e:
                self.after(0, lambda: self._show_ss_result(f"Loi: {e}"))

        threading.Thread(target=search, daemon=True).start()

    def _show_ss_result(self, text):
        self.ss_result.delete("1.0", "end")
        self.ss_result.insert("end", text)

    # --- Actions ---

    def _set_api_key(self):
        key = self.api_key_var.get().strip()
        if not key:
            messagebox.showwarning("Chu y", "Nhap API key.")
            return
        self.auto_heal.configure(key, ai_config=self.ai_config)
        self.test_suggest.configure(key, ai_config=self.ai_config)
        self.natural_lang.configure(key, ai_config=self.ai_config)
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

    # --- Public accessors (for locator_panel AI integration) ---

    def get_ai_config(self):
        return self.ai_config

    def get_vector_db(self):
        return self.vector_db
