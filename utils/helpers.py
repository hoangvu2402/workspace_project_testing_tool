import pandas as pd
from pathlib import Path
from utils.logger import log
from config.config import Config

class Helpers:
    """
    Chứa các hàm tiện ích dùng chung cho toàn bộ dự án như đọc file, 
    xử lý chuỗi, hoặc chụp ảnh màn hình.
    """

    @staticmethod
    def read_excel_data(file_name, sheet_name=0):
        """
        Đọc dữ liệu từ file Excel và trả về danh sách các Dictionary.
        Mỗi Dictionary tương ứng với một dòng trong Excel (Key là tiêu đề cột).
        """
        file_path = Config.TEST_DATA_DIR / file_name
        
        try:
            log.info(f"Đang đọc dữ liệu từ file: {file_path}, sheet: {sheet_name}")
            # Đọc file bằng pandas
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # Chuyển đổi DataFrame thành danh sách các bản ghi (list of dicts)
            # Rất phù hợp để truyền vào @pytest.mark.parametrize
            data = df.to_dict(orient='records')
            
            log.info(f"Đọc thành công {len(data)} dòng dữ liệu.")
            return data
            
        except FileNotFoundError:
            log.error(f"Không tìm thấy file dữ liệu tại: {file_path}")
            return []
        except Exception as e:
            log.error(f"Lỗi khi đọc file Excel: {str(e)}")
            return []

    @staticmethod
    def capture_screenshot(page, name):
        """
        Chụp ảnh màn hình trình duyệt Playwright và lưu vào thư mục reports/screenshots.
        """
        try:
            # Tạo thư mục screenshots nếu chưa có
            Config.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
            
            file_path = Config.SCREENSHOTS_DIR / f"{name}.png"
            page.screenshot(path=file_path)
            
            log.info(f"Đã lưu ảnh chụp màn hình tại: {file_path}")
            return str(file_path)
        except Exception as e:
            log.error(f"Không thể chụp ảnh màn hình: {str(e)}")
            return None