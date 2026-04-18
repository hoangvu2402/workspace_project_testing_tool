import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import subprocess
import sys
import os
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
        self.update_data_list() # Cập nhật danh sách data test ngay khi khởi động
        
    def setup_ui(self):
        # --- SECTION 1: CẤU HÌNH ---
        config_frame = ttk.LabelFrame(self.root, text=" 1. Cấu hình Dự án & Trang Web ", padding=10)
        config_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(config_frame, text="Thư mục dự án:").grid(row=0, column=0, sticky="w")
        self.project_path = tk.StringVar(value=str(self.logic.base_dir))
        self.project_entry = ttk.Entry(config_frame, textvariable=self.project_path, width=80)
        self.project_entry.grid(row=0, column=1, padx=5)
        ttk.Button(config_frame, text="Duyệt...", command=self.browse_folder).grid(row=0, column=2)
        
        ttk.Label(config_frame, text="Tên trang (ID):").grid(row=1, column=0, sticky="w", pady=5)
        self.page_id = tk.StringVar(value="login")
        ttk.Entry(config_frame, textvariable=self.page_id, width=30).grid(row=1, column=1, sticky="w", padx=5)
        
        ttk.Label(config_frame, text="URL mục tiêu:").grid(row=2, column=0, sticky="w")
        self.target_url_var = tk.StringVar()
        self.url_entry = ttk.Entry(config_frame, textvariable=self.target_url_var, width=80)
        self.url_entry.grid(row=2, column=1, padx=5)
        
        # Khi người dùng nhập URL xong và nhấn Tab hoặc chuyển focus, cập nhật danh sách Data
        self.url_entry.bind("<FocusOut>", lambda e: self.update_data_list())

        # --- SECTION 2: DANH SÁCH PHẦN TỬ ---
        list_frame = ttk.LabelFrame(self.root, text=" 2. Danh sách phần tử & Dữ liệu test ", padding=10)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        columns = ("name", "type", "selector", "action_type")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col.replace('_', ' ').title())
        
        self.tree.column("name", width=200)
        self.tree.column("type", width=80)
        self.tree.column("selector", width=400)
        self.tree.column("action_type", width=120)

        self.tree.bind("<Double-1>", self.on_double_click)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="top", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y", in_=self.tree)

        edit_btn_frame = ttk.Frame(list_frame, padding=5)
        edit_btn_frame.pack(fill="x")
        
        ttk.Button(edit_btn_frame, text="🔍 QUÉT TRANG", command=self.handle_scan).pack(side="left", padx=5)
        ttk.Button(edit_btn_frame, text="📁 IMPORT DATA (XLSX)", command=self.handle_import_data).pack(side="left", padx=5)
        ttk.Button(edit_btn_frame, text="➕ Thêm dòng", command=self.add_manual).pack(side="left", padx=5)
        ttk.Button(edit_btn_frame, text="🗑️ Xóa dòng", command=self.delete_selected).pack(side="left", padx=5)
        ttk.Button(edit_btn_frame, text="▲ Up", command=self.move_up).pack(side="left", padx=5)
        ttk.Button(edit_btn_frame, text="▼ Down", command=self.move_down).pack(side="left", padx=5)
        ttk.Button(edit_btn_frame, text="💾 LƯU CẤU HÌNH", command=self.handle_save).pack(side="right", padx=5)





        # --- SECTION 3: THỰC THI ---
        run_frame = ttk.LabelFrame(self.root, text=" 3. Chạy thử nghiệm kịch bản ", padding=10)
        run_frame.pack(fill="x", padx=10, pady=5)
        
        run_controls = ttk.Frame(run_frame)
        run_controls.pack(fill="x", pady=5)

        # 1. Chọn Browser (Thêm mới)
        ttk.Label(run_controls, text="Browser:").pack(side="left", padx=5)
        self.browser_combo = ttk.Combobox(run_controls, values=["chromium", "firefox", "webkit"], width=10)
        self.browser_combo.set("chromium")
        self.browser_combo.pack(side="left", padx=5)

        # 2. Checkbox Headless (Thêm mới)
        self.headless_var = tk.BooleanVar(value=False)
        self.headless_check = ttk.Checkbutton(run_controls, text="Headless", variable=self.headless_var)
        self.headless_check.pack(side="left", padx=5)

        ttk.Label(run_controls, text="Chọn Script:").pack(side="left", padx=5)
        self.test_file_var = tk.StringVar()
        self.test_combo = ttk.Combobox(run_controls, textvariable=self.test_file_var, width=30)
        self.test_combo.pack(side="left", padx=5)

        ttk.Label(run_controls, text="Chọn Data Test:").pack(side="left", padx=5)
        self.data_file_var = tk.StringVar()
        self.data_combo = ttk.Combobox(run_controls, textvariable=self.data_file_var, width=30)
        self.data_combo.pack(side="left", padx=5)

        ttk.Label(run_controls, text="Sheet:").pack(side="left", padx=5)
        self.sheet_combo = ttk.Combobox(run_controls, values=["Sheet1"], width=10)
        self.sheet_combo.set("Sheet1")
        self.sheet_combo.pack(side="left", padx=5)
        
        self.run_btn = ttk.Button(run_controls, text="🚀 CHẠY TEST", command=self.execute_pytest)
        self.run_btn.pack(side="right", padx=5)

        self.log_text = tk.Text(run_frame, height=12, bg="#1e1e1e", fg="#00ff00", font=("Consolas", 10))
        self.log_text.pack(fill="x", pady=5)


    #--

    def move_up(self):
        leaves = self.tree.selection()
        for row in leaves:
            index = self.tree.index(row)
            if index > 0:
                self.tree.move(row, self.tree.parent(row), index - 1)

    def move_down(self):
        leaves = self.tree.selection()
        # Phải đảo ngược danh sách chọn để tránh lỗi index khi di chuyển nhiều dòng
        for row in reversed(leaves):
            index = self.tree.index(row)
            if index < len(self.tree.get_children()) - 1:
                self.tree.move(row, self.tree.parent(row), index + 1)
                
    def on_double_click(self, event):
        """Xử lý khi người dùng nhấn đúp chuột vào một ô"""
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        column = self.tree.identify_column(event.x) # Ví dụ: "#1"
        item = self.tree.identify_row(event.y)      # Ví dụ: "I001"
        
        # Lấy tọa độ của ô để đặt Entry đè lên
        x, y, width, height = self.tree.bbox(item, column)
        
        # Lấy giá trị hiện tại
        column_index = int(column[1:]) - 1
        current_values = list(self.tree.item(item, "values"))
        current_value = current_values[column_index]

        # Tạo Entry tạm thời
        edit_entry = ttk.Entry(self.tree)
        edit_entry.insert(0, current_value)
        edit_entry.select_range(0, tk.END)
        edit_entry.focus_set()

        # Đặt vị trí Entry đúng vào ô đã click
        edit_entry.place(x=x, y=y, width=width, height=height)

        def save_edit(event=None):
            new_value = edit_entry.get()
            current_values[column_index] = new_value
            self.tree.item(item, values=tuple(current_values))
            edit_entry.destroy()

        # Bind sự kiện khi nhấn Enter hoặc mất focus thì lưu lại
        edit_entry.bind("<Return>", save_edit)
        edit_entry.bind("<FocusOut>", save_edit)
        edit_entry.bind("<Escape>", lambda e: edit_entry.destroy())
    #//
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder: 
            self.project_path.set(folder)
            self.update_data_list()

    def update_data_list(self):
        """Cập nhật danh sách các file excel có sẵn cho domain hiện tại"""
        try:
            files = self.logic.get_data_files(self.project_path.get(), self.target_url_var.get())
            self.data_combo['values'] = files
            if files:
                self.data_combo.current(0)
            else:
                self.data_file_var.set("")
        except:
            pass

    def handle_import_data(self):
        """Mở hộp thoại chọn file XLSX và copy vào thư mục test_data của domain"""
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if file_path:
            try:
                name = self.logic.import_test_data(self.project_path.get(), self.target_url_var.get(), file_path)
                messagebox.showinfo("Thành công", f"Đã import file: {name}")
                self.update_data_list() # Làm mới danh sách combobox
                self.data_file_var.set(name) # Chọn luôn file vừa import
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể import: {str(e)}")

    def handle_scan(self):
        url = self.target_url_var.get()
        def run_scan():
            try:
                elements = self.logic.scan_url(url)
                self.root.after(0, lambda: self._display_elements(elements))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Lỗi Quét", str(e)))

        threading.Thread(target=run_scan, daemon=True).start()

    def _display_elements(self, elements):
        for item in self.tree.get_children(): self.tree.delete(item)
        for el in elements:
            self.tree.insert("", "end", values=(el['name'], el['type'], el['selector'], el['action']))
        messagebox.showinfo("Scanner", f"Đã quét xong {len(elements)} phần tử!")

    def handle_save(self):
        try:
            rows = [self.tree.item(child)["values"] for child in self.tree.get_children()]
            site_folder = self.logic.save_configuration(
                self.project_path.get(), 
                self.target_url_var.get(), 
                self.page_id.get(), 
                rows
            )
            messagebox.showinfo("Thành công", f"Đã lưu vào thư mục site: {site_folder}")
        except Exception as e:
            messagebox.showerror("Lỗi Lưu", str(e))

    def add_manual(self):
        self.tree.insert("", "end", values=("NEW_ELEMENT", "Action", "#id", "click"))

    def delete_selected(self):
        for item in self.tree.selection(): self.tree.delete(item)

    def refresh_test_list(self):
        """Lấy danh sách các file test hiện có trong thư mục tests"""
        p_path = Path(self.project_path.get())
        test_dir = p_path / "tests"
        if test_dir.exists():
            scripts = [str(p.relative_to(p_path)) for p in test_dir.glob("test_*.py")]
            self.test_combo['values'] = scripts
            if scripts: self.test_combo.current(0)
        else:
            self.test_combo['values'] = ["tests/test_main.py"]
            self.test_combo.set("tests/test_main.py")

    def _append_log(self, text):
        self.log_text.insert(tk.END, text)
        self.log_text.see(tk.END)

    def execute_pytest(self):
        test_file = self.test_file_var.get()
        data_file = self.data_file_var.get()
        target_url = self.target_url_var.get()      # Lấy URL từ ô nhập liệu

        
        browser = self.browser_combo.get()    # Lấy trình duyệt (chrome/firefox...)
        headless = self.headless_var.get()    # Lấy trạng thái ẩn/hiện trình duyệt
        sheet_name = self.sheet_combo.get()   # Lấy tên sheet từ combo
        page_id = self.page_id.get()              # Lấy page_id từ ô nhập liệu
        
        if not test_file:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn script test!")
            return
        
        self.run_btn.config(state="disabled")
        self.log_text.delete(1.0, tk.END)
        self._append_log(f"🚀 Chạy test: {test_file}\n📊 Data: {data_file if data_file else 'Không sử dụng'}\n" + "-"*50 + "\n")

        def run():
            cmd = self.logic.get_pytest_command(test_file)
            env = os.environ.copy()
            
            # 2. ÉP Pytest sử dụng các thông số mới bằng cách ghi đè biến môi trường
            # Các biến này phải khớp với cách code test của bạn đang đọc (thường là trong config.py)
            env["BASE_URL"] = target_url
            env["BROWSER"] = browser
            env["HEADLESS"] = str(headless)
            env["SELECTED_TEST_DATA"] = data_file
            env["SHEET_NAME"] = sheet_name
            env["PAGE_ID"] = page_id
            
            
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
    style = ttk.Style()
    style.theme_use('clam')
    app = AutomationGeneratorUI(root)
    root.mainloop()