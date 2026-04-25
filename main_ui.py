import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import subprocess
import sys
import os
import json #sửa
import traceback
from pathlib import Path
from logic_manager import AutomationLogic

class AutomationGeneratorUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Automation Control Center - Hệ thống Generic")
        self.root.geometry("1100x950")
        
        self.logic = AutomationLogic()
        self.setup_ui()
        self.refresh_test_list()
        self.update_data_list() 
    def setup_ui(self):
        config_frame = ttk.LabelFrame(self.root, text=" 1. Cấu hình Dự án & Trang Web ", padding=10)
        config_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(config_frame, text="Thư mục dự án:").grid(row=0, column=0, sticky="w")
        self.project_path = tk.StringVar(value=str(self.logic.base_dir))
        self.project_entry = ttk.Entry(config_frame, textvariable=self.project_path, width=80)
        self.project_entry.grid(row=0, column=1, padx=5)
        ttk.Button(config_frame, text="Duyệt...", command=self.browse_project).grid(row=0, column=2)
        
        ttk.Label(config_frame, text="URL mục tiêu:").grid(row=1, column=0, sticky="w", pady=5)
        self.url_path = tk.StringVar()
        self.url_entry = ttk.Entry(config_frame, textvariable=self.url_path, width=80)
        self.url_entry.grid(row=1, column=1, padx=5)
        
        ttk.Label(config_frame, text="Page ID (VD: login):").grid(row=2, column=0, sticky="w")
        self.page_id_var = tk.StringVar(value="login")
        self.page_id_entry = ttk.Entry(config_frame, textvariable=self.page_id_var, width=30)
        self.page_id_entry.grid(row=2, column=1, sticky="w", padx=5)

        # --- Bổ sung nhập Browser ---
        ttk.Label(config_frame, text="Trình duyệt:").grid(row=2, column=2, sticky="w", padx=10)
        self.browser_var = tk.StringVar(value="chromium")
        self.browser_combo = ttk.Combobox(config_frame, textvariable=self.browser_var, width=15)
        self.browser_combo['values'] = ("chromium", "firefox", "webkit")
        self.browser_combo.grid(row=2, column=3, sticky="w", padx=5)

        # --- SECTION 2: ĐIỀU KHIỂN ---
        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.pack(fill="x")
        
        ttk.Button(control_frame, text="🔍 Quét trang web", command=self.start_scan).pack(side="left", padx=5)
        # ttk.Button(control_frame, text="💾 Lưu cấu hình", command=self.save_config).pack(side="left", padx=5) #xóa
        ttk.Button(control_frame, text="📍 Hiện Locator", command=self.show_locators).pack(side="left", padx=5) #sửa
        ttk.Button(control_frame, text="📝 Hiện Template", command=self.show_template).pack(side="left", padx=5) #sửa
        ttk.Button(control_frame, text="📂 Nhập Data Test (Excel)", command=self.import_data).pack(side="left", padx=5)

 
        elements_frame = ttk.LabelFrame(self.root, text=" 2. Các phần tử tìm thấy (Chọn để tạo kịch bản) ", padding=10)
        elements_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.tree = ttk.Treeview(elements_frame, columns=("Tag", "Text", "Selector", "Action", "DataKey"), show="headings")
        self.tree.heading("Tag", text="Thẻ")
        self.tree.heading("Text", text="Nội dung/ID")
        self.tree.heading("Selector", text="Selector (CSS/ID)")
        self.tree.heading("Action", text="Hành động (Template)")
        self.tree.heading("DataKey", text="Khóa dữ liệu (Excel)")
        
        self.tree.column("Tag", width=70)
        self.tree.column("Text", width=150)
        self.tree.column("Selector", width=250)
        self.tree.column("Action", width=120)
        self.tree.column("DataKey", width=120)
        
        self.tree.pack(fill="both", expand=True, side="left")
        
        scrollbar = ttk.Scrollbar(elements_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(fill="y", side="right")
        
        self.tree.bind("<Double-1>", self.on_tree_double_click)

        # --- SECTION 4: CHẠY TEST ---
        run_frame = ttk.LabelFrame(self.root, text=" 3. Thực thi Test Case ", padding=10)
        run_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(run_frame, text="Chọn file test:").grid(row=0, column=0, sticky="w")
        self.test_combo = ttk.Combobox(run_frame, width=40)
        self.test_combo.grid(row=0, column=1, padx=5, sticky="w")
        
        ttk.Label(run_frame, text="Dữ liệu test:").grid(row=0, column=2, sticky="w", padx=10)
        self.data_combo = ttk.Combobox(run_frame, width=30)
        self.data_combo.grid(row=0, column=3, padx=5, sticky="w")
        
        ttk.Label(run_frame, text="Sheet:").grid(row=0, column=4, sticky="w", padx=10)
        self.sheet_var = tk.StringVar(value="Sheet1")
        ttk.Entry(run_frame, textvariable=self.sheet_var, width=15).grid(row=0, column=5)
        
        self.run_btn = ttk.Button(run_frame, text="🚀 CHẠY TEST", command=self.run_test)
        self.run_btn.grid(row=0, column=6, padx=15)

        # --- SECTION 5: LOG ---
        log_frame = ttk.LabelFrame(self.root, text=" Nhật ký hệ thống ", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_text = tk.Text(log_frame, height=10, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 10))
        self.log_text.pack(fill="both", expand=True)

    def browse_project(self):
        path = filedialog.askdirectory()
        if path:
            self.project_path.set(path)
            self.refresh_test_list()

    def start_scan(self):
        url = self.url_path.get()
        if not url:
            messagebox.showwarning("Chú ý", "Vui lòng nhập URL")
            return
            
        self._append_log(f"🌐 Bắt đầu quét: {url}...")
        
        def run_scan():
            try:
                elements = self.logic.scan_url(url)
                self.root.after(0, lambda: self.update_tree(elements))
                self.root.after(0, lambda: self._append_log(f"✅ Đã tìm thấy {len(elements)} phần tử."))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Lỗi", str(e)))
        
        threading.Thread(target=run_scan, daemon=True).start()

    def update_tree(self, elements):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for el in elements:
            self.tree.insert("", "end", values=(
                el.get('action', ''),    # Tương ứng cột "Thẻ" hoặc "Hành động" tùy bạn sắp xếp
                el.get('name', ''),      # Tương ứng cột "Nội dung/ID"
                el.get('selector', ''),  # Tương ứng cột "Selector"
                el.get('action', ''),    # Tương ứng cột "Hành động (Template)"
                el.get('name', '').lower() # Tương ứng cột "Khóa dữ liệu (Excel)"
            ))

    def on_tree_double_click(self, event):
        item_id = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        
        if not item_id: return
        
        col_idx = int(column.replace("#", "")) - 1
        if col_idx < 3: return # Chỉ cho sửa Action và DataKey
        
        current_values = list(self.tree.item(item_id, "values"))
        
        # Tạo cửa sổ nhập liệu nhỏ
        dialog = tk.Toplevel(self.root)
        dialog.title("Chỉnh sửa")
        dialog.geometry("300x120")
        
        ttk.Label(dialog, text=f"Nhập giá trị mới cho {self.tree.heading(column)['text']}:").pack(pady=5)
        entry = ttk.Entry(dialog, width=30)
        entry.insert(0, current_values[col_idx])
        entry.pack(pady=5)
        entry.focus_set()
        
        def save():
            current_values[col_idx] = entry.get()
            self.tree.item(item_id, values=current_values)
            dialog.destroy()
            
        ttk.Button(dialog, text="OK", command=save).pack()


    def show_locators(self): #sửa
        """Lấy dữ liệu từ Treeview và hiển thị cửa sổ JSON Locator"""
        url = self.url_path.get()
        page_id = self.page_id_var.get()
        if not url or not page_id:
            messagebox.showwarning("Chú ý", "Vui lòng nhập URL và Page ID trước")
            return

        # Tạo dict locator từ treeview
        locators_data = {}
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            key = vals[4].upper() if vals[4] else vals[1].upper().replace(" ", "_")
            if not key: key = f"ELEMENT_{item}"
            
            locators_data[key] = {
                "selector": vals[2],
                "type": "info" if vals[3] == "verify_text" else "action"
            }
        
        self.open_json_editor("Chỉnh sửa Locators", locators_data, "locators")

    def show_template(self): #sửa
        """Lấy dữ liệu từ Treeview và hiển thị cửa sổ JSON Template"""
        url = self.url_path.get()
        page_id = self.page_id_var.get()
        if not url or not page_id:
            messagebox.showwarning("Chú ý", "Vui lòng nhập URL và Page ID trước")
            return

        steps = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            key = vals[4].upper() if vals[4] else vals[1].upper().replace(" ", "_")
            if not key: continue
            
            steps.append({
                "id": key,
                "action": vals[3],
                "data_key": vals[4]
            })
            
        template_data = {
            "page_id": page_id,
            "url": url,
            "steps": steps
        }
        
        self.open_json_editor("Chỉnh sửa Template", template_data, "templates")

    def open_json_editor(self, title, data, type_json): #sửa
        """Cửa sổ soạn thảo JSON chung"""
        editor_win = tk.Toplevel(self.root)
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
                
                # Gọi logic để lưu file
                proj_path = self.project_path.get()
                url = self.url_path.get()
                page_id = self.page_id_var.get()
                
                if type_json == "locators":
                    self.logic.save_locator_json(proj_path, url, page_id, updated_data)
                else:
                    self.logic.save_template_json(proj_path, url, page_id, updated_data)
                
                messagebox.showinfo("Thành công", f"Đã lưu {type_json} thành công!")
                editor_win.destroy()
            except Exception as e:
                messagebox.showerror("Lỗi JSON", f"Định dạng JSON không hợp lệ: {str(e)}")
                
        btn_frame = ttk.Frame(editor_win)
        btn_frame.pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="💾 Lưu lại", command=save_json).pack(side="right", padx=10)
        ttk.Button(btn_frame, text="Đóng", command=editor_win.destroy).pack(side="right")

    def import_data(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if file_path:
            url = self.url_path.get()
            if not url:
                messagebox.showwarning("Chú ý", "Vui lòng nhập URL trước")
                return
            
            new_name = self.logic.import_test_data(self.project_path.get(), url, file_path)
            self._append_log(f"📥 Đã nhập file dữ liệu: {new_name}")
            self.update_data_list()

    def update_data_list(self):
        try:
            url = self.url_path.get()
            files = self.logic.get_data_files(self.project_path.get(), url)
            self.data_combo['values'] = files
            if files: self.data_combo.set(files[0])
        except:
            pass

    def refresh_test_list(self):
        p = Path(self.project_path.get()) / "tests"
        if p.exists():
            tests = [str(f.relative_to(self.project_path.get())) for f in p.glob("test_*.py")]
            self.test_combo['values'] = tests
            if tests: self.test_combo.set(tests[0])

    def _append_log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def run_test(self):
        test_file = self.test_combo.get()
        data_file = self.data_combo.get()
        sheet_name = self.sheet_var.get()
        page_id = self.page_id_var.get()
 
        
        if not test_file:
            messagebox.showwarning("Chú ý", "Vui lòng chọn file test")
            return
            
        self.run_btn.config(state="disabled")
        self.log_text.delete(1.0, tk.END)
        self._append_log(f"🚀 Đang khởi chạy: {test_file}...")

        def run():
            # Sử dụng sys.executable để lấy đúng đường dẫn python đang chạy
            python_exe = sys.executable
            proj_path = self.project_path.get()
            
            # Lệnh chạy pytest
            cmd = [python_exe, "-m", "pytest", test_file, "-v", "-s"]
            
            # Thiết lập biến môi trường để truyền tham số vào script test
            env = os.environ.copy()
            env["PYTHONPATH"] = proj_path
            env["BASE_URL"] = self.url_path.get()
            env["SELECTED_TEST_DATA"] = data_file
            env["SHEET_NAME"] = sheet_name
            env["PAGE_ID"] = page_id
            env["BROWSER"] = self.browser_var.get()
            
            # Đảm bảo bảng mã chuẩn để không bị lỗi hiển thị tiếng Việt
            env.update({"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"})


            try:
                # Chạy lệnh với bộ biến môi trường (env) đã cập nhật
                process = subprocess.Popen(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT, 
                    text=True, 
                    encoding="utf-8", 
                    env=env
                )
                
                if process.stdout:
                    for line in process.stdout:
                        self.root.after(0, lambda l=line: self._append_log(l))
                process.wait()
                self.root.after(0, lambda: self._append_log("\n✅ Hoàn thành lượt chạy.\n"))
            except Exception:
                err = traceback.format_exc()
                self.root.after(0, lambda m=err: self._append_log(f"\n❌ Lỗi hệ thống:\n{m}\n"))
            finally:
                self.root.after(0, lambda: self.run_btn.config(state="normal"))

        threading.Thread(target=run, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = AutomationGeneratorUI(root)
    root.mainloop()