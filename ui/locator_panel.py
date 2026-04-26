import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
from logic_manager import AutomationLogic


class LocatorPanel(ttk.Frame):
    """Panel for scanning locators, displaying and editing locators & templates.
    Supports multi-page scanning: add unlimited URL + Page ID pairs and scan all sequentially."""

    def __init__(self, parent, logic: AutomationLogic, shared_vars: dict):
        super().__init__(parent, padding=10)
        self.logic = logic
        self.shared = shared_vars
        self._scan_pages = []  # list of dicts: {url, page_id}
        self._scan_results = {}  # page_id -> list of elements
        self.on_project_changed = None

        self._build_config_section()
        self._build_scan_list_section()
        self._build_elements_tree()
        self._build_log_section()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_config_section(self):
        cfg = ttk.LabelFrame(self, text=" 1. Cau hinh Du an & Them trang quet ", padding=10)
        cfg.pack(fill="x", pady=(0, 5))

        # Row 0: project path
        ttk.Label(cfg, text="Thu muc du an:").grid(row=0, column=0, sticky="w")
        self.project_entry = ttk.Entry(cfg, textvariable=self.shared["project_path"], width=60)
        self.project_entry.grid(row=0, column=1, padx=5, columnspan=3)
        ttk.Button(cfg, text="Duyet...", command=self._browse_project).grid(row=0, column=4)

        # Row 1: URL input
        ttk.Label(cfg, text="URL trang:").grid(row=1, column=0, sticky="w", pady=5)
        self.url_entry = ttk.Entry(cfg, textvariable=self.shared["url_path"], width=50)
        self.url_entry.grid(row=1, column=1, padx=5, columnspan=2)

        # Row 1: Page ID input + Add button
        ttk.Label(cfg, text="Page ID:").grid(row=1, column=3, sticky="w", padx=(10, 0))
        ttk.Entry(cfg, textvariable=self.shared["page_id_var"], width=15).grid(row=1, column=4, padx=5)

        # Row 2: add page button
        btn_frame = ttk.Frame(cfg)
        btn_frame.grid(row=2, column=0, columnspan=5, pady=5)
        ttk.Button(btn_frame, text="Them trang vao danh sach", command=self._add_scan_page).pack(
            side="left", padx=5
        )
        ttk.Button(btn_frame, text="Quet trang hien tai", command=self._scan_single).pack(
            side="left", padx=5
        )

    def _build_scan_list_section(self):
        scan_frame = ttk.LabelFrame(self, text=" 2. Danh sach trang quet ", padding=10)
        scan_frame.pack(fill="x", pady=5)

        # Scan list treeview
        columns = ("STT", "URL", "PageID", "Trang thai")
        self.scan_tree = ttk.Treeview(scan_frame, columns=columns, show="headings", height=4)
        self.scan_tree.heading("STT", text="#")
        self.scan_tree.heading("URL", text="URL")
        self.scan_tree.heading("PageID", text="Page ID")
        self.scan_tree.heading("Trang thai", text="Trang thai")

        self.scan_tree.column("STT", width=30)
        self.scan_tree.column("URL", width=400)
        self.scan_tree.column("PageID", width=100)
        self.scan_tree.column("Trang thai", width=100)

        self.scan_tree.pack(fill="x", side="top")

        # Control buttons
        scan_btn_frame = ttk.Frame(scan_frame)
        scan_btn_frame.pack(fill="x", pady=5)

        ttk.Button(scan_btn_frame, text="Len", command=self._move_page_up).pack(side="left", padx=3)
        ttk.Button(scan_btn_frame, text="Xuong", command=self._move_page_down).pack(side="left", padx=3)
        ttk.Button(scan_btn_frame, text="Xoa muc chon", command=self._remove_scan_page).pack(
            side="left", padx=3
        )
        ttk.Button(scan_btn_frame, text="Xoa tat ca", command=self._clear_scan_pages).pack(
            side="left", padx=3
        )

        self.scan_all_btn = ttk.Button(
            scan_btn_frame, text="QUET TAT CA", command=self._scan_all_pages
        )
        self.scan_all_btn.pack(side="right", padx=10)

    def _build_elements_tree(self):
        frame = ttk.LabelFrame(
            self,
            text=" 3. Cac phan tu tim thay ",
            padding=10,
        )
        frame.pack(fill="both", expand=True, pady=5)

        # Page selector for viewing results
        selector_frame = ttk.Frame(frame)
        selector_frame.pack(fill="x", pady=(0, 5))

        ttk.Label(selector_frame, text="Xem trang:").pack(side="left")
        self.page_selector = ttk.Combobox(selector_frame, width=30, state="readonly")
        self.page_selector.pack(side="left", padx=5)
        self.page_selector.bind("<<ComboboxSelected>>", self._on_page_selector_changed)

        ttk.Button(selector_frame, text="Hien Locator", command=self._show_locators).pack(
            side="left", padx=5
        )
        ttk.Button(selector_frame, text="Hien Template", command=self._show_template).pack(
            side="left", padx=5
        )

        # Treeview
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

        self.log_text = tk.Text(log_frame, height=5, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 10))
        self.log_text.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    # Scan page list management
    # ------------------------------------------------------------------

    def _add_scan_page(self):
        url = self.shared["url_path"].get().strip()
        page_id = self.shared["page_id_var"].get().strip()

        if not url:
            messagebox.showwarning("Chu y", "Vui long nhap URL")
            return
        if not page_id:
            messagebox.showwarning("Chu y", "Vui long nhap Page ID")
            return

        self._scan_pages.append({"url": url, "page_id": page_id, "status": "Cho quet"})
        self._refresh_scan_tree()
        self._append_log(f"Da them trang: {page_id} ({url})")

    def _refresh_scan_tree(self):
        for child in self.scan_tree.get_children():
            self.scan_tree.delete(child)
        for i, page in enumerate(self._scan_pages, 1):
            self.scan_tree.insert(
                "",
                "end",
                values=(i, page["url"], page["page_id"], page.get("status", "Cho quet")),
            )

    def _move_page_up(self):
        sel = self.scan_tree.selection()
        if not sel:
            return
        idx = self.scan_tree.index(sel[0])
        if idx > 0:
            self._scan_pages[idx], self._scan_pages[idx - 1] = (
                self._scan_pages[idx - 1],
                self._scan_pages[idx],
            )
            self._refresh_scan_tree()
            children = self.scan_tree.get_children()
            self.scan_tree.selection_set(children[idx - 1])

    def _move_page_down(self):
        sel = self.scan_tree.selection()
        if not sel:
            return
        idx = self.scan_tree.index(sel[0])
        if idx < len(self._scan_pages) - 1:
            self._scan_pages[idx], self._scan_pages[idx + 1] = (
                self._scan_pages[idx + 1],
                self._scan_pages[idx],
            )
            self._refresh_scan_tree()
            children = self.scan_tree.get_children()
            self.scan_tree.selection_set(children[idx + 1])

    def _remove_scan_page(self):
        sel = self.scan_tree.selection()
        if not sel:
            return
        idx = self.scan_tree.index(sel[0])
        removed = self._scan_pages.pop(idx)
        # Remove from results too
        self._scan_results.pop(removed["page_id"], None)
        self._refresh_scan_tree()
        self._update_page_selector()
        self._append_log(f"Da xoa trang: {removed['page_id']}")

    def _clear_scan_pages(self):
        self._scan_pages.clear()
        self._scan_results.clear()
        self._refresh_scan_tree()
        self._update_page_selector()
        self._append_log("Da xoa tat ca trang trong danh sach.")

    # ------------------------------------------------------------------
    # Scanning
    # ------------------------------------------------------------------

    def _scan_single(self):
        """Scan the current URL + Page ID (existing single-page behavior)."""
        url = self.shared["url_path"].get().strip()
        page_id = self.shared["page_id_var"].get().strip()
        if not url:
            messagebox.showwarning("Chu y", "Vui long nhap URL")
            return
        if not page_id:
            messagebox.showwarning("Chu y", "Vui long nhap Page ID")
            return

        self._append_log(f"Bat dau quet: {page_id} ({url})...")

        def run_scan():
            try:
                elements = self.logic.scan_url(url)
                self._scan_results[page_id] = {"url": url, "elements": elements}
                self.after(0, lambda: self._update_tree(elements))
                self.after(0, lambda: self._update_page_selector())
                self.after(0, lambda p=page_id: self.page_selector.set(p))
                self.after(
                    0,
                    lambda: self._append_log(
                        f"Da quet xong {page_id}: {len(elements)} phan tu."
                    ),
                )
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Loi", str(e)))
                self.after(0, lambda: self._append_log(f"Loi khi quet {page_id}: {str(e)}"))

        threading.Thread(target=run_scan, daemon=True).start()

    def _scan_all_pages(self):
        """Scan all pages in the scan list sequentially."""
        if not self._scan_pages:
            messagebox.showwarning("Chu y", "Danh sach trang trong. Vui long them trang truoc.")
            return

        self.scan_all_btn.config(state="disabled")
        total = len(self._scan_pages)
        self._append_log(f"\nBat dau quet {total} trang...\n{'='*40}")

        def run_all():
            for i, page_info in enumerate(self._scan_pages):
                url = page_info["url"]
                page_id = page_info["page_id"]

                self.after(
                    0,
                    lambda n=i + 1, t=total, p=page_id, u=url: self._append_log(
                        f"[{n}/{t}] Dang quet: {p} ({u})..."
                    ),
                )

                # Update status to scanning
                page_info["status"] = "Dang quet..."
                self.after(0, self._refresh_scan_tree)

                try:
                    elements = self.logic.scan_url(url)
                    self._scan_results[page_id] = {"url": url, "elements": elements}

                    # Auto-save locators and template
                    proj_path = self.shared["project_path"].get()
                    locators_data = self._build_locators_from_elements(elements)
                    template_data = self._build_template_from_elements(page_id, url, elements)
                    self.logic.save_locator_json(proj_path, url, page_id, locators_data)
                    self.logic.save_template_json(proj_path, url, page_id, template_data)

                    page_info["status"] = f"Xong ({len(elements)})"
                    self.after(0, self._refresh_scan_tree)
                    self.after(
                        0,
                        lambda p=page_id, c=len(elements): self._append_log(
                            f"  -> {p}: {c} phan tu. Da luu locators & template."
                        ),
                    )
                except Exception as e:
                    page_info["status"] = "Loi!"
                    self.after(0, self._refresh_scan_tree)
                    self.after(
                        0,
                        lambda p=page_id, err=str(e): self._append_log(
                            f"  -> Loi khi quet {p}: {err}"
                        ),
                    )

            self.after(0, self._update_page_selector)
            # Auto-select the first page
            if self._scan_results:
                first_page = next(iter(self._scan_results))
                self.after(0, lambda p=first_page: self.page_selector.set(p))
                elements = self._scan_results[first_page]["elements"]
                self.after(0, lambda e=elements: self._update_tree(e))

            self.after(
                0,
                lambda: self._append_log(
                    f"{'='*40}\nHoan thanh quet {total} trang.\n"
                ),
            )
            self.after(0, lambda: self.scan_all_btn.config(state="normal"))

        threading.Thread(target=run_all, daemon=True).start()

    # ------------------------------------------------------------------
    # Build locators/template from scanned elements
    # ------------------------------------------------------------------

    @staticmethod
    def _build_locators_from_elements(elements):
        locators = {}
        for el in elements:
            name = el.get("name", "")
            key = name.upper().replace(" ", "_") if name else "ELEMENT"
            if not key:
                continue
            locators[key] = {
                "selector": el.get("selector", ""),
                "type": "info" if el.get("action") == "verify_text" else "action",
            }
        return locators

    @staticmethod
    def _build_template_from_elements(page_id, url, elements):
        steps = []
        for el in elements:
            name = el.get("name", "")
            key = name.upper().replace(" ", "_") if name else ""
            if not key:
                continue
            steps.append({
                "id": key,
                "action": el.get("action", "click"),
                "data_key": name.lower().replace(" ", "_") if name else "",
            })
        return {"page_id": page_id, "url": url, "steps": steps}

    # ------------------------------------------------------------------
    # Page selector & elements tree
    # ------------------------------------------------------------------

    def _update_page_selector(self):
        pages = list(self._scan_results.keys())
        self.page_selector["values"] = pages
        if pages and not self.page_selector.get():
            self.page_selector.set(pages[0])

    def _on_page_selector_changed(self, event=None):
        page_id = self.page_selector.get()
        if page_id in self._scan_results:
            elements = self._scan_results[page_id]["elements"]
            self._update_tree(elements)

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
        page_id = self.page_selector.get()
        if not page_id:
            # Fallback to shared var
            page_id = self.shared["page_id_var"].get()

        if not page_id:
            messagebox.showwarning("Chu y", "Vui long chon trang de xem locators")
            return

        url = ""
        if page_id in self._scan_results:
            url = self._scan_results[page_id].get("url", "")
        if not url:
            url = self.shared["url_path"].get()

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

        self._open_json_editor("Chinh sua Locators", locators_data, "locators", page_id, url)

    def _show_template(self):
        page_id = self.page_selector.get()
        if not page_id:
            page_id = self.shared["page_id_var"].get()

        if not page_id:
            messagebox.showwarning("Chu y", "Vui long chon trang de xem template")
            return

        url = ""
        if page_id in self._scan_results:
            url = self._scan_results[page_id].get("url", "")
        if not url:
            url = self.shared["url_path"].get()

        steps = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            key = vals[4].upper() if vals[4] else vals[1].upper().replace(" ", "_")
            if not key:
                continue
            steps.append({"id": key, "action": vals[3], "data_key": vals[4]})

        template_data = {"page_id": page_id, "url": url, "steps": steps}
        self._open_json_editor("Chinh sua Template", template_data, "templates", page_id, url)

    def _open_json_editor(self, title, data, type_json, page_id, url):
        editor_win = tk.Toplevel(self.winfo_toplevel())
        editor_win.title(f"{title} - {page_id}")
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

                if type_json == "locators":
                    self.logic.save_locator_json(proj_path, url, page_id, updated_data)
                else:
                    self.logic.save_template_json(proj_path, url, page_id, updated_data)

                messagebox.showinfo("Thanh cong", f"Da luu {type_json} cho {page_id} thanh cong!")
                editor_win.destroy()
            except Exception as e:
                messagebox.showerror("Loi JSON", f"Dinh dang JSON khong hop le: {str(e)}")

        btn_frame = ttk.Frame(editor_win)
        btn_frame.pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="Luu lai", command=save_json).pack(side="right", padx=10)
        ttk.Button(btn_frame, text="Dong", command=editor_win.destroy).pack(side="right")

    # ------------------------------------------------------------------
    # Project browsing
    # ------------------------------------------------------------------

    def _browse_project(self):
        from tkinter import filedialog

        path = filedialog.askdirectory()
        if path:
            self.shared["project_path"].set(path)
            if self.on_project_changed:
                self.on_project_changed()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _append_log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
