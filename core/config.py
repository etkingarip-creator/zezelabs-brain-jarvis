import os
from dotenv import load_dotenv

from core.registry import load_env

_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
import sys
_is_testing = "pytest" in sys.modules or any("pytest" in arg for arg in sys.argv)
load_dotenv(_env_path, override=not _is_testing)

class Config:
    """
    ZOM Centralized Configuration (v10.1)
    Gemini tamamen kaldırıldı - Ücretsiz OpenRouter modelleri kullanılıyor
    """
    _registry_env = load_env()

    # Registry loaded values
    DEEPSEEK_MODEL = _registry_env.get("DEEPSEEK_MODEL", "deepseek-chat")
    DEEPSEEK_API_KEY = _registry_env.get("DEEPSEEK_API_KEY", "")
    RABBITMQ_HOST = _registry_env.get("RABBITMQ_HOST", "localhost")
    RABBITMQ_PORT = _registry_env.get("RABBITMQ_PORT", 5672)
    RABBITMQ_USER = _registry_env.get("RABBITMQ_USER", "guest")
    RABBITMQ_PASS = _registry_env.get("RABBITMQ_PASS", "guest")
    MAX_WORKERS = _registry_env.get("MAX_WORKERS", 10)

    # Fallback/calculated values
    ZOM_MAX_RETRIES = int(os.getenv("ZOM_MAX_RETRIES", "3"))
    ZOM_ENABLE_VOICE_LISTENER = os.getenv("ZOM_ENABLE_VOICE_LISTENER", "false").lower() == "true"
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:2b")
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    AI_PROVIDER = os.getenv("AI_PROVIDER", "deepseek")
    DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
    CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://openrouter.ai/api/v1")
    # Gemma model - OpenRouter üzerinden
    GEMMA_MODEL = os.getenv("GEMMA_MODEL", "google/gemma-4-26b-a4b-it")
    GEMMA_MODEL_FAST = os.getenv("GEMMA_MODEL_FAST", "google/gemma-4-26b-a4b-it")
    # Kalıcı çözüm: tek free endpoint yerine sağlık-bilinçli rotasyon zinciri.
    # Biri 429/402 yerse sıradakine kayılır; sonu Ollama (offline garanti).
    # .env'den FREE_MODEL_CHAIN ile override edilebilir (virgülle ayrılmış).
    FREE_MODEL_CHAIN = [
        m.strip() for m in os.getenv(
            "FREE_MODEL_CHAIN",
            "deepseek/deepseek-r1:free,"
            "meta-llama/llama-3.3-70b-instruct:free,"
            "google/gemini-2.0-flash-exp:free,"
            "qwen/qwen-2.5-72b-instruct:free,"
            "z-ai/glm-4.5-air:free,"
            "mistralai/mistral-small-3.1-24b-instruct:free,"
            "meta-llama/llama-3.2-3b-instruct:free"
        ).split(",") if m.strip()
    ]
    # Backward compatibility - eski OPENAI_MODEL de Gemma'ya yönlendirildi
    OPENAI_MODEL = os.getenv("GEMMA_MODEL", "google/gemma-4-26b-a4b-it")
    OPENAI_MODEL_FAST = os.getenv("GEMMA_MODEL_FAST", "google/gemma-4-26b-a4b-it")
    OPENAI_MODEL_MINIMAX = os.getenv("GEMMA_MODEL", "google/gemma-4-26b-a4b-it")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    ZOM_ENABLE_RABBITMQ = os.getenv("ZOM_ENABLE_RABBITMQ", "false").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
    BINANCE_SECRET = os.getenv("BINANCE_SECRET", "")

    # ─────────────────────────────────────────────────────────────
    # Authentication & Authorization
    # ─────────────────────────────────────────────────────────────
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))

    # Admin şifresi — .env'den okunur, ASLA kodda sabit değer olmaz
    ZOM_ADMIN_PASSWORD = os.getenv("ZOM_ADMIN_PASSWORD", "")

    # Önceden tanımlı API anahtarları — .env'den okunur
    ZOM_ADMIN_API_KEY = os.getenv("ZOM_ADMIN_API_KEY", "")
    ZOM_DEPT_API_KEY = os.getenv("ZOM_DEPT_API_KEY", "")
    ZOM_READONLY_API_KEY = os.getenv("ZOM_READONLY_API_KEY", "")

    # API Keys (comma-separated list)
    API_KEYS = [k.strip() for k in os.getenv("API_KEYS", "").split(",") if k.strip()]

    # Telegram Shadow CEO alerts
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
    SHADOW_CEO_ALERT_CHANNEL = os.getenv("SHADOW_CEO_ALERT_CHANNEL", "log_only")

    # Rate Limiting
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "500"))  # per minute - artırıldı
    RATE_LIMIT_BURST = int(os.getenv("RATE_LIMIT_BURST", "100"))  # burst size - artırıldı

    # Audit Logging
    AUDIT_LOG_ENABLED = os.getenv("AUDIT_LOG_ENABLED", "true").lower() == "true"
    AUDIT_LOG_PATH = os.getenv("AUDIT_LOG_PATH", "logs/audit.log")

    # CORS allowlist for the FastAPI surface. Comma-separated; default = local dev only.
    ALLOWED_ORIGINS = [
        o.strip() for o in os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,app://zezelabs",
        ).split(",") if o.strip()
    ]

    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    WORKSPACE_DIR = os.path.join(BASE_DIR, "workspace")
    LOG_DIR = os.path.join(BASE_DIR, "logs")

config = Config()
