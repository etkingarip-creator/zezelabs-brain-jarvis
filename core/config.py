import os
from dotenv import load_dotenv

from core.registry import load_env

load_dotenv()

class Config:
    """
    ZOM Centralized Configuration (v10.0)
    Addresses GÖREV 2.2 and ensures strict doctrine compliance.
    """
    _registry_env = load_env()

    # Registry loaded values
    DEEPSEEK_MODEL = _registry_env.get("DEEPSEEK_MODEL", "deepseek-chat")
    DEEPSEEK_API_KEY = _registry_env.get("DEEPSEEK_API_KEY", "")
    RABBITMQ_HOST = _registry_env.get("RABBITMQ_HOST", "localhost")
    RABBITMQ_PORT = _registry_env.get("RABBITMQ_PORT", 5672)
    RABBITMQ_USER = _registry_env.get("RABBITMQ_USER", "guest")
    RABBITMQ_PASS = _registry_env.get("RABBITMQ_PASS", "guest")

    # Fallback/calculated values
    ZOM_MAX_RETRIES = int(os.getenv("ZOM_MAX_RETRIES", "3"))
    ZOM_ENABLE_VOICE_LISTENER = os.getenv("ZOM_ENABLE_VOICE_LISTENER", "false").lower() == "true"
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:2b")
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    AI_PROVIDER = os.getenv("AI_PROVIDER", "deepseek")
    DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    WORKSPACE_DIR = os.path.join(BASE_DIR, "workspace")
    LOG_DIR = os.path.join(BASE_DIR, "logs")

config = Config()
