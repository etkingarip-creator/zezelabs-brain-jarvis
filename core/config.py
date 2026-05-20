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
    AI_PROVIDER = os.getenv("AI_PROVIDER", "deepseek")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
    DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
    RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
    RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")

    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    WORKSPACE_DIR = os.path.join(BASE_DIR, "workspace")
    LOG_DIR = os.path.join(BASE_DIR, "logs")

config = Config()
