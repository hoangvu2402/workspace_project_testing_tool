import sys
import os
from loguru import logger
from datetime import datetime

def setup_logger():

    log_dir = "reports/logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_filename = datetime.now().strftime("log_%Y-%m-%d_%H-%M-%S.log")
    log_path = os.path.join(log_dir, log_filename)

    # Xóa các cấu hình log mặc định trước khi thêm mới
    logger.remove()

    # 1. Ghi log ra Console 
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )


    logger.add(
        log_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        encoding="utf-8",
        rotation="10 MB",
        retention="30 days"
    )

    return logger

log = setup_logger()