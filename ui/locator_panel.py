import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
from logic_manager import AutomationLogic


class LocatorPanel(ttk.Frame):
    """Panel for scanning locators, displaying and editing locators & templates."""

    def __init__(self, parent, logic: AutomationLogic, shared_vars: dict):
        super().__init__(parent, padding=10)
        self.logic = logic
        self.shared = shared_vars
        self._build_config_section()
        self._build_control_buttons()
        self._build_elements_tree()
        self._build_log_section()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_config_section(self):
        cfg = ttk.LabelFrame(self, text=" 1. Cau hinh Du an & Trang Web ", padding=10)
        cfg.pack(fill="x", pady=(0, 5))

        ttk.Label(cfg, text="Thu muc du an:").grid(row=0, column=0, sticky="w")
        self.project_entry = ttk.Entry(cfg, textvariable=self.shared["project_path"], width=70)
        self.project_entry.grid(row=0, column=1, padx=5)
        ttk.Button(cfg, text="Duyet...", command=self._browse_project).grid(row=0, column=2)

        ttk.Label(cfg, text="URL muc tieu:").grid(row=1, column=0, sticky="w", pady=5)
        self.url_entry = ttk.Entry(cfg, textvariable=self.shared["url_path"], width=70)
        self.url_entry.grid(row=1, column=1, padx=5)

        ttk.Label(cfg, text="Page ID (VD: login):").grid(row=2, column=0, sticky="w")
        ttk.Entry(cfg, textvariable=self.shared["page_id_var"], width=30).grid(row=2, column=1, sticky="w", padx=5)

        ttk.Label(cfg, text="Trinh duyet:").grid(row=2, column=2, sticky="w", padx=10)
        browser_combo = ttk.Combobox(cfg, textvariable=self.shared["browser_var"], width=15)
        browser_combo["values"] = ("chromium", "firefox", "webkit")
        browser_combo.grid(row=2, column=3, sticky="w", padx=5)

    def _build_control_buttons(self):
        ctl = ttk.Frame(self, padding=5)
        ctl.pack(fill="x")

        ttk.Button(ctl, text="Quet trang web", command=self._start_scan).pack(side="left", padx=5)
        ttk.Button(ctl, text="Hien Locator", command=self._show_locators).pack(side="left", padx=5)
        ttk.Button(ctl, text="Hien Template", command=self._show_template).pack(side="left", padx=5)

    def _build_elements_tree(self):
        frame = ttk.LabelFrame(
            self,
            text=" 2. Cac phan tu tim thay (Chon de tao kich ban) ",
            padding=10,
        )
        frame.pack(fill="both", expand=True, pady=5)

        columns = ("Type", "Name", "Selector", "Action", "DataKey")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")
        self.tree.heading("Type", text="Loai")
        self.tree.heading("Name", text="Ten / ID")
        self.tree.heading("Selector", text="Selector (CSS/ID)")
        self.tree.heading("Action", text="Hanh dong")
        self.tree.heading("DataKey", text="Khoa du lieu (Excel)")

        self.tree.column("Type", width=70)
        self.tree.column("Name", width=150)
        self.tree.column("Selector", width=250)
        self.tree.column("Action", width=120)
        self.tree.column("DataKey", width=120)

        self.tree.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(fill="y", side="right")

        self.tree.bind("<Double-1>", self._on_tree_double_click)

    def _build_log_section(self):
        log_frame = ttk.LabelFrame(self, text=" Nhat ky ", padding=5)
        log_frame.pack(fill="both", expand=True, pady=5)

        self.log_text = tk.Text(log_frame, height=6, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 10))
        self.log_text.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _browse_project(self):
        from tkinter import filedialog

        path = filedialog.askdirectory()
        if path:
            self.shared["project_path"].set(path)
            if hasattr(self, "on_project_changed") and self.on_project_changed:
                self.on_project_changed()

    def _start_scan(self):
        url = self.shared["url_path"].get()
        if not url:
            messagebox.showwarning("Chu y", "Vui long nhap URL")
            return

        browser_name = self.shared["browser_var"].get()
        self._append_log(f"Bat dau quet: {url} (browser={browser_name})...")

        def run_scan():
            try:
                elements = self.logic.scan_url(url, browser_name=browser_name)
                self.after(0, lambda: self._update_tree(elements))
                self.after(0, lambda: self._append_log(f"Da tim thay {len(elements)} phan tu."))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Loi", str(e)))

        threading.Thread(target=run_scan, daemon=True).start()

    def _update_tree(self, elements):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for el in elements:
            name = el.get("name", "")
            self.tree.insert(
                "",
                "end",
                values=(
                    el.get("type", ""),
                    name,
                    el.get("selector", ""),
                    el.get("action", ""),
                    name.lower(),
                ),
            )

    def _on_tree_double_click(self, event):
        item_id = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        if not item_id:
            return

        col_idx = int(column.replace("#", "")) - 1
        if col_idx < 3:
            return

        current_values = list(self.tree.item(item_id, "values"))

        dialog = tk.Toplevel(self.winfo_toplevel())
        dialog.title("Chinh sua")
        dialog.geometry("300x120")

        heading_text = self.tree.heading(column)["text"]
        ttk.Label(dialog, text=f"Nhap gia tri moi cho {heading_text}:").pack(pady=5)
        entry = ttk.Entry(dialog, width=30)
        entry.insert(0, current_values[col_idx])
        entry.pack(pady=5)
        entry.focus_set()

        def save():
            current_values[col_idx] = entry.get()
            self.tree.item(item_id, values=current_values)
            dialog.destroy()

        ttk.Button(dialog, text="OK", command=save).pack()

    # ------------------------------------------------------------------
    # Locator / Template JSON editors
    # ------------------------------------------------------------------

    def _show_locators(self):
        url = self.shared["url_path"].get()
        page_id = self.shared["page_id_var"].get()
        if not url or not page_id:
            messagebox.showwarning("Chu y", "Vui long nhap URL va Page ID truoc")
            return

        locators_data = {}
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            key = vals[4].upper() if vals[4] else vals[1].upper().replace(" ", "_")
            if not key:
                key = f"ELEMENT_{item}"

            locators_data[key] = {
                "selector": vals[2],
                "type": "info" if vals[3] == "verify_text" else "action",
            }

        self._open_json_editor("Chinh sua Locators", locators_data, "locators")

    def _show_template(self):
        url = self.shared["url_path"].get()
        page_id = self.shared["page_id_var"].get()
        if not url or not page_id:
            messagebox.showwarning("Chu y", "Vui long nhap URL va Page ID truoc")
            return

        steps = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            key = vals[4].upper() if vals[4] else vals[1].upper().replace(" ", "_")
            if not key:
                continue
            steps.append({"id": key, "action": vals[3], "data_key": vals[4]})

        template_data = {"page_id": page_id, "url": url, "steps": steps}
        self._open_json_editor("Chinh sua Template", template_data, "templates")

    def _open_json_editor(self, title, data, type_json):
        editor_win = tk.Toplevel(self.winfo_toplevel())
        editor_win.title(title)
        editor_win.geometry("600x700")

        txt_area = tk.Text(editor_win, font=("Consolas", 11))
        txt_area.pack(fill="both", expand=True, padx=10, pady=10)

        json_str = json.dumps(data, indent=4, ensure_ascii=False)
        txt_area.insert("1.0", json_str)

        def save_json():
            try:
                content = txt_area.get("1.0", tk.END).strip()
                updated_data = json.loads(content)

                proj_path = self.shared["project_path"].get()
                url = self.shared["url_path"].get()
                page_id = self.shared["page_id_var"].get()

                if type_json == "locators":
                    self.logic.save_locator_json(proj_path, url, page_id, updated_data)
                else:
                    self.logic.save_template_json(proj_path, url, page_id, updated_data)

                messagebox.showinfo("Thanh cong", f"Da luu {type_json} thanh cong!")
                editor_win.destroy()
            except Exception as e:
                messagebox.showerror("Loi JSON", f"Dinh dang JSON khong hop le: {str(e)}")

        btn_frame = ttk.Frame(editor_win)
        btn_frame.pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="Luu lai", command=save_json).pack(side="right", padx=10)
        ttk.Button(btn_frame, text="Dong", command=editor_win.destroy).pack(side="right")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _append_log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
