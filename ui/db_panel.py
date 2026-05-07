"""Database Verification Panel: connect DB and verify data."""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
from core.db_verifier import DBVerifier


class DBVerificationPanel(ttk.Frame):
    """Tab for database verification after test execution."""

    def __init__(self, parent, logic, shared_vars):
        super().__init__(parent, padding=10)
        self.logic = logic
        self.shared = shared_vars
        self.verifier = DBVerifier()

        self._build_connection_section()
        self._build_query_section()
        self._build_verification_section()
        self._build_results_section()

    def _build_connection_section(self):
        conn = ttk.LabelFrame(self, text=" 1. Ket noi Database ", padding=8)
        conn.pack(fill="x", pady=(0, 5))

        # Row 0: DB type
        ttk.Label(conn, text="Loai DB:").grid(row=0, column=0, sticky="w")
        self.db_type_var = tk.StringVar(value="sqlite")
        ttk.Combobox(conn, textvariable=self.db_type_var, width=15,
                     values=("sqlite", "mysql", "postgresql", "mssql")).grid(row=0, column=1, padx=5)

        ttk.Label(conn, text="Host:").grid(row=0, column=2, sticky="w", padx=(10, 0))
        self.host_var = tk.StringVar(value="localhost")
        ttk.Entry(conn, textvariable=self.host_var, width=20).grid(row=0, column=3, padx=5)

        ttk.Label(conn, text="Port:").grid(row=0, column=4, sticky="w")
        self.port_var = tk.StringVar(value="5432")
        ttk.Entry(conn, textvariable=self.port_var, width=8).grid(row=0, column=5, padx=5)

        # Row 1: DB, user, pass
        ttk.Label(conn, text="Database:").grid(row=1, column=0, sticky="w", pady=3)
        self.db_var = tk.StringVar()
        ttk.Entry(conn, textvariable=self.db_var, width=20).grid(row=1, column=1, padx=5)

        ttk.Label(conn, text="User:").grid(row=1, column=2, sticky="w", padx=(10, 0))
        self.user_var = tk.StringVar()
        ttk.Entry(conn, textvariable=self.user_var, width=15).grid(row=1, column=3, padx=5)

        ttk.Label(conn, text="Pass:").grid(row=1, column=4, sticky="w")
        self.pass_var = tk.StringVar()
        ttk.Entry(conn, textvariable=self.pass_var, width=15, show="*").grid(row=1, column=5, padx=5)

        # Row 2: Connect/Disconnect
        btn = ttk.Frame(conn)
        btn.grid(row=2, column=0, columnspan=6, pady=5)
        ttk.Button(btn, text="Ket noi", command=self._connect).pack(side="left", padx=5)
        ttk.Button(btn, text="Ngat ket noi", command=self._disconnect).pack(side="left", padx=5)
        self.status_label = ttk.Label(btn, text="Chua ket noi", foreground="gray")
        self.status_label.pack(side="left", padx=10)

    def _build_query_section(self):
        q = ttk.LabelFrame(self, text=" 2. Truy van ", padding=8)
        q.pack(fill="x", pady=5)

        ttk.Label(q, text="SQL Query:").pack(anchor="w")
        self.query_text = tk.Text(q, height=3, font=("Consolas", 10))
        self.query_text.pack(fill="x", pady=3)
        self.query_text.insert("1.0", "SELECT * FROM users LIMIT 10")

        btn = ttk.Frame(q)
        btn.pack(fill="x")
        ttk.Button(btn, text="Thuc thi", command=self._execute_query).pack(side="left", padx=5)

    def _build_verification_section(self):
        v = ttk.LabelFrame(self, text=" 3. Xac minh du lieu ", padding=8)
        v.pack(fill="x", pady=5)

        # Verification type
        row1 = ttk.Frame(v)
        row1.pack(fill="x", pady=2)
        ttk.Label(row1, text="Loai:").pack(side="left")
        self.verify_type_var = tk.StringVar(value="record_exists")
        ttk.Combobox(row1, textvariable=self.verify_type_var, width=15,
                     values=("record_exists", "field_value", "row_count")).pack(side="left", padx=5)

        ttk.Label(row1, text="Table:").pack(side="left", padx=(10, 0))
        self.table_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.table_var, width=20).pack(side="left", padx=5)

        # Conditions
        row2 = ttk.Frame(v)
        row2.pack(fill="x", pady=2)
        ttk.Label(row2, text="Conditions (JSON):").pack(side="left")
        self.conditions_var = tk.StringVar(value='{"id": 1}')
        ttk.Entry(row2, textvariable=self.conditions_var, width=40).pack(side="left", padx=5)

        ttk.Label(row2, text="Field:").pack(side="left")
        self.field_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.field_var, width=15).pack(side="left", padx=5)

        ttk.Label(row2, text="Expected:").pack(side="left")
        self.expected_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.expected_var, width=15).pack(side="left", padx=5)

        ttk.Button(v, text="Xac minh", command=self._verify).pack(anchor="w", pady=5)

    def _build_results_section(self):
        r = ttk.LabelFrame(self, text=" Ket qua ", padding=5)
        r.pack(fill="both", expand=True, pady=5)

        self.result_text = tk.Text(r, height=8, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 9))
        self.result_text.pack(fill="both", expand=True)

    # --- Actions ---

    def _connect(self):
        port = 0
        try:
            port = int(self.port_var.get())
        except ValueError:
            pass

        success = self.verifier.connect(
            db_type=self.db_type_var.get(),
            host=self.host_var.get(),
            port=port,
            database=self.db_var.get(),
            username=self.user_var.get(),
            password=self.pass_var.get(),
        )
        if success:
            self.status_label.config(text="Da ket noi", foreground="green")
            self._log("Ket noi thanh cong!")
        else:
            self.status_label.config(text="Loi ket noi", foreground="red")
            self._log("Loi ket noi. Kiem tra thong tin va thu lai.")

    def _disconnect(self):
        self.verifier.disconnect()
        self.status_label.config(text="Da ngat ket noi", foreground="gray")
        self._log("Da ngat ket noi database.")

    def _execute_query(self):
        query = self.query_text.get("1.0", "end").strip()
        if not query:
            return

        def run():
            results = self.verifier.execute_query(query)
            if results:
                output = json.dumps(results, indent=2, ensure_ascii=False, default=str)
                self.after(0, lambda: self._log(f"Ket qua ({len(results)} dong):\n{output}"))
            else:
                self.after(0, lambda: self._log("Khong co ket qua hoac loi truy van."))

        threading.Thread(target=run, daemon=True).start()

    def _verify(self):
        verify_type = self.verify_type_var.get()
        table = self.table_var.get()
        if not table:
            messagebox.showwarning("Chu y", "Nhap ten table.")
            return

        try:
            conditions = json.loads(self.conditions_var.get())
        except json.JSONDecodeError:
            conditions = {}

        def run():
            if verify_type == "record_exists":
                result = self.verifier.verify_record_exists(table, conditions)
                msg = f"Record exists in {table}: {'CO' if result else 'KHONG'}"
            elif verify_type == "field_value":
                result = self.verifier.verify_field_value(
                    table, conditions, self.field_var.get(), self.expected_var.get()
                )
                msg = f"Field {self.field_var.get()} = {self.expected_var.get()}: {'KHOP' if result else 'KHONG KHOP'}"
            elif verify_type == "row_count":
                expected = int(self.expected_var.get()) if self.expected_var.get().isdigit() else 0
                result = self.verifier.verify_row_count(table, conditions, expected)
                msg = f"Row count = {expected}: {'KHOP' if result else 'KHONG KHOP'}"
            else:
                msg = "Loai xac minh khong hop le."
            self.after(0, lambda: self._log(msg))

        threading.Thread(target=run, daemon=True).start()

    def _log(self, text):
        self.result_text.insert("end", text + "\n\n")
        self.result_text.see("end")
