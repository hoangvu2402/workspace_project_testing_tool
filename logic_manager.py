import os
import json
import re
import subprocess
import sys
import shutil
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

class AutomationLogic:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent

    def get_site_folder_name(self, url):
        """Trích xuất tên thư mục từ domain của URL"""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.replace('.', '_') if parsed_url.netloc else "unknown_site"
        return re.sub(r'[\\/*?:"<>|]', "", domain)

    def scan_url(self, url, browser_name="chromium"):
        """Thực hiện quét trang web bằng Playwright và trả về danh sách phần tử bao gồm cả các thẻ rỗng"""
        if not url:
            raise ValueError("URL không được để trống")

        with sync_playwright() as p:
            browser_type = getattr(p, browser_name, p.chromium)
            browser = browser_type.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=60000)
            
            # Trong file logic_manager.txt, thay đổi đoạn evaluate trong scan_url:

            elements = page.evaluate(r"""
                () => {
                    const results = [];
                    const selectors = 'body, div, section, input, button, select, textarea, h1, h2, h3, h4, h5, h6, span, p, a, label';
                    
                    // Hàm phụ để lấy selector rút gọn của một phần tử
                    const getSimpleSelector = (el) => {
                        if (el.id) return `#${el.id}`;
                        if (el.getAttribute('data-test')) return `[data-test="${el.getAttribute('data-test')}"]`;
                        if (el.className && typeof el.className === 'string' && el.className.trim() !== '') {
                            return '.' + el.className.trim().split(/\s+/)[0];
                        }
                        return el.tagName.toLowerCase();
                    };

                    document.querySelectorAll(selectors).forEach(el => {
                        let tagName = el.tagName.toLowerCase();
                        if (['script', 'style', 'noscript', 'meta', 'link'].includes(tagName)) return;

                        let selector = '';
                        const dataTest = el.getAttribute('data-test');
                        const nameAttr = el.getAttribute('name');                                 

                        // 1. Ưu tiên ID
                        if (el.id) {
                            selector = `#${el.id}`;
                        } 
                        // 2. Ưu tiên data-test
                        else if (dataTest) {
                            selector = `[data-test="${dataTest}"]`;
                        } 
                        // 2. Ưu tiên name
                        else if (nameAttr) {
                            selector = `[name="${nameAttr}"]`;
                        }
                        else {
                            // Lấy thông tin 2 cấp cha
                            let p1 = el.parentElement;
                            let p2 = p1 ? p1.parentElement : null;
                            let prefix = "";
                            if (p2) prefix += getSimpleSelector(p2) + " > ";
                            if (p1) prefix += getSimpleSelector(p1) + " > ";

                            // 3. Ưu tiên Class (có 2 cấp cha)
                            if (el.className && typeof el.className === 'string' && el.className.trim() !== '') {
                                const classes = el.className.trim().split(/\s+/).filter(c => c && !c.includes(':')).join('.');
                                selector = prefix + (classes ? `.${classes}` : tagName);
                            } 
                            // 4. Ưu tiên Thẻ (có 2 cấp cha)
                            else {
                                selector = prefix + tagName;
                            }
                        }

                        // ... (giữ nguyên phần logic xử lý nameCandidate, action, is_info bên dưới) [cite: 9, 10, 12, 14, 15]
                        let innerTxt = el.innerText ? el.innerText.split('\n')[0].trim().substring(0, 20) : '';
                        let nameCandidate = el.id || dataTest || el.getAttribute('name') || innerTxt || tagName;
                        let name = nameCandidate.toUpperCase().split(/[^A-Z0-9]+/).filter(x => x).join('_');
                        if (!name) name = tagName.toUpperCase() + '_ELEMENT';

                        let action = 'click';
                        let is_info = false;
                        if (['input', 'textarea'].includes(tagName)) {
                            action = 'fill';
                        } else if (tagName === 'select') {
                            action = 'select';
                        } else {
                            if (!['button', 'a'].includes(tagName)) {
                                action = 'verify_text';
                                is_info = true;
                            }
                        }
                        if (el.type === 'password') action = 'fill_password';

                        if (selector && selector !== '.') {
                            results.push({ 
                                name: name.substring(0, 50),
                                type: is_info ? 'Info' : 'Action',
                                selector: selector,
                                action: action
                            });
                        }
                    });
                    // ... (giữ nguyên phần filter trùng lặp) [cite: 19, 20]
                    const seen = new Set();
                    return results.filter(item => {
                        const duplicate = seen.has(item.selector);
                        seen.add(item.selector);
                        return !duplicate;
                    });
                }
            """)
            browser.close()
            return elements

    # def save_configuration(self, project_path, target_url, page_id, data_rows):
        
    #     p_path = Path(project_path)
    #     site_folder_name = self.get_site_folder_name(target_url)

    #     locators = {}
    #     workflow = []
        
    #     for row in data_rows:
    #         name, p_type, selector, action = row
    #         locators[name] = {"selector": selector, "type": p_type.lower()}
            
    #         workflow.append({"id": name, "action": action, "data_key": name.lower()})

    #     # Lưu Locators
    #     loc_site_dir = p_path / "locators" / site_folder_name
    #     loc_site_dir.mkdir(parents=True, exist_ok=True)
    #     with open(loc_site_dir / f"{page_id}.json", "w", encoding="utf-8") as f:
    #         json.dump(locators, f, indent=4, ensure_ascii=False)
            
    #     # Lưu Workflow
    #     tmpl_site_dir = p_path / "templates" / site_folder_name
    #     tmpl_site_dir.mkdir(parents=True, exist_ok=True)
    #     with open(tmpl_site_dir / f"{page_id}_workflow.json", "w", encoding="utf-8") as f:
    #         json.dump({"page_id": page_id, "url": target_url, "steps": workflow}, f, indent=4, ensure_ascii=False)
        
    #     return site_folder_name

        # --- HÀM LƯU JSON MỚI --- #sửa
    def save_locator_json(self, project_path, target_url, page_id, data): #sửa
        """Lưu file locator JSON"""
        p_path = Path(project_path)
        site_folder = self.get_site_folder_name(target_url)
        loc_dir = p_path / "locators" / site_folder
        loc_dir.mkdir(parents=True, exist_ok=True)
        
        with open(loc_dir / f"{page_id}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def save_template_json(self, project_path, target_url, page_id, data): #sửa
        """Lưu file template JSON"""
        p_path = Path(project_path)
        site_folder = self.get_site_folder_name(target_url)
        tmpl_dir = p_path / "templates" / site_folder
        tmpl_dir.mkdir(parents=True, exist_ok=True)
        
        with open(tmpl_dir / f"{page_id}_workflow.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def import_test_data(self, project_path, target_url, source_file_path):
        """Sao chép file XLSX vào thư mục test_data của dự án"""
        p_path = Path(project_path)
        site_folder = self.get_site_folder_name(target_url)
        dest_dir = p_path / "test_data" / site_folder
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        file_name = Path(source_file_path).name
        dest_path = dest_dir / file_name
        shutil.copy2(source_file_path, dest_path)
        return file_name

    def get_data_files(self, project_path, target_url):
        """Lấy danh sách các file dữ liệu test cho trang web hiện tại"""
        p_path = Path(project_path)
        site_folder = self.get_site_folder_name(target_url)
        data_dir = p_path / "test_data" / site_folder
        
        if not data_dir.exists():
            return []
        
        return [f.name for f in data_dir.glob("*.xlsx")]

    def get_template_files(self, project_path):
        """List all template workflow JSON files across all sites."""
        p_path = Path(project_path) / "templates"
        if not p_path.exists():
            return []
        results = []
        for f in sorted(p_path.rglob("*_workflow.json")):
            rel = f.relative_to(p_path)
            results.append(str(rel))
        return results

    def get_all_data_files(self, project_path):
        """List all Excel data files across all sites."""
        p_path = Path(project_path) / "test_data"
        if not p_path.exists():
            return []
        results = []
        for f in sorted(p_path.rglob("*.xlsx")):
            rel = f.relative_to(p_path)
            results.append(str(rel))
        return results

    def get_template_info(self, project_path, template_rel_path):
        """Read a template JSON and return its content (page_id, url, steps)."""
        full_path = Path(project_path) / "templates" / template_rel_path
        if not full_path.exists():
            return None
        with open(full_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_pytest_command(self, test_file):
        """Tạo lệnh chạy pytest"""
        return [sys.executable, "-m", "pytest", test_file, "-v", "-s", "--tb=no"]