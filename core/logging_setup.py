import logging
import json
import os
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Structured JSON logging for production (Claude Code Standard)"""
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

def setup_logging(config):
    """Configure centralized logging for all modules"""
    log_dir = config.LOG_DIR
    os.makedirs(log_dir, exist_ok=True)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.LOG_LEVEL))
    
    # Console Handler (JSON)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(console_handler)
    
    # File Handler (JSON)
    log_file = os.path.join(log_dir, f"zom_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)
    
    logging.info(f"✅ Logging system initialized. Logs: {log_file}")
