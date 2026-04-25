import re

import pandas as pd
import json
from pathlib import Path
from utils.logger import log
from config.config import Config

class Helpers:
    """
    Chứa các hàm tiện ích dùng chung. 
    Đã được nâng cấp để hỗ trợ cấu hình Generic JSON và Excel theo từng Site.
    """

    # @staticmethod
    # def read_excel_data(file_name, site_folder=None):
    #     """
    #     Đọc dữ liệu từ file Excel. 
    #     Nếu có site_folder, sẽ tìm trong test_data/[site_folder]/file_name.
    #     """
    #     if site_folder:
    #         file_path = Config.TEST_DATA_DIR / site_folder / file_name
    #     else:
    #         file_path = Config.TEST_DATA_DIR / file_name
        
    #     try:
    #         log.info(f"Đang đọc dữ liệu Excel: {file_path}")
    #         df = pd.read_excel(file_path)
    #         data = df.to_dict(orient='records')
    #         log.info(f"Đọc thành công {len(data)} dòng dữ liệu.")
    #         return data
    #     except Exception as e:
    #         log.error(f"Lỗi khi đọc file Excel: {str(e)}")
    #         return []

    @staticmethod
    def read_excel_data(file_name, site_folder=None, max_show=10):
        """
        Đọc dữ liệu từ file Excel và luôn in preview để kiểm tra.
        Không dùng input(), không block pytest.
        """
        if site_folder:
            domain = site_folder.replace('.', '_').replace(':', '' )
            site_folder = re.sub(r'[\\/*?:"<>|]', "", domain)  # Chuyển đổi tên miền thành folder 
            file_path = Config.TEST_DATA_DIR / site_folder / file_name
        else:
            file_path = Config.TEST_DATA_DIR / file_name

        
        log.warning(f"⚠️ đang tìm file tại: {file_path} ----- {file_name} --- {site_folder}")
        
        try:
            log.info(f"Đang đọc dữ liệu Excel: {file_path}")

            if not file_path.exists():
                raise FileNotFoundError(f"Không tìm thấy file: {file_path}")

            df = pd.read_excel(file_path, dtype=str)
            df = df.fillna("")

            data = df.to_dict(orient='records')

            log.info(f"Đọc thành công {len(data)} dòng dữ liệu.")

            
            preview = data[:max_show]

            print("\n" + "="*50)
            print("📊 DATA PREVIEW:")
            print(f"đường dẫn: {file_path}")
            for i, row in enumerate(preview, 1):
                print(f"{i}: {row}")

            if len(data) > max_show:
                print(f"... (còn {len(data) - max_show} dòng)")

            print("="*50 + "\n")

            return data

        except Exception as e:
            log.exception(f"Lỗi khi đọc file Excel: {e}")
            return []

    @staticmethod
    def load_json_config(file_path):
        try:
            if not Path(file_path).exists():
                log.error(f"Không tìm thấy file JSON: {file_path}")
                return None
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            log.error(f"Lỗi khi đọc JSON {file_path}: {str(e)}")
            return None

    @staticmethod
    def capture_screenshot(page, name):
        """Lưu ảnh màn hình vào reports/screenshots."""
        try:
            Config.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
            file_path = Config.SCREENSHOTS_DIR / f"{name}.png"
            page.screenshot(path=file_path)
            log.info(f"Đã lưu ảnh chụp màn hình tại: {file_path}")
            return str(file_path)
        except Exception as e:
            log.error(f"Không thể chụp ảnh màn hình: {str(e)}")
            return None