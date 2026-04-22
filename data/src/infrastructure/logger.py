import logging
from logging.handlers import TimedRotatingFileHandler
import os

def setup_scraper_logger(scraper_name: str, log_dir: str, backup_count: int = 7) -> logging.Logger:
    """
    Sets up a common rotating logger for a scraper.
    Rotates logs at midnight and keeps up to `backup_count` days.
    """
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
        
    logger = logging.getLogger(scraper_name)
    logger.setLevel(logging.INFO)
    
    # Avoid adding multiple handlers if logger is already configured (Singleton safe)
    if not logger.handlers:
        log_file = os.path.join(log_dir, f"{scraper_name}.log")
        
        # Handler: Rotate daily at midnight
        file_handler = TimedRotatingFileHandler(
            log_file, 
            when="midnight", 
            interval=1, 
            backupCount=backup_count,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)
        
        # Optional: Console handler for easier debugging
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
    return logger
