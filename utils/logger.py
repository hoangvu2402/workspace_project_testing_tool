import sys
import os
from loguru import logger
from datetime import datetime

def setup_logger():
    """
    Cấu hình Loguru để ghi log ra cả console và file.
    Log file sẽ được lưu trong thư mục 'reports/logs/' với tên file theo ngày giờ.
    """
    
    # Tạo thư mục chứa log nếu chưa có
    log_dir = "reports/logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Định dạng tên file log: log_2024-03-20_15-30-00.log
    log_filename = datetime.now().strftime("log_%Y-%m-%d_%H-%M-%S.log")
    log_path = os.path.join(log_dir, log_filename)

    # Xóa các cấu hình log mặc định trước khi thêm mới
    logger.remove()

    # 1. Ghi log ra Console (Màu sắc rực rỡ để dễ quan sát)
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )

    # 2. Ghi log ra File (Chi tiết hơn để phục vụ debug)
    logger.add(
        log_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        encoding="utf-8",
        rotation="10 MB", # Tự động tạo file mới nếu file cũ > 10MB
        retention="30 days" # Xóa log cũ sau 30 ngày
    )

    return logger

# Khởi tạo instance logger để các module khác có thể import trực tiếp
log = setup_logger()