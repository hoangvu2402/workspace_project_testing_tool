import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
import subprocess
import threading
import sys
import locale

class AutomationGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Automation Control Center - Dự án Dona1")
        self.root.geometry("1000x900")
        
        # Cấu hình đường dẫn
        self.base_dir = Path(__file__).resolve().parent
        
        self.setup_ui()
        # Tự động quét file test khi khởi động
        self.refresh_test_list()
        
    def setup_ui(self):
        # --- SECTION 1: CẤU HÌNH ---
        config_frame = ttk.LabelFrame(self.root, text=" 1. Cấu hình Dự án & Môi trường ", padding=10)
        config_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(config_frame, text="Thư mục dự án:").grid(row=0, column=0, sticky="w")
        self.project_path = tk.StringVar(value=str(self.base_dir))
        self.project_entry = ttk.Entry(config_frame, textvariable=self.project_path, width=80)
        self.project_entry.grid(row=0, column=1, padx=5)
        ttk.Button(config_frame, text="Duyệt...", command=self.browse_folder).grid(row=0, column=2)
        
        ttk.Label(config_frame, text="Tên Page Class:").grid(row=1, column=0, sticky="w", pady=5)
        self.page_name = tk.StringVar(value="Inventory")
        ttk.Entry(config_frame, textvariable=self.page_name, width=30).grid(row=1, column=1, sticky="w", padx=5)
        
        ttk.Label(config_frame, text="Target URL:").grid(row=2, column=0, sticky="w")
        self.target_url = tk.StringVar(value="https://www.saucedemo.com")
        ttk.Entry(config_frame, textvariable=self.target_url, width=80).grid(row=2, column=1, padx=5)

        # --- SECTION 2: DANH SÁCH ELEMENT ---
        list_frame = ttk.LabelFrame(self.root, text=" 2. Danh sách phần tử (Nhấp đúp để sửa dòng) ", padding=10)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        columns = ("name", "type", "selector")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        self.tree.heading("name", text="Tên Biến (VD: LOGIN_BTN)")
        self.tree.heading("type", text="Loại (input/button/select)")
        self.tree.heading("selector", text="Selector (id=... / css=...)")
        self.tree.column("name", width=250)
        self.tree.column("type", width=150)
        self.tree.column("selector", width=450)
        
        self.tree.bind("<Double-1>", self.on_double_click)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        edit_btn_frame = ttk.Frame(self.root, padding=5)
        edit_btn_frame.pack(fill="x", padx=10)
        
        ttk.Button(edit_btn_frame, text="🔍 QUÉT TRANG TỰ ĐỘNG", command=self.scan_page).pack(side="left", padx=5)
        ttk.Button(edit_btn_frame, text="➕ Thêm dòng mới", command=self.add_manual).pack(side="left", padx=5)
        ttk.Button(edit_btn_frame, text="🗑️ Xóa dòng chọn", command=self.delete_selected).pack(side="left", padx=5)
        ttk.Button(edit_btn_frame, text="🔥 SINH CODE & CẬP NHẬT DỰ ÁN", command=self.generate_files).pack(side="right", padx=5)

        # --- SECTION 3: TRÌNH CHẠY TEST ---
        run_frame = ttk.LabelFrame(self.root, text=" 3. Thực thi Kiểm thử (Run Pytest) ", padding=10)
        run_frame.pack(fill="x", padx=10, pady=5)
        
        run_control_frame = ttk.Frame(run_frame)
        run_control_frame.pack(fill="x")
        
        ttk.Label(run_control_frame, text="Gợi ý file test:").pack(side="left")
        self.test_file_var = tk.StringVar()
        self.test_combo = ttk.Combobox(run_control_frame, textvariable=self.test_file_var, width=50, state="readonly")
        self.test_combo.pack(side="left", padx=5)
        
        ttk.Button(run_control_frame, text="🔄 Làm mới", command=self.refresh_test_list).pack(side="left", padx=2)
        ttk.Button(run_control_frame, text="📂 Chọn file khác...", command=self.browse_test_file).pack(side="left", padx=2)
        
        self.run_btn = ttk.Button(run_control_frame, text="🚀 CHẠY TEST NGAY", command=self.run_pytest_thread)
        self.run_btn.pack(side="right", padx=5)

        # Cửa sổ hiển thị Log
        self.log_text = tk.Text(run_frame, height=12, bg="#1e1e1e", fg="#00ff00", font=("Consolas", 10))
        self.log_text.pack(fill="x", pady=5)

    def refresh_test_list(self):
        """Quét thư mục dự án để tìm các file test (bắt đầu bằng test_)."""
        p_path = Path(self.project_path.get())
        test_files = []
        search_dirs = [p_path / "tests", p_path]
        
        for d in search_dirs:
            if d.exists() and d.is_dir():
                for file in d.glob("test_*.py"):
                    test_files.append(str(file.relative_to(p_path) if file.is_relative_to(p_path) else file))
        
        if test_files:
            self.test_combo['values'] = test_files
            self.test_combo.current(0)
        else:
            self.test_combo['values'] = ["Không tìm thấy file test_*.py"]
            self.test_combo.set("Không tìm thấy file test_*.py")

    def on_double_click(self, event):
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        if not item or not column: return
        
        col_idx = int(column.replace("#", "")) - 1
        x, y, w, h = self.tree.bbox(item, column)
        
        entry = ttk.Entry(self.root)
        entry.insert(0, self.tree.item(item)['values'][col_idx])
        entry.place(x=x + self.tree.winfo_x() + 10, y=y + self.tree.winfo_y() + 165, width=w, height=h)
        
        def save_edit(event=None):
            new_val = entry.get()
            vals = list(self.tree.item(item)['values'])
            vals[col_idx] = new_val
            self.tree.item(item, values=vals)
            entry.destroy()
            
        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", lambda e: entry.destroy())
        entry.focus_set()

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder: 
            self.project_path.set(folder)
            self.refresh_test_list()

    def browse_test_file(self):
        file = filedialog.askopenfilename(initialdir=self.project_path.get(), title="Chọn file test", filetypes=[("Python files", "*.py")])
        if file:
            current_vals = list(self.test_combo['values'])
            if file not in current_vals:
                current_vals.append(file)
                self.test_combo['values'] = current_vals
            self.test_file_var.set(file)

    def scan_page(self):
        url = self.target_url.get()
        if not url: return messagebox.showwarning("Cảnh báo", "Vui lòng nhập URL!")
        
        try:
            for item in self.tree.get_children(): self.tree.delete(item)
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, timeout=60000)
                elements = page.evaluate("""
                    () => {
                        const results = [];
                        document.querySelectorAll('input, button, select, a.btn').forEach(el => {
                            let name = el.id || el.name || el.innerText.trim().toUpperCase().replace(/\\s+/g, '_') || 'ELEMENT';
                            let type = el.tagName.toLowerCase();
                            if (el.classList.contains('btn')) type = 'button';
                            let selector = el.id ? `id=${el.id}` : (el.name ? `name=${el.name}` : '');
                            if (name && selector && name.length > 1) {
                                results.push({ name: name.substring(0, 30), type: type, selector: selector });
                            }
                        });
                        return results;
                    }
                """)
                browser.close()
                for el in elements:
                    self.tree.insert("", "end", values=(el['name'], el['type'], el['selector']))
            messagebox.showinfo("Thành công", f"Đã tìm thấy {len(elements)} phần tử!")
        except Exception as e: messagebox.showerror("Lỗi Playwright", str(e))

    def add_manual(self):
        self.tree.insert("", "end", values=("NEW_VAR", "input", "css=..."))

    def delete_selected(self):
        for item in self.tree.selection(): self.tree.delete(item)

    def generate_files(self):
        p_path = Path(self.project_path.get())
        p_name = self.page_name.get()
        if not p_name: return messagebox.showerror("Lỗi", "Nhập tên Page!")
        
        p_name_lower = p_name.lower()
        loc_content = f"class {p_name}Locators:\n"
        page_content = f"from pages.base_page import BasePage\nfrom locators.{p_name_lower}_locators import {p_name}Locators\n\nclass {p_name}Page(BasePage):\n    def execute_workflow(self, data):\n"
        
        for child in self.tree.get_children():
            name, p_type, selector = self.tree.item(child)["values"]
            var_name = str(name).upper().replace('-', '_').replace(' ', '_')
            loc_content += f"    {var_name} = \"{selector}\"\n"
            if p_type == 'input':
                page_content += f"        self.fill({p_name}Locators.{var_name}, data.get('{var_name.lower()}'))\n"
            elif p_type == 'button':
                page_content += f"        self.click({p_name}Locators.{var_name})\n"

        env_content = f"BASE_URL={self.target_url.get()}\nBROWSER=chromium\nHEADLESS=False\n"

        try:
            (p_path / "locators").mkdir(exist_ok=True)
            (p_path / "pages").mkdir(exist_ok=True)
            with open(p_path / "locators" / f"{p_name_lower}_locators.py", "w", encoding="utf-8") as f: f.write(loc_content)
            with open(p_path / "pages" / f"{p_name_lower}_page.py", "w", encoding="utf-8") as f: f.write(page_content)
            with open(p_path / ".env", "w", encoding="utf-8") as f: f.write(env_content)
            messagebox.showinfo("Hoàn tất", "Đã cập nhật Code và File .env!")
            self.refresh_test_list()
        except Exception as e: messagebox.showerror("Lỗi", str(e))

    def run_pytest_thread(self):
        test_file = self.test_file_var.get()
        if not test_file or "Không tìm thấy" in test_file: 
            return messagebox.showwarning("Cảnh báo", "Hãy chọn file test hợp lệ!")
        
        p_path = Path(self.project_path.get())
        full_test_path = p_path / test_file if not os.path.isabs(test_file) else Path(test_file)

        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, f"🚀 Bắt đầu chạy test: {full_test_path}\n")
        self.run_btn.config(state="disabled")
        
        thread = threading.Thread(target=self.execute_pytest, args=(str(full_test_path),))
        thread.start()

    def execute_pytest(self, test_file):
        python_exe = sys.executable
        # Tự động lấy encoding của hệ thống (Windows thường là cp1252 hoặc utf-8)
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1" 
        
        try:
            process = subprocess.Popen(
                [python_exe, "-m", "pytest", test_file, "-v", "-s"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8', # Đổi từ sys_encoding sang utf-8 để khớp với env mới
                errors='replace',
                env=env # Truyền môi trường đã sửa vào đây
            )
            
            if process.stdout:
                for line in process.stdout:
                    self.log_text.insert(tk.END, line)
                    self.log_text.see(tk.END)
                
            process.wait()
            self.log_text.insert(tk.END, "\n✅ Hoàn thành lượt chạy test.")
        except Exception as e:
            self.log_text.insert(tk.END, f"\n❌ Lỗi thực thi: {str(e)}")
        finally:
            self.run_btn.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use('clam') 
    app = AutomationGeneratorApp(root)
    root.mainloop()