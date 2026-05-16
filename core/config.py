import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """
    ZOM Centralized Configuration (v10.0)
    Addresses GÖREV 2.2 and ensures strict doctrine compliance.
    """
    ZOM_MAX_RETRIES = int(os.getenv("ZOM_MAX_RETRIES", "3"))
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:2b")
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "tulpar2026")
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    WORKSPACE_DIR = os.path.join(BASE_DIR, "workspace")
    LOG_DIR = os.path.join(BASE_DIR, "logs")

config = Config()
