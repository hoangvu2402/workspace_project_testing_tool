import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
from pathlib import Path
from logic_manager import AutomationLogic


# Default actions config path
ACTIONS_CONFIG = Path(__file__).resolve().parent.parent / "config" / "actions_config.json"


class ActionManagerPanel(ttk.Frame):
    """Panel for defining and managing test actions, mapped to Playwright functions."""

    def __init__(self, parent, logic: AutomationLogic, shared_vars: dict):
        super().__init__(parent, padding=10)
        self.logic = logic
        self.shared = shared_vars
        self._config = self._load_config()
        self._editing_action = None  # action key being edited, or None for new

        self._build_action_list_section()
        self._build_editor_section()
        self._build_codegen_section()
        self._refresh_action_list()

    # ------------------------------------------------------------------
    # Config I/O
    # ------------------------------------------------------------------

    def _load_config(self):
        if ACTIONS_CONFIG.exists():
            with open(ACTIONS_CONFIG, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"actions": {}, "playwright_functions": {}}

    def _save_config(self):
        with open(ACTIONS_CONFIG, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=4, ensure_ascii=False)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_action_list_section(self):
        frame = ttk.LabelFrame(self, text=" 1. Danh sach Action ", padding=10)
        frame.pack(fill="x", pady=(0, 5))

        # Treeview
        columns = ("Action", "HienThi", "PlaywrightFn", "Selector", "Value", "LoaiAction")
        self.action_tree = ttk.Treeview(frame, columns=columns, show="headings", height=8)
        self.action_tree.heading("Action", text="Action Key")
        self.action_tree.heading("HienThi", text="Ten hien thi")
        self.action_tree.heading("PlaywrightFn", text="Playwright Function")
        self.action_tree.heading("Selector", text="Selector?")
        self.action_tree.heading("Value", text="Value?")
        self.action_tree.heading("LoaiAction", text="Loai")

        self.action_tree.column("Action", width=110)
        self.action_tree.column("HienThi", width=180)
        self.action_tree.column("PlaywrightFn", width=170)
        self.action_tree.column("Selector", width=60)
        self.action_tree.column("Value", width=60)
        self.action_tree.column("LoaiAction", width=90)

        self.action_tree.pack(fill="x", side="top")
        self.action_tree.bind("<<TreeviewSelect>>", self._on_action_selected)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.action_tree.yview)
        self.action_tree.configure(yscrollcommand=scrollbar.set)

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="Tao moi", command=self._new_action).pack(side="left", padx=3)
        ttk.Button(btn_frame, text="Xoa action", command=self._delete_action).pack(side="left", padx=3)
        ttk.Button(btn_frame, text="Lam moi", command=self._refresh_action_list).pack(side="left", padx=3)

    def _build_editor_section(self):
        frame = ttk.LabelFrame(self, text=" 2. Chinh sua Action ", padding=10)
        frame.pack(fill="x", pady=5)

        # Row 0: action key + display name
        ttk.Label(frame, text="Action Key:").grid(row=0, column=0, sticky="w")
        self.key_var = tk.StringVar()
        self.key_entry = ttk.Entry(frame, textvariable=self.key_var, width=20)
        self.key_entry.grid(row=0, column=1, padx=5, sticky="w")

        ttk.Label(frame, text="Ten hien thi:").grid(row=0, column=2, sticky="w", padx=10)
        self.display_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.display_var, width=30).grid(row=0, column=3, padx=5, sticky="w")

        # Row 1: playwright function + category
        ttk.Label(frame, text="Playwright Function:").grid(row=1, column=0, sticky="w", pady=5)
        self.pw_func_var = tk.StringVar()
        self.pw_func_combo = ttk.Combobox(frame, textvariable=self.pw_func_var, width=25)
        pw_funcs = sorted(self._config.get("playwright_functions", {}).keys())
        self.pw_func_combo["values"] = pw_funcs
        self.pw_func_combo.grid(row=1, column=1, padx=5, sticky="w")
        self.pw_func_combo.bind("<<ComboboxSelected>>", self._on_pw_func_selected)

        ttk.Label(frame, text="Loai:").grid(row=1, column=2, sticky="w", padx=10)
        self.category_var = tk.StringVar(value="interaction")
        cat_combo = ttk.Combobox(frame, textvariable=self.category_var, width=15)
        cat_combo["values"] = ("interaction", "verification", "utility")
        cat_combo.grid(row=1, column=3, padx=5, sticky="w")

        # Row 2: needs_selector + needs_value
        self.needs_selector_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="Can Selector", variable=self.needs_selector_var).grid(
            row=2, column=0, sticky="w", pady=5
        )

        self.needs_value_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="Can Value (tu data)", variable=self.needs_value_var).grid(
            row=2, column=1, sticky="w"
        )

        # Row 2: assertion type
        ttk.Label(frame, text="Assertion:").grid(row=2, column=2, sticky="w", padx=10)
        self.assertion_var = tk.StringVar(value="none")
        assert_combo = ttk.Combobox(frame, textvariable=self.assertion_var, width=15)
        assert_combo["values"] = ("none", "text_contains", "is_visible", "url_contains")
        assert_combo.grid(row=2, column=3, padx=5, sticky="w")

        # Row 3: log message
        ttk.Label(frame, text="Log message:").grid(row=3, column=0, sticky="w", pady=5)
        self.log_msg_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.log_msg_var, width=60).grid(
            row=3, column=1, padx=5, sticky="w", columnspan=3
        )

        # Row 4: function info display
        self.func_info_label = ttk.Label(frame, text="", foreground="gray")
        self.func_info_label.grid(row=4, column=0, columnspan=4, sticky="w", pady=3)

        # Row 5: extra params (JSON)
        ttk.Label(frame, text="Tham so them (JSON):").grid(row=5, column=0, sticky="nw", pady=5)
        self.params_text = tk.Text(frame, height=3, width=55, font=("Consolas", 9))
        self.params_text.grid(row=5, column=1, padx=5, columnspan=3, sticky="w")
        self.params_text.insert("1.0", "{}")

        # Row 6: buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=6, column=0, columnspan=4, pady=8)
        ttk.Button(btn_frame, text="Luu Action", command=self._save_action).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Huy", command=self._clear_editor).pack(side="left", padx=5)

    def _build_codegen_section(self):
        frame = ttk.LabelFrame(self, text=" 3. Sinh code tu dong ", padding=10)
        frame.pack(fill="both", expand=True, pady=5)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x")

        ttk.Button(btn_frame, text="Xem truoc code base_page.py", command=self._preview_base_page).pack(
            side="left", padx=5
        )
        ttk.Button(btn_frame, text="Xem truoc code generic_runner.py", command=self._preview_runner).pack(
            side="left", padx=5
        )
        ttk.Button(btn_frame, text="GHI CODE VAO FILE", command=self._write_code).pack(
            side="right", padx=5
        )

        self.code_preview = scrolledtext.ScrolledText(
            frame, height=12, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 10)
        )
        self.code_preview.pack(fill="both", expand=True, pady=5)

    # ------------------------------------------------------------------
    # Action list management
    # ------------------------------------------------------------------

    def _refresh_action_list(self):
        for child in self.action_tree.get_children():
            self.action_tree.delete(child)
        actions = self._config.get("actions", {})
        for key, info in actions.items():
            self.action_tree.insert("", "end", values=(
                key,
                info.get("display_name", key),
                info.get("playwright_method", ""),
                "Co" if info.get("needs_selector") else "Khong",
                "Co" if info.get("needs_value") else "Khong",
                info.get("category", ""),
            ))

    def _on_action_selected(self, event=None):
        sel = self.action_tree.selection()
        if not sel:
            return
        values = self.action_tree.item(sel[0], "values")
        action_key = values[0]
        action_info = self._config["actions"].get(action_key, {})
        self._editing_action = action_key
        self._populate_editor(action_key, action_info)

    def _populate_editor(self, key, info):
        self.key_var.set(key)
        self.display_var.set(info.get("display_name", ""))
        self.pw_func_var.set(info.get("playwright_method", ""))
        self.category_var.set(info.get("category", "interaction"))
        self.needs_selector_var.set(info.get("needs_selector", True))
        self.needs_value_var.set(info.get("needs_value", False))
        self.assertion_var.set(info.get("assertion", "none"))
        self.log_msg_var.set(info.get("log_message", ""))
        self.params_text.delete("1.0", tk.END)
        self.params_text.insert("1.0", json.dumps(info.get("params", {}), indent=2, ensure_ascii=False))
        self._update_func_info()

    def _new_action(self):
        self._editing_action = None
        self._clear_editor()
        self.key_entry.focus()

    def _clear_editor(self):
        self._editing_action = None
        self.key_var.set("")
        self.display_var.set("")
        self.pw_func_var.set("")
        self.category_var.set("interaction")
        self.needs_selector_var.set(True)
        self.needs_value_var.set(False)
        self.assertion_var.set("none")
        self.log_msg_var.set("")
        self.params_text.delete("1.0", tk.END)
        self.params_text.insert("1.0", "{}")
        self.func_info_label.config(text="")

    def _save_action(self):
        key = self.key_var.get().strip()
        if not key:
            messagebox.showwarning("Chu y", "Vui long nhap Action Key")
            return
        if not self.pw_func_var.get():
            messagebox.showwarning("Chu y", "Vui long chon Playwright Function")
            return

        try:
            params = json.loads(self.params_text.get("1.0", tk.END).strip())
        except json.JSONDecodeError:
            messagebox.showerror("Loi", "Tham so them khong phai JSON hop le")
            return

        action_def = {
            "display_name": self.display_var.get() or key,
            "playwright_method": self.pw_func_var.get(),
            "needs_selector": self.needs_selector_var.get(),
            "needs_value": self.needs_value_var.get(),
            "params": params,
            "log_message": self.log_msg_var.get(),
            "category": self.category_var.get(),
        }
        assertion = self.assertion_var.get()
        if assertion != "none":
            action_def["assertion"] = assertion

        # If renaming an action, remove old key
        if self._editing_action and self._editing_action != key:
            self._config["actions"].pop(self._editing_action, None)

        self._config["actions"][key] = action_def
        self._save_config()
        self._refresh_action_list()
        self._editing_action = key
        self._set_code_preview(f"Da luu action: {key}")

    def _delete_action(self):
        sel = self.action_tree.selection()
        if not sel:
            messagebox.showwarning("Chu y", "Vui long chon action de xoa")
            return
        key = self.action_tree.item(sel[0], "values")[0]
        if messagebox.askyesno("Xac nhan", f"Xoa action '{key}'?"):
            self._config["actions"].pop(key, None)
            self._save_config()
            self._refresh_action_list()
            self._clear_editor()
            self._set_code_preview(f"Da xoa action: {key}")

    # ------------------------------------------------------------------
    # Playwright function info
    # ------------------------------------------------------------------

    def _on_pw_func_selected(self, event=None):
        self._update_func_info()
        pw_func = self.pw_func_var.get()
        func_info = self._config.get("playwright_functions", {}).get(pw_func, {})
        params = func_info.get("params", [])
        # Auto-set needs_selector/needs_value based on params
        self.needs_selector_var.set("selector" in params)
        self.needs_value_var.set(
            any(p in params for p in ("value", "text", "key", "url", "timeout", "files", "expression"))
        )

    def _update_func_info(self):
        pw_func = self.pw_func_var.get()
        func_info = self._config.get("playwright_functions", {}).get(pw_func, {})
        if func_info:
            desc = func_info.get("description", "")
            params = ", ".join(func_info.get("params", []))
            opt = ", ".join(f"{k}:{v}" for k, v in func_info.get("optional_params", {}).items())
            info = f"{desc}  |  Params: {params}"
            if opt:
                info += f"  |  Optional: {opt}"
            self.func_info_label.config(text=info)
        else:
            self.func_info_label.config(text="")

    # ------------------------------------------------------------------
    # Code generation
    # ------------------------------------------------------------------

    def _generate_base_page_code(self):
        lines = [
            "from playwright.sync_api import Page, expect",
            "from utils.logger import log",
            "from config.config import Config",
            "",
            "",
            "class BasePage:",
            "    def __init__(self, page: Page):",
            "        self.page = page",
            "",
            "    def navigate(self, url=\"\"):",
            "        target_url = url if url else Config.get_base_url()",
            '        log.info(f"Dieu huong toi: {target_url}")',
            "        self.page.goto(target_url)",
            "",
        ]

        actions = self._config.get("actions", {})
        generated_methods = set()

        for key, info in actions.items():
            pw_method = info.get("playwright_method", "")
            method_name = pw_method.split(".")[-1] if pw_method else key
            needs_selector = info.get("needs_selector", False)
            needs_value = info.get("needs_value", False)
            assertion = info.get("assertion", "")
            log_msg = info.get("log_message", "")
            display = info.get("display_name", key)

            # Skip certain built-in methods or duplicates
            if method_name in generated_methods:
                continue
            if method_name in ("goto", "url"):
                continue

            generated_methods.add(method_name)

            # Build method signature
            sig_parts = ["self"]
            if needs_selector:
                sig_parts.append("selector: str")
            if needs_value:
                sig_parts.append("value: str")
            sig_parts.append('name: str = ""')

            func_def = f"    def {method_name}({', '.join(sig_parts)}):"
            lines.append(func_def)
            lines.append(f'        """Auto-generated: {display}"""')
            lines.append("        display_name = name if name else selector" if needs_selector else "        display_name = name")

            # Try/except wrapper for interaction actions
            if assertion:
                # Verification methods
                if assertion == "text_contains":
                    lines.append("        try:")
                    lines.append("            self.page.wait_for_selector(selector, state=\"attached\", timeout=5000)")
                    lines.append("            actual = self.page.inner_text(selector).strip()")
                    lines.append("        except Exception:")
                    lines.append("            actual = \"\"")
                    lines.append(f'        log.info(f"Kiem tra van ban: Ky vong chua \'{{value}}\', thuc te co \'{{actual}}\'")')
                    lines.append("        assert str(value).lower() in actual.lower(), \\")
                    lines.append(f"            f\"Loi noi dung: khong chua '{{value}}'\"")
                elif assertion == "is_visible":
                    lines.append("        try:")
                    lines.append("            self.page.wait_for_selector(selector, state=\"visible\", timeout=5000)")
                    lines.append("            result = self.page.is_visible(selector)")
                    lines.append("        except Exception:")
                    lines.append("            result = False")
                    lines.append(f'        log.info(f"Kiem tra hien thi: {{display_name}} -> {{result}}")')
                    lines.append("        assert result, f\"Loi hien thi: Khong tim thay phan tu '{display_name}'\"")
                elif assertion == "url_contains":
                    lines.append("        current_url = self.page.url")
                    lines.append(f'        log.info(f"Kiem tra URL chua: \'{{value}}\', thuc te: \'{{current_url}}\'")')
                    lines.append("        assert value in current_url, \\")
                    lines.append("            f\"Ky vong URL chua '{value}' nhung thuc te la '{current_url}'\"")
            else:
                # Interaction methods
                lines.append("        try:")
                if log_msg:
                    log_line = log_msg.replace("{name}", "{display_name}").replace("{value}", "{value}")
                    lines.append(f'            log.info(f"{log_line}")')

                # Generate Playwright call
                call_args = []
                if needs_selector:
                    call_args.append("selector")
                if needs_value:
                    if method_name == "wait_for_timeout":
                        call_args.append("int(value) if str(value).isdigit() else 2000")
                    elif method_name in ("fill", "type"):
                        call_args.append("str(value)")
                    elif method_name == "select_option":
                        call_args.append("str(value)")
                    else:
                        call_args.append("value")

                lines.append(f"            self.page.{method_name}({', '.join(call_args)})")
                lines.append("        except Exception as e:")
                lines.append(f'            log.error(f"Loi khi {display.lower()}: {{display_name}}: {{str(e)}}")')
                lines.append("            raise")

            lines.append("")

        # Add get_text and get_element_snapshot as utility methods
        lines.extend([
            "    def get_text(self, selector: str) -> str:",
            "        try:",
            "            self.page.wait_for_selector(selector, state=\"attached\", timeout=5000)",
            "            return self.page.inner_text(selector).strip()",
            "        except Exception as e:",
            '            log.error(f"Khong the lay text tu {selector}: {str(e)}")',
            '            return ""',
            "",
            "    def get_element_snapshot(self, selector: str) -> dict:",
            "        try:",
            '            self.page.wait_for_selector(selector, state="attached", timeout=3000)',
            '            info = self.page.evaluate(f"""',
            "                (sel) => {{",
            "                    const el = document.querySelector(sel);",
            "                    if (!el) return null;",
            "                    return {{",
            "                        tag: el.tagName.toLowerCase(),",
            '                        text: el.innerText || el.value || "",',
            "                        class: el.className,",
            "                        id: el.id,",
            "                        is_visible: el.offsetWidth > 0 && el.offsetHeight > 0",
            "                    }};",
            "                }}",
            '            """, selector)',
            "            if info:",
            "                return info",
            "            return {}",
            "        except Exception:",
            "            return {}",
            "",
            "    def wait_for_element(self, selector: str, timeout: int = 10000):",
            "        try:",
            "            self.page.wait_for_selector(selector, timeout=timeout)",
            "        except Exception as e:",
            '            log.error(f"Het thoi gian cho {selector}: {str(e)}")',
            "",
            "    def verify_url(self, expected_url: str):",
            "        current_url = self.page.url",
            "        assert expected_url in current_url, \\",
            "            f\"Ky vong URL chua '{expected_url}' nhung thuc te la '{current_url}'\"",
        ])

        return "\n".join(lines)

    def _generate_runner_code(self):
        lines = [
            "from pages.base_page import BasePage",
            "from utils.logger import log",
            "from utils.helpers import Helpers",
            "from config.config import Config",
            "from pathlib import Path",
            "",
            "",
            "class GenericRunner:",
            "    def __init__(self, page, site_name, page_id):",
            "        self.page = page",
            "        self.site_name = site_name",
            "        self.page_id = page_id",
            "        self.base_page = BasePage(page)",
            "",
            "        base_dir = Config.BASE_DIR",
            "",
            '        self.locators = Helpers.load_json_config(base_dir / "locators" / site_name / f"{page_id}.json")',
            '        self.workflow = Helpers.load_json_config(base_dir / "templates" / site_name / f"{page_id}_workflow.json")',
            "",
            "    def run_test(self, test_data: dict):",
            '        """Thuc thi toan bo kich ban dua tren mot dong du lieu tu Excel."""',
            "        if not self.locators or not self.workflow:",
            '            log.error(f"Khong the bat dau test: Thieu file cau hinh JSON cho {self.page_id}")',
            "            return False",
            "",
            "        try:",
            '            log.info(f"Bat dau kich ban: {self.page_id} cho site {self.site_name}")',
            "",
            '            target_url = self.workflow.get("url")',
            "            if target_url:",
            "                self.base_page.navigate(target_url)",
            "",
            '            steps = self.workflow.get("steps", [])',
            "            for step in steps:",
            "                self._execute_step(step, test_data)",
            "",
            '            log.info(f"Hoan thanh kich ban {self.page_id} thanh cong.")',
            "            return True",
            "",
            "        except Exception as e:",
            '            log.error(f"Kich ban dung dot ngot do loi: {str(e)}")',
            "            raise e",
            "",
            "    def _execute_step(self, step: dict, test_data: dict):",
            '        """Thuc thi mot buoc don le trong kich ban."""',
            '        step_id = step.get("id")',
            '        action = step.get("action")',
            '        data_key = step.get("data_key")',
            "",
            "        selector_info = self.locators.get(step_id, {})",
            '        selector = selector_info.get("selector")',
            '        step_name = selector_info.get("name", step_id)',
            "",
            '        value = test_data.get(data_key) if data_key in test_data else step.get("value", "")',
            '        log.info(f"Step \'{step_id}\' | data_key=\'{data_key}\' | value=\'{value}\'")',
            "",
        ]

        actions = self._config.get("actions", {})
        skip_selector_actions = set()

        # Build if/elif chain
        first = True
        for key, info in actions.items():
            needs_selector = info.get("needs_selector", False)
            needs_value = info.get("needs_value", False)
            assertion = info.get("assertion", "")
            pw_method = info.get("playwright_method", "")
            method_name = pw_method.split(".")[-1] if pw_method else key

            if not needs_selector:
                skip_selector_actions.add(key)

            prefix = "        if" if first else "        elif"
            first = False

            lines.append(f'{prefix} action == "{key}":')

            if assertion == "text_contains":
                lines.append("            snapshot = self.base_page.get_element_snapshot(selector)")
                lines.append('            actual_text = snapshot.get("text", "")')
                lines.append(f'            log.info(f"Kiem tra van ban: Ky vong chua \'{{value}}\', thuc te co \'{{actual_text}}\'")')
                lines.append("            if not value and actual_text.strip() != \"\":")
                lines.append("                raise AssertionError(")
                lines.append("                    f\"Step '{step_id}' khong co value (data_key='{data_key}') du thuc te co text: '{actual_text}'\"")
                lines.append("                )")
                lines.append("            assert str(value).lower() in actual_text.lower(), \\")
                lines.append("                f\"Loi noi dung: khong chua '{value}'\"")
            elif assertion == "is_visible":
                lines.append("            is_visible = self.base_page.is_visible(selector)")
                lines.append("            if not is_visible:")
                lines.append("                self.base_page.get_element_snapshot(selector)")
                lines.append("            assert is_visible, f\"Loi hien thi: Khong tim thay phan tu '{step_name}'\"")
            elif assertion == "url_contains":
                lines.append("            self.base_page.verify_url(value)")
            elif method_name == "wait_for_timeout":
                lines.append("            wait_time = int(value) if str(value).isdigit() else 2000")
                lines.append('            log.info(f"Cho trong {wait_time}ms...")')
                lines.append("            self.page.wait_for_timeout(wait_time)")
            elif method_name == "select_option":
                lines.append("            self.page.select_option(selector, str(value))")
                lines.append(f'            log.info(f"Da chon option \'{{value}}\' tai {{step_name}}")')
            elif method_name == "goto":
                lines.append("            self.base_page.navigate(value)")
            elif method_name == "screenshot":
                lines.append("            path = str(value) if value else f\"{self.page_id}_screenshot.png\"")
                lines.append("            self.page.screenshot(path=path)")
                lines.append('            log.info(f"Da chup man hinh: {path}")')
            elif needs_selector and needs_value:
                lines.append(f"            self.base_page.{method_name}(selector, value, step_name)")
            elif needs_selector:
                lines.append(f"            self.base_page.{method_name}(selector, step_name)")
            else:
                lines.append(f"            self.base_page.{method_name}(value, step_name)")

            lines.append("")

        # Add selector check before the if/elif chain
        skip_list = ", ".join(f'"{a}"' for a in skip_selector_actions)
        selector_check = f"        if not selector and action not in ({skip_list}):"
        # Insert selector check before the if/elif chain
        insert_idx = len(lines)
        for i, line in enumerate(lines):
            if line.strip().startswith('if action == ') or line.strip().startswith('elif action == '):
                insert_idx = i
                break

        check_lines = [
            f"        if not selector and action not in ({skip_list}):",
            '            log.warning(f"Bo qua buoc \'{step_id}\': Khong tim thay Selector.")',
            "            return",
            "",
        ]
        for j, cl in enumerate(check_lines):
            lines.insert(insert_idx + j, cl)

        return "\n".join(lines)

    def _preview_base_page(self):
        code = self._generate_base_page_code()
        self._set_code_preview(code)

    def _preview_runner(self):
        code = self._generate_runner_code()
        self._set_code_preview(code)

    def _write_code(self):
        proj_path = Path(self.shared["project_path"].get())
        if not proj_path.exists():
            messagebox.showerror("Loi", "Thu muc du an khong ton tai")
            return

        bp_path = proj_path / "pages" / "base_page.py"
        gr_path = proj_path / "core" / "generic_runner.py"

        if not messagebox.askyesno(
            "Xac nhan",
            f"Ghi de code vao:\n- {bp_path}\n- {gr_path}\n\nTiep tuc?"
        ):
            return

        bp_code = self._generate_base_page_code()
        gr_code = self._generate_runner_code()

        bp_path.parent.mkdir(parents=True, exist_ok=True)
        gr_path.parent.mkdir(parents=True, exist_ok=True)

        with open(bp_path, "w", encoding="utf-8") as f:
            f.write(bp_code + "\n")

        with open(gr_path, "w", encoding="utf-8") as f:
            f.write(gr_code + "\n")

        self._set_code_preview(
            f"Da ghi code thanh cong!\n\n"
            f"- {bp_path}\n"
            f"- {gr_path}\n\n"
            f"Luu y: Hay kiem tra code truoc khi chay test."
        )
        messagebox.showinfo("Thanh cong", "Da ghi code vao base_page.py va generic_runner.py")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_code_preview(self, text):
        self.code_preview.delete("1.0", tk.END)
        self.code_preview.insert("1.0", text)
