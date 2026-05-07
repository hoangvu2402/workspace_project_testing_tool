"""API Testing Panel: REST/GraphQL testing with assertions UI."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import json
from pathlib import Path
from core.api_tester import APITester, APITestCase


class APITestingPanel(ttk.Frame):
    """Tab for API testing with requests, assertions, and results."""

    def __init__(self, parent, logic, shared_vars):
        super().__init__(parent, padding=10)
        self.logic = logic
        self.shared = shared_vars
        self.tester = APITester()
        self._test_cases = []

        self._build_request_section()
        self._build_assertions_section()
        self._build_collection_section()
        self._build_results_section()

    def _build_request_section(self):
        req = ttk.LabelFrame(self, text=" 1. Request ", padding=8)
        req.pack(fill="x", pady=(0, 5))

        # Row 0: Method + URL
        ttk.Label(req, text="Method:").grid(row=0, column=0, sticky="w")
        self.method_var = tk.StringVar(value="GET")
        method_cb = ttk.Combobox(req, textvariable=self.method_var, width=8,
                                 values=("GET", "POST", "PUT", "PATCH", "DELETE"))
        method_cb.grid(row=0, column=1, padx=5)

        ttk.Label(req, text="URL:").grid(row=0, column=2, sticky="w")
        self.url_var = tk.StringVar()
        ttk.Entry(req, textvariable=self.url_var, width=50).grid(row=0, column=3, padx=5, columnspan=2)

        # Row 1: Name
        ttk.Label(req, text="Ten test:").grid(row=1, column=0, sticky="w", pady=3)
        self.name_var = tk.StringVar(value="Test 1")
        ttk.Entry(req, textvariable=self.name_var, width=30).grid(row=1, column=1, padx=5, columnspan=2)

        # Row 2: Headers
        ttk.Label(req, text="Headers (JSON):").grid(row=2, column=0, sticky="nw", pady=3)
        self.headers_text = tk.Text(req, height=2, width=60, font=("Consolas", 9))
        self.headers_text.grid(row=2, column=1, padx=5, columnspan=4)
        self.headers_text.insert("1.0", '{"Content-Type": "application/json"}')

        # Row 3: Body
        ttk.Label(req, text="Body:").grid(row=3, column=0, sticky="nw", pady=3)
        self.body_text = tk.Text(req, height=3, width=60, font=("Consolas", 9))
        self.body_text.grid(row=3, column=1, padx=5, columnspan=4)

        # Row 4: Buttons
        btn_frame = ttk.Frame(req)
        btn_frame.grid(row=4, column=0, columnspan=5, pady=5)
        ttk.Button(btn_frame, text="GUI REQUEST", command=self._send_request).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Them vao Collection", command=self._add_to_collection).pack(side="left", padx=5)

    def _build_assertions_section(self):
        asrt = ttk.LabelFrame(self, text=" 2. Assertions ", padding=8)
        asrt.pack(fill="x", pady=5)

        # Assertion type
        row = ttk.Frame(asrt)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text="Loai:").pack(side="left")
        self.assert_type_var = tk.StringVar(value="status_code")
        ttk.Combobox(row, textvariable=self.assert_type_var, width=20,
                     values=("status_code", "body_contains", "body_json_path",
                             "header", "response_time")).pack(side="left", padx=5)

        ttk.Label(row, text="Path/Key:").pack(side="left", padx=(10, 0))
        self.assert_path_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.assert_path_var, width=20).pack(side="left", padx=5)

        ttk.Label(row, text="Expected:").pack(side="left")
        self.assert_expected_var = tk.StringVar(value="200")
        ttk.Entry(row, textvariable=self.assert_expected_var, width=15).pack(side="left", padx=5)

        ttk.Button(row, text="Them", command=self._add_assertion).pack(side="left", padx=5)

        # Assertions list
        self.assertions_tree = ttk.Treeview(asrt, columns=("Type", "Path", "Expected"), show="headings", height=3)
        self.assertions_tree.heading("Type", text="Loai")
        self.assertions_tree.heading("Path", text="Path")
        self.assertions_tree.heading("Expected", text="Ky vong")
        self.assertions_tree.column("Type", width=120)
        self.assertions_tree.column("Path", width=150)
        self.assertions_tree.column("Expected", width=150)
        self.assertions_tree.pack(fill="x", pady=3)

        self._current_assertions = []

    def _build_collection_section(self):
        col = ttk.LabelFrame(self, text=" 3. Collection ", padding=8)
        col.pack(fill="x", pady=5)

        self.collection_tree = ttk.Treeview(
            col, columns=("STT", "Name", "Method", "URL", "Assertions"),
            show="headings", height=4
        )
        self.collection_tree.heading("STT", text="#")
        self.collection_tree.heading("Name", text="Ten")
        self.collection_tree.heading("Method", text="Method")
        self.collection_tree.heading("URL", text="URL")
        self.collection_tree.heading("Assertions", text="Assertions")
        self.collection_tree.column("STT", width=30)
        self.collection_tree.column("Name", width=120)
        self.collection_tree.column("Method", width=60)
        self.collection_tree.column("URL", width=250)
        self.collection_tree.column("Assertions", width=80)
        self.collection_tree.pack(fill="x")

        btn = ttk.Frame(col)
        btn.pack(fill="x", pady=5)
        ttk.Button(btn, text="Xoa muc chon", command=self._remove_from_collection).pack(side="left", padx=3)
        ttk.Button(btn, text="Luu Collection", command=self._save_collection).pack(side="left", padx=3)
        ttk.Button(btn, text="Tai Collection", command=self._load_collection).pack(side="left", padx=3)
        ttk.Button(btn, text="CHAY TAT CA", command=self._run_collection).pack(side="right", padx=10)

    def _build_results_section(self):
        res = ttk.LabelFrame(self, text=" 4. Ket qua ", padding=5)
        res.pack(fill="both", expand=True, pady=5)

        self.result_text = tk.Text(res, height=8, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 9))
        self.result_text.pack(fill="both", expand=True)

    # --- Actions ---

    def _add_assertion(self):
        a = {
            "type": self.assert_type_var.get(),
            "path": self.assert_path_var.get(),
            "expected": self.assert_expected_var.get(),
        }
        self._current_assertions.append(a)
        self.assertions_tree.insert("", "end", values=(a["type"], a["path"], a["expected"]))

    def _build_test_case(self) -> APITestCase:
        headers = {}
        try:
            h_text = self.headers_text.get("1.0", "end").strip()
            if h_text:
                headers = json.loads(h_text)
        except json.JSONDecodeError:
            pass

        return APITestCase(
            name=self.name_var.get(),
            method=self.method_var.get(),
            url=self.url_var.get(),
            headers=headers,
            body=self.body_text.get("1.0", "end").strip(),
            assertions=list(self._current_assertions),
        )

    def _send_request(self):
        tc = self._build_test_case()
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("end", "Dang gui request...\n")

        def run():
            result = self.tester.run_test(tc)
            output = f"Status: {result.status_code} | Time: {result.response_time_ms}ms | {result.status.upper()}\n"
            output += f"\nResponse:\n{result.response_body[:2000]}\n"
            if result.assertions_results:
                output += "\nAssertions:\n"
                for a in result.assertions_results:
                    icon = "PASS" if a["passed"] else "FAIL"
                    output += f"  [{icon}] {a['type']}: expected={a['expected']}, actual={a.get('actual','')}\n"
            self.after(0, lambda: self._show_result(output))

        threading.Thread(target=run, daemon=True).start()

    def _show_result(self, text):
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("end", text)

    def _add_to_collection(self):
        tc = self._build_test_case()
        self._test_cases.append(tc)
        self._refresh_collection()
        self._current_assertions = []
        for child in self.assertions_tree.get_children():
            self.assertions_tree.delete(child)

    def _remove_from_collection(self):
        sel = self.collection_tree.selection()
        if sel:
            idx = self.collection_tree.index(sel[0])
            self._test_cases.pop(idx)
            self._refresh_collection()

    def _refresh_collection(self):
        for child in self.collection_tree.get_children():
            self.collection_tree.delete(child)
        for i, tc in enumerate(self._test_cases, 1):
            self.collection_tree.insert("", "end", values=(
                i, tc.name, tc.method, tc.url, len(tc.assertions)
            ))

    def _save_collection(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("JSON", "*.json")],
            initialfile="api_collection.json"
        )
        if path:
            self.tester.save_collection(path, self._test_cases)
            messagebox.showinfo("Luu", f"Da luu {len(self._test_cases)} test cases.")

    def _load_collection(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if path:
            self._test_cases = self.tester.load_collection(path)
            self._refresh_collection()

    def _run_collection(self):
        if not self._test_cases:
            messagebox.showwarning("Chu y", "Collection trong.")
            return
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("end", f"Dang chay {len(self._test_cases)} test cases...\n\n")

        def run():
            results = self.tester.run_collection(self._test_cases)
            output = ""
            passed = 0
            for r in results:
                status = "PASS" if r.status == "passed" else "FAIL"
                if r.status == "passed":
                    passed += 1
                output += f"[{status}] {r.test_name} | {r.status_code} | {r.response_time_ms}ms\n"
                for a in r.assertions_results:
                    icon = "  PASS" if a["passed"] else "  FAIL"
                    output += f"  [{icon}] {a['type']}: {a['expected']}\n"
                output += "\n"
            output += f"\n{'='*40}\nKet qua: {passed}/{len(results)} PASSED\n"
            self.after(0, lambda: self._show_result(output))

        threading.Thread(target=run, daemon=True).start()
