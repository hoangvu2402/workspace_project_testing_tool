import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
from logic_manager import AutomationLogic
from pathlib import Path


class LocatorPanel(ttk.Frame):
    """Panel for scanning locators, displaying and editing locators & templates.
    Supports multi-page scanning: add unlimited URL + Page ID pairs and scan all sequentially."""

    def __init__(self, parent, logic: AutomationLogic, shared_vars: dict):
        super().__init__(parent, padding=0)
        self.logic = logic
        self.shared = shared_vars
        self._scan_pages = []  # list of dicts: {url, page_id}
        self._scan_results = {}  # page_id -> list of elements
        self.on_project_changed = None

        # Scrollable container
        self._canvas = tk.Canvas(self, highlightthickness=0)
        self._v_scroll = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self._inner = ttk.Frame(self._canvas, padding=10)

        self._inner.bind("<Configure>", lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas_window = self._canvas.create_window((0, 0), window=self._inner, anchor="nw")
        self._canvas.configure(yscrollcommand=self._v_scroll.set)

        self._v_scroll.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        # Resize inner frame width to match canvas
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        # Mouse wheel scrolling
        self._canvas.bind_all("<Button-4>", self._on_mousewheel_up, add="+")
        self._canvas.bind_all("<Button-5>", self._on_mousewheel_down, add="+")

        self._build_config_section()
        self._build_scan_list_section()
        self._build_elements_tree()
        self._build_ai_section()
        self._build_log_section()
        self._refresh_setup_scripts()

    def _on_canvas_configure(self, event):
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    def _on_mousewheel_up(self, event):
        self._canvas.yview_scroll(-3, "units")

    def _on_mousewheel_down(self, event):
        self._canvas.yview_scroll(3, "units")

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_config_section(self):
        cfg = ttk.LabelFrame(self._inner, text=" 1. Cau hinh Du an & Them trang quet ", padding=10)
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

        # Row 2: setup script selector
        ttk.Label(cfg, text="Setup script:").grid(row=2, column=0, sticky="w", pady=5)
        self.setup_combo = ttk.Combobox(cfg, width=35, state="readonly")
        self.setup_combo.grid(row=2, column=1, padx=5, sticky="w", columnspan=2)
        ttk.Button(cfg, text="Lam moi", command=self._refresh_setup_scripts).grid(row=2, column=3, padx=5)

        # Row 3: add page button
        btn_frame = ttk.Frame(cfg)
        btn_frame.grid(row=3, column=0, columnspan=5, pady=5)
        ttk.Button(btn_frame, text="Them trang vao danh sach", command=self._add_scan_page).pack(
            side="left", padx=5
        )
        ttk.Button(btn_frame, text="Quet trang hien tai", command=self._scan_single).pack(
            side="left", padx=5
        )

    def _build_scan_list_section(self):
        scan_frame = ttk.LabelFrame(self._inner, text=" 2. Danh sach trang quet ", padding=5)
        scan_frame.pack(fill="x", pady=5)

        # Scan list treeview
        columns = ("STT", "URL", "PageID", "Trang thai")
        self.scan_tree = ttk.Treeview(scan_frame, columns=columns, show="headings", height=3)
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
            self._inner,
            text=" 3. Cac phan tu tim thay ",
            padding=5,
        )
        frame.pack(fill="x", pady=5)

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
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=8)
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

        self.tree.pack(fill="x", side="left", expand=True)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(fill="y", side="right")

        self.tree.bind("<Double-1>", self._on_tree_double_click)

    def _build_log_section(self):
        log_frame = ttk.LabelFrame(self._inner, text=" Nhat ky ", padding=5)
        log_frame.pack(fill="x", pady=5)

        self.log_text = tk.Text(log_frame, height=4, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 10))
        self.log_text.pack(fill="x")

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

    def _get_setup_script_path(self):
        """Return the absolute path of the selected setup script, or empty string."""
        script_name = self.setup_combo.get()
        if not script_name or script_name == "(Khong dung)":
            return ""
        proj = self.shared["project_path"].get()
        return self.logic.get_setup_script_path(proj, script_name)

    def _refresh_setup_scripts(self):
        """Refresh the setup script dropdown."""
        proj = self.shared["project_path"].get()
        scripts = self.logic.get_setup_scripts(proj)
        values = ["(Khong dung)"] + scripts
        self.setup_combo["values"] = values
        self.setup_combo.set(values[0])

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

        setup_script = self._get_setup_script_path()
        if setup_script:
            self._append_log(f"Chay setup script: {self.setup_combo.get()}")
        self._append_log(f"Bat dau quet: {page_id} ({url})...")

        def run_scan():
            try:
                elements = self.logic.scan_url(url, setup_script=setup_script)
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
        setup_script = self._get_setup_script_path()
        if setup_script:
            self._append_log(f"Setup script: {self.setup_combo.get()}")
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
                    elements = self.logic.scan_url(url, setup_script=setup_script)
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
    # AI Generation Section
    # ------------------------------------------------------------------

    def _build_ai_section(self):
        ai_frame = ttk.LabelFrame(self._inner, text=" 4. AI - Tao test tu dong (Gemini) ", padding=5)
        ai_frame.pack(fill="x", pady=5)

        # Row 0: API key
        ttk.Label(ai_frame, text="API Key:").grid(row=0, column=0, sticky="w")
        self.api_key_var = tk.StringVar()
        self.api_key_entry = ttk.Entry(ai_frame, textvariable=self.api_key_var, width=50, show="*")
        self.api_key_entry.grid(row=0, column=1, padx=5, sticky="w", columnspan=2)
        ttk.Button(ai_frame, text="Hien/An", command=self._toggle_api_key_visibility).grid(
            row=0, column=3, padx=5
        )

        # Row 1: Use case text area
        ttk.Label(ai_frame, text="Use Case:").grid(row=1, column=0, sticky="nw", pady=5)
        self.usecase_text = tk.Text(ai_frame, height=5, width=70, font=("Consolas", 10))
        self.usecase_text.grid(row=1, column=1, padx=5, pady=5, columnspan=3, sticky="we")

        # Row 2: Generate button
        btn_frame = ttk.Frame(ai_frame)
        btn_frame.grid(row=2, column=0, columnspan=4, pady=5)
        self.ai_generate_btn = ttk.Button(
            btn_frame, text="TAO BANG AI", command=self._on_ai_generate
        )
        self.ai_generate_btn.pack(side="left", padx=5)
        self.ai_status_label = ttk.Label(btn_frame, text="")
        self.ai_status_label.pack(side="left", padx=10)

    def _toggle_api_key_visibility(self):
        current = self.api_key_entry.cget("show")
        self.api_key_entry.config(show="" if current == "*" else "*")

    def _on_ai_generate(self):
        """Handle AI generate button click."""
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showwarning("Chu y", "Vui long nhap API Key cua Google AI Studio.")
            return

        use_case = self.usecase_text.get("1.0", tk.END).strip()
        if not use_case:
            messagebox.showwarning("Chu y", "Vui long nhap Use Case.")
            return

        page_id = self.page_selector.get()
        if not page_id:
            page_id = self.shared["page_id_var"].get().strip()
        if not page_id:
            messagebox.showwarning("Chu y", "Vui long chon trang (quet truoc khi dung AI).")
            return

        # Get URL
        url = ""
        if page_id in self._scan_results:
            url = self._scan_results[page_id].get("url", "")
        if not url:
            url = self.shared["url_path"].get().strip()

        # Build current locators from tree
        locators = {}
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            key = vals[4].upper() if vals[4] else vals[1].upper().replace(" ", "_")
            if not key:
                continue
            locators[key] = {
                "selector": vals[2],
                "type": "info" if vals[3] == "verify_text" else "action",
            }

        # Build current template from tree
        steps = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            key = vals[4].upper() if vals[4] else vals[1].upper().replace(" ", "_")
            if not key:
                continue
            steps.append({"id": key, "action": vals[3], "data_key": vals[4]})
        template = {"page_id": page_id, "url": url, "steps": steps}

        # Configure AI and call
        self.logic.configure_ai(api_key)
        self.ai_generate_btn.config(state="disabled")
        self.ai_status_label.config(text="Dang xu ly... (tu dong thu lai neu bi rate limit)")
        self._append_log(f"[AI] Dang goi Gemini AI cho {page_id}...")

        def run_ai():
            try:
                result = self.logic.ai_generate(use_case, locators, template, page_id, url)
                self.after(0, lambda r=result: self._show_ai_results(r, page_id, url))
                self.after(0, lambda: self._append_log(f"[AI] Hoan thanh! {result.get('summary', '')}"))
                self.after(0, lambda: self.ai_status_label.config(text="Hoan thanh!"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Loi AI", str(e)))
                self.after(0, lambda: self._append_log(f"[AI] Loi: {str(e)}"))
                self.after(0, lambda: self.ai_status_label.config(text="Loi!"))
            finally:
                self.after(0, lambda: self.ai_generate_btn.config(state="normal"))

        threading.Thread(target=run_ai, daemon=True).start()

    def _show_ai_results(self, result, page_id, url):
        """Open a dialog showing the AI-generated results with tabs for each artifact."""
        win = tk.Toplevel(self.winfo_toplevel())
        win.title(f"Ket qua AI - {page_id}")
        win.geometry("800x700")

        # Summary
        if result.get("summary"):
            summary_frame = ttk.LabelFrame(win, text=" Tom tat ", padding=5)
            summary_frame.pack(fill="x", padx=10, pady=5)
            ttk.Label(summary_frame, text=result["summary"], wraplength=750).pack(fill="x")

        # Notebook with tabs
        notebook = ttk.Notebook(win)
        notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # Tab 1: Locators
        loc_frame = ttk.Frame(notebook, padding=5)
        notebook.add(loc_frame, text=" Locators ")
        loc_text = tk.Text(loc_frame, font=("Consolas", 10))
        loc_text.pack(fill="both", expand=True)
        loc_text.insert("1.0", json.dumps(result.get("locators", {}), indent=4, ensure_ascii=False))

        # Tab 2: Template
        tpl_frame = ttk.Frame(notebook, padding=5)
        notebook.add(tpl_frame, text=" Template ")
        tpl_text = tk.Text(tpl_frame, font=("Consolas", 10))
        tpl_text.pack(fill="both", expand=True)
        tpl_text.insert("1.0", json.dumps(result.get("template", {}), indent=4, ensure_ascii=False))

        # Tab 3: Test Data
        td_frame = ttk.Frame(notebook, padding=5)
        notebook.add(td_frame, text=" Du lieu test ")
        td_text = tk.Text(td_frame, font=("Consolas", 10))
        td_text.pack(fill="both", expand=True)
        td_text.insert("1.0", json.dumps(result.get("test_data", []), indent=4, ensure_ascii=False))

        # Tab 4: Setup Script
        ss_frame = ttk.Frame(notebook, padding=5)
        notebook.add(ss_frame, text=" Setup Script ")
        ss_text = tk.Text(ss_frame, font=("Consolas", 10))
        ss_text.pack(fill="both", expand=True)
        setup_data = result.get("setup_script")
        if setup_data:
            ss_text.insert("1.0", json.dumps(setup_data, indent=4, ensure_ascii=False))
        else:
            ss_text.insert("1.0", "null\n\n(Khong can setup script cho use case nay)")

        # Save buttons
        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill="x", padx=10, pady=10)

        def save_all():
            self._save_ai_artifacts(loc_text, tpl_text, td_text, ss_text, page_id, url, win)

        ttk.Button(btn_frame, text="LUU TAT CA", command=save_all).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Dong", command=win.destroy).pack(side="right", padx=5)

        # Individual save buttons for each tab
        loc_btn = ttk.Frame(loc_frame)
        loc_btn.pack(fill="x", pady=5)
        ttk.Button(loc_btn, text="Luu Locators", command=lambda: self._save_single_artifact(
            "locators", loc_text, page_id, url
        )).pack(side="right")

        tpl_btn = ttk.Frame(tpl_frame)
        tpl_btn.pack(fill="x", pady=5)
        ttk.Button(tpl_btn, text="Luu Template", command=lambda: self._save_single_artifact(
            "template", tpl_text, page_id, url
        )).pack(side="right")

        td_btn = ttk.Frame(td_frame)
        td_btn.pack(fill="x", pady=5)
        ttk.Button(td_btn, text="Luu Test Data", command=lambda: self._save_single_artifact(
            "test_data", td_text, page_id, url
        )).pack(side="right")

        ss_btn = ttk.Frame(ss_frame)
        ss_btn.pack(fill="x", pady=5)
        ttk.Button(ss_btn, text="Luu Setup Script", command=lambda: self._save_single_artifact(
            "setup_script", ss_text, page_id, url
        )).pack(side="right")

    def _save_single_artifact(self, artifact_type, text_widget, page_id, url):
        """Save a single AI-generated artifact."""
        proj_path = self.shared["project_path"].get()
        content = text_widget.get("1.0", tk.END).strip()

        try:
            if artifact_type == "locators":
                data = json.loads(content)
                self.logic.save_locator_json(proj_path, url, page_id, data)
                messagebox.showinfo("Thanh cong", f"Da luu locators cho {page_id}!")

            elif artifact_type == "template":
                data = json.loads(content)
                self.logic.save_template_json(proj_path, url, page_id, data)
                messagebox.showinfo("Thanh cong", f"Da luu template cho {page_id}!")

            elif artifact_type == "test_data":
                data = json.loads(content)
                if isinstance(data, list) and data:
                    headers = list(data[0].keys())
                    filepath = self.logic.save_test_data_from_rows(
                        proj_path, url, page_id, data, headers
                    )
                    messagebox.showinfo("Thanh cong", f"Da luu test data: {filepath}")
                else:
                    messagebox.showwarning("Chu y", "Khong co du lieu test de luu.")

            elif artifact_type == "setup_script":
                if content.strip() == "null" or not content.strip():
                    messagebox.showinfo("Thong bao", "Khong co setup script de luu.")
                    return
                data = json.loads(content)
                script_name = f"{page_id}_setup.json"
                filepath = self.logic.save_setup_script(proj_path, script_name, data)
                messagebox.showinfo("Thanh cong", f"Da luu setup script: {filepath}")
                self._refresh_setup_scripts()

        except json.JSONDecodeError as e:
            messagebox.showerror("Loi JSON", f"Dinh dang JSON khong hop le: {e}")
        except Exception as e:
            messagebox.showerror("Loi", str(e))

    def _save_ai_artifacts(self, loc_text, tpl_text, td_text, ss_text, page_id, url, win):
        """Save all AI-generated artifacts at once."""
        saved = []
        errors = []

        for name, text_widget, artifact_type in [
            ("Locators", loc_text, "locators"),
            ("Template", tpl_text, "template"),
            ("Test Data", td_text, "test_data"),
            ("Setup Script", ss_text, "setup_script"),
        ]:
            try:
                self._save_single_artifact(artifact_type, text_widget, page_id, url)
                saved.append(name)
            except Exception as e:
                errors.append(f"{name}: {e}")

        if errors:
            messagebox.showwarning(
                "Ket qua luu",
                f"Da luu: {', '.join(saved)}\nLoi: {'; '.join(errors)}"
            )
        else:
            self._append_log(f"[AI] Da luu tat ca artifacts cho {page_id}.")

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
