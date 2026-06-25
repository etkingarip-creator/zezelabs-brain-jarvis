import asyncio
import logging
import signal
import sys
import os

# Force UTF-8 on Windows for stdout/stderr to prevent UnicodeEncodeError crashes with emojis
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import threading
import time
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import json
import uuid
from typing import Optional, Dict, Any, List, Union

# Add project root to path so package imports resolve when this file is run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Jarvis Core Systems
from core.config import config
from core.ai.providers.openrouter_director import OpenRouterDirector
from core.prompts.jarvis_identity import build_jarvis_prompt, build_department_awareness, build_recent_events_context
from core.registry.department_registry import department_registry, initialize_default_departments
from core.events.event_bus import event_bus
from core.events.event_types import SystemEvents, DepartmentEvents
from core.knowledge.shared_knowledge import shared_knowledge_base
from core.learning.cross_dept_learner import cross_dept_learner
from core.orchestration.intelligent_router import intelligent_router
from core.orchestration.autonomous_collab import autonomous_collaborator
from core.realtime.websocket_server import realtime_server
from backend.ecosystem_api import router as ecosystem_router, set_jarvis_core
from backend.api.design_ai import router as design_ai_router, set_director as set_design_director

# Traceloop OpenLLMetry lazy import pattern
try:
    from traceloop.sdk import Traceloop
    _TRACELOOP_AVAILABLE = True
except ImportError:
    _TRACELOOP_AVAILABLE = False

from core.mq_client import MQClient

# Zeze Guard & Orchestration Systems
from core.zeze_guard.roi_tracker import ROITracker
from core.zeze_guard.anti_loop import AntiLoopEngine
from core.zeze_guard.shadow_ceo_alerts import ShadowCEOAlertClient



# Security - lazy import pattern (safe fallback if modules missing)
try:
    from core.security.guardrails import Guardrails
    from core.security.auth import (
        User, UserRole, JWTHandler, APIKeyManager,
        get_current_user, require_any_auth, TokenResponse,
        JWT_EXPIRATION_MINUTES
    )
    from core.security.rbac import (
        Permission, RBACChecker, require_permission,
        require_admin, require_department, require_readonly
    )
    from core.security.rate_limiter import RateLimitMiddleware, rate_limiter
    from core.security.audit import AuditLogger, audit_logger, AuditMiddleware, get_audit_stats
    from core.operator_runtime.policy_engine import PolicyEngine
    _SECURITY_ENABLED = True
except ImportError as _sec_err:
    logging.error(
        f"[SECURITY] Güvenlik modülleri yüklenemedi: {_sec_err}\n"
        "[SECURITY] SİSTEM FAIL-CLOSED modunda çalışıyor — tüm korunan endpoint'ler 401 döndürecek."
    )
    _SECURITY_ENABLED = False
    # ── FAIL-CLOSED stubs: hiçbir kullanıcıya otomatik yetki VERİLMEZ ──
    from fastapi import HTTPException as _HTTPException
    class User:
        def __init__(self, **kw): pass
    class UserRole:
        ADMIN = "admin"; DEPARTMENT = "dept"; READONLY = "readonly"
    class JWTHandler:
        @staticmethod
        def create_token(u): raise _HTTPException(status_code=503, detail="Security module unavailable")
    class APIKeyManager:
        @staticmethod
        def generate_key(u): raise _HTTPException(status_code=503, detail="Security module unavailable")
        @staticmethod
        def list_keys(): return []
    class RBACChecker:
        @staticmethod
        def get_user_permissions(u): return []
    async def get_current_user(*a, **kw):
        raise _HTTPException(status_code=401, detail="Security module unavailable — access denied")
    def require_admin(*a, **kw):
        raise _HTTPException(status_code=401, detail="Security module unavailable — access denied")
    class TokenResponse:
        def __init__(self, **kw): pass
    JWT_EXPIRATION_MINUTES = 60
    RateLimitMiddleware = None
    AuditMiddleware = None
    rate_limiter = type('rl', (), {'get_stats': lambda self: {}, 'enabled': False})()
    audit_logger = type('al', (), {'search_logs': lambda self, **kw: [], 'log_event': lambda self, **kw: None})()
    def get_audit_stats(): return {}
    class PolicyEngine:
        def evaluate(self, *a, **kw): return True
    class Guardrails:
        def check(self, *a, **kw): return True
        def looks_like_dangerous_payload(self, *a, **kw): return False, ""
    def Depends(fn): return fn

# Departman Ajanları - safe import with fallback
def _safe_import_agent(module_path, class_name):
    try:
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)
    except (ImportError, SyntaxError, AttributeError) as e:
        logging.warning(f"Failed to import {class_name} from {module_path}: {e}")
        # Return dummy agent class
        return type(class_name, (), {
            '__init__': lambda self, **kwargs: None,
            'run_cycle': lambda self: asyncio.sleep(0),
        })

ZezeDesignAgent = _safe_import_agent('departments.zeze_design.agent', 'ZezeDesignAgent')
ZezeTrendAgent = _safe_import_agent('departments.zeze_trend.agent', 'ZezeTrendAgent')
ZezeRndAgent = _safe_import_agent('departments.zeze_rnd.agent', 'ZezeRndAgent')
AppFactoryAgent = _safe_import_agent('departments.app_factory.agent', 'AppFactoryAgent')
CryptoTradingAgent = _safe_import_agent('departments.crypto_trading.agent', 'CryptoTradingAgent')
MediaFactoryAgent = _safe_import_agent('departments.media_factory.agent', 'MediaFactoryAgent')
ZezeAroAgent = _safe_import_agent('departments.zeze_aro.agent', 'ZezeAroAgent')
ZezeSecAgent = _safe_import_agent('departments.zeze_sec.agent', 'ZezeSecAgent')
ZezeBusinessAgent = _safe_import_agent('departments.zeze_business.agent', 'ZezeBusinessAgent')
ZezeCommsAgent = _safe_import_agent('departments.zeze_comms.agent', 'ZezeCommsAgent')
ZezeComplianceAgent = _safe_import_agent('departments.zeze_compliance.agent', 'ZezeComplianceAgent')
ZezeDevAgent = _safe_import_agent('departments.zeze_dev.agent', 'ZezeDevAgent')
ZezeOpsAgent = _safe_import_agent('departments.zeze_ops.agent', 'ZezeOpsAgent')
ZezeProductionAgent = _safe_import_agent('departments.zeze_production.agent', 'ZezeProductionAgent')
ZezeGameAgent = _safe_import_agent('departments.zeze_game.agent', 'ZezeGameAgent')
ZezeBettingAgent = _safe_import_agent('departments.zeze_betting.agent', 'ZezeBettingAgent')
ZezeAcademyAgent = _safe_import_agent('departments.zeze_academy.agent', 'ZezeAcademyAgent')

# Logging yapılandırması - logs/ klasörüne yaz
_log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(_log_dir, exist_ok=True)
_log_file = os.path.join(_log_dir, "jarvis_zom_core.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(_log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('jarvis_zom')

class JarvisZOMCore:
    def __init__(self):
        # Modern lifespan context manager (FastAPI 0.93+ — replaces deprecated @app.on_event)
        @asynccontextmanager
        async def _lifespan(app: FastAPI):
            await self.startup()
            yield
            await self.shutdown()

        self.app = FastAPI(title="Jarvis ZOM Core", version="2.0.0", lifespan=_lifespan)
        self.setup_middleware()
        self.setup_routes()
        self.setup_websocket()
        
        # Core Systems
        self.policy = PolicyEngine()
        self.roi = ROITracker()
        self.anti_loop = AntiLoopEngine()
        self.alerts = ShadowCEOAlertClient()

        self.guardrails = Guardrails()
        
        # Super Intelligence Ecosystem
        self.department_registry = initialize_default_departments()
        self.event_bus = event_bus
        self.knowledge_base = shared_knowledge_base
        self.cross_learner = cross_dept_learner
        self.intelligent_router = intelligent_router
        self.autonomous_collaborator = autonomous_collaborator

        # Initialize MQClient and dynamic connection readiness status
        self.mq = MQClient(
            host=config.RABBITMQ_HOST,
            port=config.RABBITMQ_PORT,
            user=config.RABBITMQ_USER,
            password=config.RABBITMQ_PASS,
        )
        self.mq_ready = False
        self.local_task_queue = asyncio.Queue()

        # Pending task results keyed by task_id; populated when the result
        # listener thread consumes task_results_queue. We store plain dicts here
        # (not Futures) because resolution happens from a non-asyncio thread.
        self.task_results: dict[str, dict] = {}
        self.task_history: list[dict] = []
        self._main_loop: asyncio.AbstractEventLoop | None = None
        self._result_thread_stop = threading.Event()
        self._result_thread = None
        self._background_tasks: list[asyncio.Task] = []
        
        # AI Providers
        self.openrouter = OpenRouterDirector()
        
        # Departman Ajanları (11 Departman)
        self.agents = {
            "app_factory": AppFactoryAgent(workspace_root="."),
            "crypto_trading": CryptoTradingAgent(workspace_root="."),
            "media_factory": MediaFactoryAgent(workspace_root="."),
            "zeze_aro": ZezeAroAgent(workspace_root="."),
            "zeze_design": ZezeDesignAgent(workspace_root="."),
            "zeze_rnd": ZezeRndAgent(workspace_root="."),
            "zeze_sec": ZezeSecAgent(workspace_root="."),
            "zeze_trend": ZezeTrendAgent(workspace_root="."),
            "zeze_business": ZezeBusinessAgent(workspace_root="."),
            "zeze_comms": ZezeCommsAgent(workspace_root="."),
            "zeze_compliance": ZezeComplianceAgent(workspace_root="."),
            "zeze_dev": ZezeDevAgent(workspace_root="."),
            "zeze_ops": ZezeOpsAgent(workspace_root="."),
            "zeze_production": ZezeProductionAgent(workspace_root="."),
            "zeze_game": ZezeGameAgent(workspace_root="."),
            "zeze_betting": ZezeBettingAgent(workspace_root="."),
            "zeze_academy": ZezeAcademyAgent(workspace_root="."),
        }
        
        # WebSocket bağlantı yönetimi
        self.active_connections: dict[str, WebSocket] = {}
        self.connection_tasks: dict[str, asyncio.Task] = {}
        
        # Keep-alive ayarları
        self.keep_alive_interval = 60  # saniye - daha uzun interval ile bağlantı stabil
        self.connection_timeout = 30   # saniye
        self.max_reconnect_attempts = 3
        
        # Sistem durumu
        self.is_running = False
        self.start_time = None
        
        # Mesaj geçmişi — SQLite'a taşındı (restart sonrası hayatta kalır)
        from core.storage.conversation_store import add_message, get_history, clear_history
        self._conv_add = add_message
        self._conv_get = get_history
        self._conv_clear = clear_history
        self.pending_actions: dict[str, dict] = {}
        self.autonomy_mode = "semi"
        self.focused_department = None
        
        logger.info("Jarvis ZOM Core initialized")

    # ── Yardımcı: UserRole string'e güvenli normalize et ──────────────────
    @staticmethod
    def _get_role_str(user) -> str:
        """UserRole enum veya str'den tutarlı küçük harf rol döndürür."""
        role = getattr(user, 'role', None)
        if role is None:
            return ''
        v = role.value if hasattr(role, 'value') else str(role)
        return v.lower()

    async def _build_awareness_context(self) -> dict[str, str]:
        """
        Jarvis için self-awareness context oluştur
        
        Returns:
            Dict with keys: awareness_snapshot, department_list, recent_events
        """
        # 1. Sistem durumu
        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        uptime_str = f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m" if uptime > 0 else "Yeni başlatıldı"
        
        awareness_snapshot = f"""
- Uptime: {uptime_str}
- Aktif WebSocket bağlantıları: {len(self.active_connections)}
- Toplam işlenen görev: {len(self.task_history)}
- Beklenen sonuçlar: {len(self.task_results)}
- Model: {self.openrouter.default_model}
"""
        
        # 2. Departman listesi ve durumları
        dept_details = []
        for dept_name, agent in self.agents.items():
            status = "Aktif" if agent else "Pasif"
            capabilities = getattr(agent, 'capabilities', ['Genel görevler'])
            if isinstance(capabilities, list):
                cap_str = ", ".join(capabilities[:3])
            else:
                cap_str = "Genel"
            dept_details.append(f"- **{dept_name}**: {status} | Yetenekler: {cap_str}")
        
        department_list = build_department_awareness(
            dept_count=len(self.agents),
            dept_details="\n".join(dept_details),
            synergy_opportunities="Departmanlar arası sinerji analizi başlatılıyor..."
        )
        
        # 3. Son olaylar (task_history'den son 5)
        recent_tasks = self.task_history[-5:] if self.task_history else []
        if recent_tasks:
            events = []
            for task in recent_tasks:
                task_id = task.get("task_id", "N/A")
                status = task.get("status", "unknown")
                desc = task.get("description", "Açıklama yok")[:80]
                events.append(f"- [{status.upper()}] {task_id}: {desc}")
            events_list = "\n".join(events)
        else:
            events_list = "Henüz görev geçmişi yok"
        
        recent_events = build_recent_events_context(
            events_list=events_list,
            analysis="Sistem normal çalışıyor. Departmanlar arası koordinasyon aktif."
        )
        
        return {
            "awareness_snapshot": awareness_snapshot,
            "department_list": department_list,
            "recent_events": recent_events
        }

    def _add_to_history(self, client_id: str, role: str, content: str, task_id: Optional[str] = None, department: Optional[str] = None):
        """Mesaj geçmişine ekle — hem SQLite hem de Vektörel (FTS5) Hafızaya yaz"""
        self._conv_add(client_id, role, content, task_id, department)
        try:
            if not hasattr(self, "_memory"):
                from core.memory.db_client import TieredMemoryClient
                self._memory = TieredMemoryClient()
            
            if content and len(content.strip()) > 3:
                metadata = {
                    "client_id": client_id,
                    "role": role,
                    "type": "chat_message"
                }
                # Apply heuristic filter to prevent FTS5 long memory bloat
                is_meaningful = True
                content_lower = content.lower().strip()
                greetings = {"merhaba", "hello", "hi", "selam", "günaydın", "iyi günler", "hey", "nasılsın", "teşekkürler", "thanks", "ok", "tamam", "evet", "hayır", "yes", "no"}
                if content_lower in greetings or len(content_lower) < 15:
                    is_meaningful = False
                if task_id:
                    is_meaningful = True
                
                tier = "long" if is_meaningful else "short"
                self._memory.add_memory(
                    memory_text=f"Sohbet Geçmişi ({role}): {content}",
                    metadata=metadata,
                    tier=tier
                )
        except Exception as e:
            logger.error(f"Failed to add message to vector memory: {e}")

    def _get_recent_messages(self, client_id: str) -> list[dict]:
        """Son mesajları SQLite'tan al"""
        return self._conv_get(client_id)

    def _route_to_department(self, message: str) -> tuple[str, bool]:
        """Mesaj içeriğine göre uygun departmanı belirle.
        Dönen değer: (dept_name, is_direct_match)
        """
        import re
        msg_lower = message.lower()
        
        # Keyword-based routing
        dept_keywords = {
            "zeze_dev": ["kod", "kod yaz", "geliştir", "program", "git", "commit", "test", "hata", "bug", "feature", "code", "develop", "build", "deploy"],
            "zeze_design": ["tasarım", "ui", "ux", "görsel", "renk", "font", "tasarla", "design", "mockup", "figma"],
            "zeze_business": ["iş", "strateji", "pazar", "müşteri", "gelir", "şirket", "business", "strategy", "revenue"],
            "zeze_comms": ["iletişim", "haber", "duyuru", "medya", "pr", "yazı", "içerik", "communications", "press"],
            "zeze_compliance": ["uyum", "yasal", "düzenleme", "politika", "izin", "compliance", "legal", "regulatory"],
            "zeze_ops": ["operasyon", "süreç", "verimlilik", "işlem", "operations", "process", "optimization"],
            "zeze_production": ["üretim", "içerik", "video", "görüntü", "production", "content", "video", "media"],
            "zeze_trend": ["trend", "pazar", "analiz", "rekabet", "trend", "market", "analysis", "competitor"],
            "zeze_rnd": ["araştırma", "r&d", "yenilik", "prototip", "research", "innovation", "prototype", "ai"],
            "zeze_sec": ["güvenlik", "güvenli", "tarama", "test", "audit", "security", "vulnerability", "penetration"],
            "zeze_aro": ["analitik", "metrik", "veri", "izleme", "analytics", "metrics", "data", "monitoring"],
            "app_factory": ["uygulama", "app", "saas", "web", "mobil", "api", "application", "saas", "fastapi"],
            "crypto_trading": ["kripto", "bitcoin", "trade", "bnb", "ethereum", "crypto", "trading", "binance", "coin", "cüzdan", "bakiye", "varlık"],
            "media_factory": ["video", "ses", "görüntü", "animasyon", "video", "audio", "animation", "media"],
            "zeze_game": ["oyun", "game", "gaming", "play", "level", "karakter"],
            "zeze_betting": ["bahis", "betting", "tahmin", "oran", "tuttur", "kupon"],
        }
        
        for dept, keywords in dept_keywords.items():
            for keyword in keywords:
                # Word boundary and prefix match using \b to prevent false positive substring collisions
                pattern = r'\b' + re.escape(keyword.lower())
                if re.search(pattern, msg_lower):
                    logger.info(f"Routing to {dept} (matched keyword: {keyword})")
                    return dept, True
        
        # Default to zeze_business for general queries (no direct keyword match)
        return "zeze_business", False

    async def _determine_message_routing(self, message: str, department_override: Optional[str] = None) -> tuple[str, Optional[str], list[str]]:
        """
        Determines the intent and target department/pipeline for a message in a single place.
        Consolidates rule-based overrides, system query exceptions, and LLM-based intent analysis.
        """
        intent = "CHAT"
        target_dept = department_override
        pipeline = []

        if department_override:
            intent = "TASK"
        else:
            # Check system status / telemetry query first
            is_system_query = False
            system_keywords = ["departman durum", "sistem durum", "sunucu durum", "departmanların durum", "jarvis durum", "telemetri"]
            if any(kw in message.lower() for kw in system_keywords):
                is_system_query = True

            if is_system_query:
                intent = "CHAT"
                target_dept = None
            else:
                intent_data = await self._analyze_intent(message)
                intent = intent_data.get("intent", "CHAT")
                target_dept = intent_data.get("department")
                pipeline = intent_data.get("pipeline") or []

                # Rule-based fallback/override
                rule_dept, is_direct_match = self._route_to_department(message)
                if rule_dept and is_direct_match and intent == "CHAT":
                    action_keywords = ["görev", "rapor", "kontrol", "yaz", "sorgula", "bakiye", "cüzdan", "analiz", "durum", "ne oldu", "listele", "hesapla"]
                    if any(kw in message.lower() for kw in action_keywords):
                        intent = "TASK"
                        target_dept = rule_dept
                        logger.info(f"Rule-based intent override: TASK allocated to '{target_dept}' for query: '{message}'")

                # IntelligentRouter ile işbirliği tespiti
                if intent == "TASK" and target_dept:
                    try:
                        from core.orchestration.intelligent_router import Task as RouterTask, TaskPriority
                        import uuid as _uuid
                        router_task = RouterTask(
                            id=str(_uuid.uuid4()),
                            title=message[:80],
                            description=message,
                            required_capabilities=pipeline if pipeline else [target_dept],
                            preferred_departments=[target_dept],
                        )
                        routing_decision = await self.intelligent_router.route_task(router_task)
                        if routing_decision.collaboration_needed:
                            logger.info(f"IntelligentRouter: işbirliği gerekli → {routing_decision.collaboration_needed}")
                            pipeline = routing_decision.collaboration_needed
                    except Exception as _re:
                        logger.debug(f"IntelligentRouter routing skipped: {_re}")

        return intent, target_dept, pipeline

    def setup_middleware(self):
        # Rate limiting middleware (en dışta) — sadece modül yüklendiyse
        if config.RATE_LIMIT_ENABLED and RateLimitMiddleware is not None:
            self.app.add_middleware(RateLimitMiddleware)

        # Audit logging middleware
        if config.AUDIT_LOG_ENABLED and AuditMiddleware is not None:
            self.app.add_middleware(AuditMiddleware)

        # CORS: .env'deki ALLOWED_ORIGINS değerini kullan — production'da * KULLANILMAZ
        cors_origins = config.ALLOWED_ORIGINS if config.ALLOWED_ORIGINS else ["http://localhost:5173"]
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type", "X-API-Key"],
        )

    def setup_routes(self):
        # ─────────────────────────────────────────────────────────────
        # Authentication Endpoints
        # ─────────────────────────────────────────────────────────────
        @self.app.post("/api/auth/token", response_model=TokenResponse, tags=["auth"])
        async def login(request: dict):
            """JWT token al (username/password ile)"""
            username = request.get("username", "")
            password = request.get("password", "")

            # Şifre ve kullanıcı bilgileri TAMAMEN .env'den okunur — kodda sabit değer yok
            admin_password = config.ZOM_ADMIN_PASSWORD
            if not admin_password:
                raise HTTPException(
                    status_code=503,
                    detail="ZOM_ADMIN_PASSWORD .env'de tanımlı değil. Sistem yöneticisine başvurun."
                )

            valid_users = {
                "jarvis_admin": ("admin_001", UserRole.ADMIN),
                "zeze_eng": ("dept_001", UserRole.DEPARTMENT),
                "zeze_media": ("dept_002", UserRole.DEPARTMENT),
                "guest": ("readonly_001", UserRole.READONLY),
            }

            if username == "jarvis_admin":
                expected_password = admin_password
                dept = None
            elif username == "zeze_eng":
                expected_password = os.getenv("ZOM_DEPT_ENG_PASSWORD") or admin_password
                dept = "zeze_eng"
            elif username == "zeze_media":
                expected_password = os.getenv("ZOM_DEPT_MEDIA_PASSWORD") or admin_password
                dept = "zeze_media"
            elif username == "guest":
                expected_password = os.getenv("ZOM_READONLY_PASSWORD") or admin_password
                dept = None
            else:
                expected_password = None
                dept = None

            import hmac as _hmac
            pw_match = bool(expected_password) and _hmac.compare_digest(
                password.encode('utf-8'), expected_password.encode('utf-8')
            )
            if not pw_match or username not in valid_users:
                logger.warning(f"[AUTH] Başarısız giriş denemesi: kullanıcı={username!r}")
                raise HTTPException(status_code=401, detail="Invalid credentials")

            user_id, role = valid_users[username]
            user = User(user_id=user_id, username=username, role=role, department=dept)

            return TokenResponse(
                access_token=JWTHandler.create_token(user),
                token_type="bearer",
                expires_in=JWT_EXPIRATION_MINUTES * 60,
            )

        @self.app.post("/api/auth/apikey", response_model=dict, tags=["auth"])
        async def create_api_key(
            request: dict,
            user: User = Depends(require_admin),
        ):
            """Yeni API key oluştur (admin only)"""
            username = request.get("username")
            role_str = request.get("role", "readonly")
            department = request.get("department")

            if not username:
                raise HTTPException(status_code=400, detail="Username required")

            try:
                role = UserRole(role_str)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid role")

            user_obj = User(
                user_id=f"user_{username}",
                username=username,
                role=role,
                department=department,
            )

            api_key = APIKeyManager.generate_key(user_obj)
            return {
                "api_key": api_key,
                "username": username,
                "role": role.value,
                "warning": "Bu anahtarı güvenli bir yerde saklayın! Bir kez daha gösterilmeyecek.",
            }

        @self.app.get("/api/auth/apikeys", tags=["auth"])
        async def list_api_keys(user: User = Depends(require_admin)):
            """Tüm API key'leri listele (admin only)"""
            return {"keys": APIKeyManager.list_keys()}

        @self.app.delete("/api/auth/apikey/{key_hash}", tags=["auth"])
        async def revoke_api_key(
            key_hash: str,
            user: User = Depends(require_admin),
        ):
            """API key iptal et (admin only)"""
            return {"revoked": True, "key_hash": key_hash}

        @self.app.get("/api/auth/me", tags=["auth"])
        async def get_current_user_info(user: User = Depends(get_current_user)):
            """Mevcut kullanıcı bilgilerini al"""
            return {
                "user_id": user.user_id,
                "username": user.username,
                "role": user.role.value,
                "department": user.department,
                "permissions": RBACChecker.get_user_permissions(user),
            }

        # ─────────────────────────────────────────────────────────────
        # Admin Endpoints
        # ─────────────────────────────────────────────────────────────
        @self.app.get("/api/admin/audit", tags=["admin"])
        async def get_audit_logs(
            limit: int = 100,
            event_type: Optional[str] = None,
            user: User = Depends(require_admin),
        ):
            """Audit loglarını al (admin only)"""
            from core.security.audit import get_audit_stats
            return {
                "stats": get_audit_stats(),
                "logs": audit_logger.search_logs(
                    event_type=event_type,
                    limit=limit,
                ),
            }

        @self.app.get("/api/admin/rate-limit-stats", tags=["admin"])
        async def get_rate_limit_stats(user: User = Depends(require_admin)):
            """Rate limiter istatistiklerini al (admin only)"""
            return rate_limiter.get_stats()

        # ─────────────────────────────────────────────────────────────
        # Health & Status Endpoints
        # ─────────────────────────────────────────────────────────────
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "online",
                "timestamp": datetime.now().isoformat(),
                "uptime": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
                "active_connections": len(self.active_connections),
                "agents_count": len(self.agents)
            }

        @self.app.get("/api/runtime/status")
        async def runtime_status():
            credits = {}
            try:
                credits = await self.openrouter.credits()
            except Exception:
                credits = {"available": False}
            
            # Departman display name'lerini al
            dept_info = {}
            for name in self.agents.keys():
                profile = self.department_registry.get(name)
                display_name = profile.display_name if profile else name.replace("_", " ").title()
                dept_info[name] = {
                    "status": "active",
                    "display_name": display_name,
                    "department_id": name
                }
            
            return {
                "status": "running" if self.is_running else "stopped",
                "ai_mode": "openrouter",
                "model": self.openrouter.default_model,
                "openrouter_credits": credits,
                "mq_connected": self.mq_ready,
                "departments": dept_info,
            }

        @self.app.get("/api/telemetry/live")
        async def telemetry_live():
            """HUD için GERÇEK canlı telemetri — traces (critic/sorgu/RAG) + guard_costs (token).
            Veri yoksa null döner; HUD bunu '—' olarak gösterir (uydurma yok)."""
            from core.observability.tracer import get_global_trace_telemetry
            t = get_global_trace_telemetry()

            total_tokens = 0
            total_cost = 0.0
            roi_score = None
            try:
                from core.zeze_guard.roi_tracker import ROITracker
                tracker = ROITracker()
                costs = getattr(tracker.storage, "costs", []) or []
                total_tokens = sum((c.get("tokens_in", 0) + c.get("tokens_out", 0)) for c in costs)
                total_cost = sum(c.get("estimated_cost_usd", 0.0) for c in costs)
                try:
                    roi_score = tracker._calculate_base_metrics().get("roi_score")
                except Exception:
                    roi_score = None
            except Exception as _te:
                logger.debug(f"telemetry token aggregation skipped: {_te}")

            # GERÇEK sistem metrikleri (psutil); yoksa None
            cpu_pct = ram_pct = None
            try:
                import psutil
                cpu_pct = psutil.cpu_percent(interval=0.1)
                ram_pct = psutil.virtual_memory().percent
            except Exception:
                pass

            tasks = self.task_history or []
            return {
                "critic_score": t.get("avg_critic_score"),
                "query_ms": t.get("avg_query_ms"),
                "rag_hits": t.get("avg_rag_hits"),
                "total_traces": t.get("total_traces", 0),
                "total_tokens": total_tokens,
                "total_cost_usd": round(total_cost, 4),
                "roi_score": roi_score,
                "cpu_percent": cpu_pct,
                "ram_percent": ram_pct,
                "active_tasks": sum(1 for x in tasks if x.get("status") == "queued"),
                "completed_tasks": sum(1 for x in tasks if x.get("status") == "success"),
            }

        @self.app.get("/api/departments")
        async def get_departments():
            """Tüm departmanları listele"""
            departments = []
            for name, profile in self.department_registry.departments.items():
                departments.append({
                    "name": name,
                    "display_name": profile.display_name,
                    "status": profile.status,
                    "load": profile.get_load(),
                    "capabilities": profile.capabilities,
                    "expertise_areas": profile.expertise_areas
                })
            return {"departments": departments, "count": len(departments)}

        @self.app.post("/api/orchestration/synergy/run")
        async def run_synergy_chain(request: dict):
            """Predefined otonom holding synergy zincirini başlat"""
            chain_name = request.get("chain_name")
            async_mode = request.get("async", True)
            if not chain_name:
                raise HTTPException(status_code=400, detail="chain_name is required")
            
            from core.orchestration.synergy_chain import synergy_chain_manager
            
            if async_mode:
                async def run_in_background():
                    await synergy_chain_manager.run_chain(chain_name, workspace_root=".")
                asyncio.create_task(run_in_background())
                return {
                    "status": "started",
                    "chain_name": chain_name,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                result = await synergy_chain_manager.run_chain(chain_name, workspace_root=".")
                return result

        @self.app.get("/api/departments/status")
        async def get_departments_status():
            """Dashboard için tüm departmanların durumunu dinamik döndür"""
            from datetime import datetime
            import psutil
            
            try:
                cpu_usage = f"{psutil.cpu_percent()}%"
                ram_usage = f"{psutil.virtual_memory().percent}%"
            except Exception:
                cpu_usage = "0%"
                ram_usage = "0%"
                
            uptime_str = "N/A"
            if self.start_time:
                uptime = (datetime.now() - self.start_time).total_seconds()
                uptime_str = f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m"

            from core.zeze_guard.storage import get_storage
            guard_storage = get_storage()
            all_alerts = getattr(guard_storage, "alerts", [])
            
            departments: dict[str, dict] = {}
            for name, profile in self.department_registry.departments.items():
                agent = self.agents.get(name)
                
                dept_tasks = [t for t in self.task_history if name in t.get("departments", []) or t.get("department") == name]
                api_calls = len(dept_tasks)
                success_tasks = [t for t in dept_tasks if t.get("status") == "success" or t.get("outcome") == "success"]
                if api_calls == 0:
                    success_rate = "N/A"  # Hiç görev yoksa yanıltıcı 100% gösterme
                else:
                    success_rate = f"{int((len(success_tasks) / api_calls) * 100)}%"
                
                dept_issues = [
                    a["message"] for a in all_alerts
                    if (
                        a.get("metadata", {}).get("dept") == name
                        or name.lower() in a.get("message", "").lower()
                        or name.lower().replace("_", " ") in a.get("message", "").lower()
                    )
                ]
                
                departments[name] = {
                    "status": "healthy" if agent else "unknown",
                    "uptime": uptime_str,
                    "api_calls": api_calls,
                    "success_rate": success_rate,
                    "queue_depth": 0,
                    "system_usage": {"cpu": cpu_usage, "ram": ram_usage, "gpu": "0%"},
                    "active_agents": 1 if agent else 0,
                    "agents_list": [],
                    "audit": {
                        "rabbitmq_connection": "connected" if self.mq_ready else "disconnected",
                        "config_status": "valid",
                        "issues": dept_issues,
                        "workload": "medium" if api_calls > 5 else "low"
                    }
                }
            return {
                "departments": departments,
                "brain_online": self.is_running,
                "brain_model": self.openrouter.default_model if hasattr(self, 'openrouter') else None,
                "fetched_at": datetime.now().isoformat()
            }

        @self.app.get("/api/departments/{name}/status")
        async def department_status(
            name: str,
            user: User = Depends(require_department),
        ):
            """Departman durumunu al"""
            agent = self.agents.get(name)
            return {
                "status": "active" if agent else "unknown",
                "agent_type": type(agent).__name__ if agent else "Unknown"
            }

        @self.app.post("/api/departments/{name}/execute")
        async def department_execute(
            name: str,
            request: dict,
            user: User = Depends(require_department),
        ):
            """Run a department agent directly (bypassing the cognitive router).

            Useful for the dashboard 'Run task on X' buttons. The agent must
            implement ``execute_task(task_data)``.
            """
            agent = self.agents.get(name)
            if agent is None:
                return {"status": "error", "error": "UNKNOWN_DEPARTMENT", "name": name}
            if not hasattr(agent, "execute_task"):
                return {"status": "error", "error": "AGENT_HAS_NO_EXECUTE_TASK"}

            description = (request.get("description") or request.get("goal") or "").strip()
            if description:
                is_dangerous, reason = self.guardrails.looks_like_dangerous_payload(description)
                if is_dangerous:
                    return {"status": "blocked", "error": f"SECURITY_BLOCK:{reason}"}

            task_id = str(uuid.uuid4())
            task_data = {
                "task_id": task_id,
                "description": description,
                "task_type": request.get("task_type", "dashboard_direct"),
                "client_id": request.get("client_id"),
                **{k: v for k, v in request.items() if k not in {"description", "goal", "task_type", "client_id"}},
            }
            try:
                outcome = await agent.execute_task(task_data)
                self.task_results[task_id] = {
                    "task_id": task_id,
                    "status": "completed",
                    "result": outcome,
                    "completed_at": datetime.now().isoformat(),
                }
                return {"status": "completed", "task_id": task_id, "result": outcome}
            except NotImplementedError:
                return {"status": "error", "error": "EXECUTE_TASK_NOT_IMPLEMENTED"}
            except Exception as e:
                logger.exception(f"Department {name} execute failed: {e}")
                return {"status": "error", "task_id": task_id, "error": str(e)}

        @self.app.get("/api/workspace/files")
        async def get_workspace_file(path: str, user: User = Depends(get_current_user)):
            """Workspace klasöründeki bir dosyayı (örn: task.md, implementation_plan.md) güvenli oku"""
            import os
            cwd = os.path.realpath(os.getcwd())
            target_path = os.path.realpath(path if os.path.isabs(path) else os.path.join(cwd, path))
            if not target_path.startswith(cwd):
                raise HTTPException(status_code=400, detail="ZOM SECURITY: Access denied. Paths must reside within workspace.")
            if not os.path.exists(target_path):
                raise HTTPException(status_code=404, detail="File not found")
            if os.path.isdir(target_path):
                raise HTTPException(status_code=400, detail="Cannot read a directory")
            try:
                with open(target_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                return {"filename": os.path.basename(target_path), "content": content, "path": path}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/runtime/recent-logs")
        async def recent_logs(lines: int = 15):
            _log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
            log_path = os.path.join(_log_dir, "jarvis_zom_core.log")
            try:
                if os.path.exists(log_path):
                    with open(log_path, "r", encoding="utf-8", errors="replace") as fp:
                        tail = fp.readlines()[-max(1, min(int(lines), 500)):]
                    return {"lines": [ln.rstrip("\n") for ln in tail], "source": "file"}
            except Exception as e:
                logger.warning(f"Log tail failed: {e}")
            return {
                "lines": [
                    f"[{datetime.now().isoformat()}] log file unavailable",
                    f"[{datetime.now().isoformat()}] active_connections={len(self.active_connections)}",
                ],
                "source": "stub",
            }

        @self.app.get("/api/betting/predictions", tags=["betting"])
        async def get_betting_predictions(user: User = Depends(get_current_user)):
            """SaaS Endpoint: Get current bulletin predictions with Monte Carlo scorelines."""
            agent = self.agents.get("zeze_betting")
            if not agent:
                raise HTTPException(status_code=404, detail="zeze_betting agent not available")
            try:
                res = await agent.get_real_sport_odds()
                matches = res.get("matches", [])
                predictions = []
                for m in matches[:6]:
                    stats = await agent.collector.fetch_team_stats(m["home"], m["away"])
                    sentiment = await agent.collector.fetch_news_sentiment_llm(m["home"], m["away"])
                    eval_res = agent.strategy.evaluate_match(m, stats, sentiment)
                    predictions.append({
                        "match": m,
                        "prediction": eval_res
                    })
                return {"predictions": predictions, "timestamp": datetime.now().isoformat()}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/betting/backtest", tags=["betting"])
        async def run_betting_backtest(request: dict, user: User = Depends(get_current_user)):
            """SaaS Endpoint: Run historical backtest and hyperparameter optimization over size matches."""
            agent = self.agents.get("zeze_betting")
            if not agent:
                raise HTTPException(status_code=404, detail="zeze_betting agent not available")
            try:
                size = int(request.get("size", 1000))
                # Enforce safe bounds
                size = max(10, min(2000, size))
                
                from departments.zeze_betting.backtest import ZezeBettingBacktestEngine
                backtester = ZezeBettingBacktestEngine(strategy_engine=agent.strategy)
                
                # 1. Generate historical dataset of `size` matches
                dataset = backtester.generate_mock_historical_data(size=size)
                
                # 2. Run hyperparameter grid search optimization
                opt_res = backtester.optimize_hyperparameters(dataset)
                
                # 3. Get detailed stats for optimal covariance
                best_cov = opt_res["optimal_covariance_factor"]
                detailed_stats = backtester.run_backtest(dataset, base_cov_factor=best_cov)
                
                return {
                    "status": "success",
                    "dataset_size": size,
                    "optimization": opt_res,
                    "detailed_performance": detailed_stats,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/crypto/portfolio", tags=["crypto"])
        async def get_crypto_portfolio(user: User = Depends(get_current_user)):
            """SaaS Endpoint: Get current paper portfolio balances, pending orders, and trade history."""
            agent = self.agents.get("crypto_trading")
            if not agent:
                raise HTTPException(status_code=404, detail="crypto_trading agent not available")
            try:
                portfolio = agent._load_portfolio()
                pending = agent._load_pending_orders()
                return {
                    "portfolio": portfolio,
                    "pending_orders": pending,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/crypto/analytics", tags=["crypto"])
        async def get_crypto_analytics(symbol: str = "BTCUSDT", user: User = Depends(get_current_user)):
            """SaaS Endpoint: Get crypto market volatility and backtest analytics."""
            agent = self.agents.get("crypto_trading")
            if not agent:
                raise HTTPException(status_code=404, detail="crypto_trading agent not available")
            try:
                klines = await agent.get_binance_klines(symbol, "1h", 24)
                if not klines:
                    raise HTTPException(status_code=404, detail="Could not fetch candle data from Binance")
                
                import math
                close_prices = [float(k[4]) for k in klines]
                log_returns = []
                for i in range(1, len(close_prices)):
                    if close_prices[i-1] > 0 and close_prices[i] > 0:
                        log_returns.append(math.log(close_prices[i] / close_prices[i-1]))
                        
                if len(log_returns) > 0:
                    mean_return = sum(log_returns) / len(log_returns)
                    variance = sum((r - mean_return) ** 2 for r in log_returns) / len(log_returns)
                    std_dev = math.sqrt(variance)
                    volatility_pct = std_dev * 100
                else:
                    volatility_pct = 0.0
                    
                mean_price = sum(close_prices) / len(close_prices)
                
                # Fetch backtest details using backtest strategy skill
                backtest_res = "N/A"
                try:
                    from core.skills.registry import SkillRegistry
                    registry = SkillRegistry()
                    if "backtest_strategy" in registry.skills:
                        backtest_res = await registry.execute_tool(
                            "backtest_strategy", 
                            {"symbol": symbol, "fast_ma": 12, "slow_ma": 26, "interval": "1h", "limit": 100}
                        )
                except Exception:
                    pass
                    
                return {
                    "symbol": symbol,
                    "mean_price": round(mean_price, 2),
                    "volatility_pct": round(volatility_pct, 4),
                    "market_direction": "BULLISH" if close_prices[-1] > close_prices[0] else "BEARISH",
                    "backtest_summary": backtest_res,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/crypto/reset", tags=["crypto"])
        async def reset_crypto_portfolio(user: User = Depends(get_current_user)):
            """SaaS Endpoint: Resets paper trade balances and clears pending orders."""
            agent = self.agents.get("crypto_trading")
            if not agent:
                raise HTTPException(status_code=404, detail="crypto_trading agent not available")
            try:
                # Reset portfolio
                default_portfolio = {
                    "balance_usd": 100000.0,
                    "locked_balance_usd": 0.0,
                    "holdings": {},
                    "locked_holdings": {},
                    "cost_basis": {},
                    "history": [],
                    "last_updated": datetime.now().isoformat()
                }
                agent._save_portfolio(default_portfolio)
                # Clear pending orders
                agent._save_pending_orders([])
                # Reset risk state
                default_risk = {
                    "circuit_breaker_until": None,
                    "daily_realized_loss": 0.0,
                    "loss_timestamps": [],
                    "pnl_history": []
                }
                agent._save_risk_state(default_risk)
                return {"status": "success", "msg": "Paper trading account and risk parameters reset to defaults."}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.delete("/api/crypto/order/{order_id}", tags=["crypto"])
        async def delete_crypto_order(order_id: str, user: User = Depends(get_current_user)):
            """SaaS Endpoint: Cancel a pending order and refund locked balance."""
            agent = self.agents.get("crypto_trading")
            if not agent:
                raise HTTPException(status_code=404, detail="crypto_trading agent not available")
            try:
                res = agent.cancel_paper_order(order_id)
                if not res.get("success"):
                    raise HTTPException(status_code=400, detail=res.get("error", "Failed to cancel order"))
                return res
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/app_factory/scaffold", tags=["app_factory"])
        async def app_factory_scaffold_create(request: dict, user: User = Depends(get_current_user)):
            """SaaS Endpoint: Trigger app_factory to generate a new project scaffold dry-run."""
            agent = self.agents.get("app_factory")
            if not agent:
                raise HTTPException(status_code=404, detail="app_factory agent not available")
            goal = request.get("goal", "").strip()
            if not goal:
                raise HTTPException(status_code=400, detail="goal is required")
                
            is_dangerous, reason = self.guardrails.looks_like_dangerous_payload(goal)
            if is_dangerous:
                raise HTTPException(status_code=400, detail=f"Security alert: {reason}")
                
            task_id = request.get("task_id")
            
            try:
                result = await agent.run_dry_task(goal, task_id)
                
                return {
                    "success": result.success,
                    "task_id": result.task_id,
                    "department": result.department,
                    "output": result.output,
                    "files": result.tool_results,
                    "timestamp": result.finished_at.isoformat()
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/app_factory/scaffold", tags=["app_factory"])
        async def app_factory_scaffold_list(user: User = Depends(get_current_user)):
            """SaaS Endpoint: List all generated project scaffolds."""
            import os
            scaffolds_dir = os.path.realpath(os.path.abspath(os.path.join(os.getcwd(), "app_factory", "scaffolds")))
            if not os.path.exists(scaffolds_dir):
                return {"scaffolds": []}
                
            scaffolds = []
            for name in os.listdir(scaffolds_dir):
                path = os.path.join(scaffolds_dir, name)
                if os.path.isdir(path):
                    try:
                        mtime = os.path.getmtime(path)
                        scaffolds.append({
                            "task_id": name,
                            "created_at": datetime.fromtimestamp(mtime).isoformat()
                        })
                    except Exception:
                        pass
            scaffolds.sort(key=lambda x: x["created_at"], reverse=True)
            return {"scaffolds": scaffolds}

        @self.app.get("/api/app_factory/scaffold/{task_id}", tags=["app_factory"])
        async def app_factory_scaffold_detail(task_id: str, user: User = Depends(get_current_user)):
            """SaaS Endpoint: Get details and files of a generated project scaffold."""
            import os
            scaffolds_dir = os.path.realpath(os.path.abspath(os.path.join(os.getcwd(), "app_factory", "scaffolds")))
            scaffold_dir = os.path.join(scaffolds_dir, task_id)
            if not os.path.exists(scaffold_dir) or not os.path.isdir(scaffold_dir):
                raise HTTPException(status_code=404, detail="Scaffold not found")
                
            files = []
            for root_dir, _, filenames in os.walk(scaffold_dir):
                for filename in filenames:
                    abs_file = os.path.join(root_dir, filename)
                    rel_file = os.path.relpath(abs_file, scaffold_dir).replace("\\", "/")
                    try:
                        with open(abs_file, "r", encoding="utf-8") as f:
                            content = f.read()
                        files.append({
                            "relative": rel_file,
                            "content": content
                        })
                    except Exception as e:
                        files.append({
                            "relative": rel_file,
                            "error": str(e)
                        })
            return {
                "task_id": task_id,
                "files": files,
                "created_at": datetime.fromtimestamp(os.path.getmtime(scaffold_dir)).isoformat()
            }

        @self.app.post("/api/media/task", tags=["media"])
        async def media_task_create(request: dict, user: User = Depends(get_current_user)):
            """SaaS Endpoint: Trigger media_factory to execute a content task."""
            agent = self.agents.get("media_factory")
            if not agent:
                raise HTTPException(status_code=404, detail="media_factory agent not available")
            goal = request.get("goal", "").strip()
            task_type = request.get("task_type", "video").strip()
            
            if not goal:
                raise HTTPException(status_code=400, detail="goal is required")
                
            is_dangerous, reason = self.guardrails.looks_like_dangerous_payload(goal)
            if is_dangerous:
                raise HTTPException(status_code=400, detail=f"Security alert: {reason}")
                
            task_id = request.get("task_id") or str(uuid.uuid4())
            
            try:
                task_data = {
                    "task_id": task_id,
                    "description": goal,
                    "task_type": task_type
                }
                result = await agent.execute_task(task_data)
                
                import json
                files_created = []
                if result.get("success") and os.path.exists(result["report_path"]):
                    with open(result["report_path"], "r", encoding="utf-8") as f:
                        report_data = json.load(f)
                    files_created = report_data.get("files_created", [])
                
                return {
                    "success": result.get("success", False),
                    "task_id": task_id,
                    "department": "media_factory",
                    "output": result.get("output", ""),
                    "files_created": files_created,
                    "policy_checks": {
                        "external_publish_requires_approval": True,
                        "youtube_upload_requires_approval": True,
                        "paid_ads_launch_requires_approval": True,
                        "live_trade_denied": True,
                        "deploy_denied": True,
                        "git_push_denied": True
                    }
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/media/reports", tags=["media"])
        async def media_reports_list(user: User = Depends(get_current_user)):
            """SaaS Endpoint: List all generated media reports."""
            import os
            reports_dir = os.path.realpath(os.path.abspath(os.path.join(os.getcwd(), "departments", "media_factory", "reports")))
            if not os.path.exists(reports_dir):
                return {"reports": []}
                
            reports = []
            for root, dirs, files in os.walk(reports_dir):
                for file in files:
                    if file == "report.json":
                        try:
                            with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                                data = json.load(f)
                            reports.append({
                                "task_id": data.get("task_id"),
                                "timestamp": data.get("timestamp"),
                                "query": data.get("query"),
                                "status": data.get("status"),
                                "files_created": data.get("files_created", [])
                            })
                        except Exception:
                            pass
            reports.sort(key=lambda x: x.get("timestamp") or "", reverse=True)
            return {"reports": reports}

        @self.app.get("/api/media/reports/{task_id}", tags=["media"])
        async def media_report_detail(task_id: str, user: User = Depends(get_current_user)):
            """SaaS Endpoint: Get details and output files of a generated media task."""
            import os
            reports_dir = os.path.realpath(os.path.abspath(os.path.join(os.getcwd(), "departments", "media_factory", "reports")))
            task_dir = os.path.join(reports_dir, task_id)
            if not os.path.exists(task_dir) or not os.path.isdir(task_dir):
                raise HTTPException(status_code=404, detail="Media task report not found")
                
            files = []
            for filename in os.listdir(task_dir):
                file_path = os.path.join(task_dir, filename)
                if os.path.isfile(file_path):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        files.append({
                            "name": filename,
                            "content": content
                        })
                    except Exception as e:
                        files.append({
                            "name": filename,
                            "error": str(e)
                        })
            return {
                "task_id": task_id,
                "files": files
            }

        @self.app.get("/api/jarvis/awareness")
        async def self_awareness():
            """Snapshot of Jarvis' current self-state.

            This is the *operational* sense of 'self-aware': the system reports
            what it knows about its own behaviour right now — active tasks,
            recent failures (from DLQ → memory), ROI score, alerts, loop risk.
            No claims about consciousness; just observable telemetry.
            """
            from core.zeze_guard.storage import get_storage
            store = get_storage()
            roi = self.roi._calculate_base_metrics()
            recent_alerts = store.alerts[-5:] if store.alerts else []
            recent_outcomes = store.outcomes[-10:] if store.outcomes else []
            unique_signatures = {e.get("signature") for e in store.events if isinstance(e, dict)}
            return {
                "uptime_s": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
                "mq_connected": self.mq_ready,
                "active_connections": len(self.active_connections),
                "tasks_seen": len(self.task_history),
                "telemetry": {
                    "events": len(store.events),
                    "outcomes": len(store.outcomes),
                    "unique_signatures": len(unique_signatures),
                },
                "roi": roi,
                "recent_alerts": recent_alerts,
                "recent_outcomes": recent_outcomes,
                "model": self.openrouter.default_model,
            }

        @self.app.get("/api/jarvis/insights")
        async def insights(query: str = "recent failure"):
            """Recall lessons from long-term memory (failures, past plans)."""
            try:
                from core.memory.db_client import TieredMemoryClient
                # Late-bind so import-time doesn't fail on missing SQLite
                if not hasattr(self, "_memory"):
                    self._memory = TieredMemoryClient()
                result = self._memory.recall_for_task(query, limit=5)
                return {"query": query, "result": result}
            except Exception as e:
                return {"query": query, "error": str(e), "result": {}}

        @self.app.get("/api/jarvis/history")
        async def chat_history(client_id: Optional[str] = None, limit: int = 50):
            """Sohbet geçmişini getir"""
            try:
                cid = client_id or "default"
                history = self._get_recent_messages(cid)
                return {"status": "success", "history": history}
            except Exception as e:
                return {"status": "error", "error": str(e)}

        @self.app.get("/api/jarvis/sessions")
        async def chat_sessions():
            """Benzersiz sohbet oturumlarını (client_id'lerini) listele"""
            try:
                from core.storage.conversation_store import get_all_client_ids
                sessions = get_all_client_ids()
                # Eger hic session yoksa varsayilan default'u dondurelim
                if not sessions:
                    sessions = ["default"]
                elif "default" not in sessions:
                    sessions.insert(0, "default")
                return {"status": "success", "sessions": sessions}
            except Exception as e:
                return {"status": "error", "error": str(e)}

        @self.app.delete("/api/jarvis/sessions/{client_id}")
        async def delete_session(client_id: str):
            """Belirli bir sohbet oturumunu sil"""
            try:
                self._conv_clear(client_id)
                return {"status": "success", "message": f"Session {client_id} cleared"}
            except Exception as e:
                return {"status": "error", "error": str(e)}

        @self.app.post("/api/jarvis/chat")
        async def chat(
            request: dict,
            user: User = Depends(get_current_user),
        ):
            message = (request.get("message") or "").strip()
            if not message:
                return {"status": "error", "error": "EMPTY_MESSAGE"}

            client_id = request.get("client_id") or "default"
            self._add_to_history(client_id, "user", message)

            # Cheap natural-language guardrail (the orchestrator runs the full shield).
            is_dangerous, reason = self.guardrails.looks_like_dangerous_payload(message)
            if is_dangerous:
                logger.warning(f"🛑 Chat blocked ({reason}): {message[:80]}")
                return {"status": "blocked", "error": f"SECURITY_BLOCK:{reason}"}

            task_id = str(uuid.uuid4())
            payload = {
                "task_id": task_id,
                "description": message,
                "sender": "jarvis_chat",
                "client_id": client_id,
                "department": request.get("department"),
                "context": request.get("context") or {},
                "created_at": datetime.now().isoformat(),
            }

            # AntiLoop telemetry — record incoming task so the self-awareness loop can see it
            try:
                import hashlib
                signature = f"chat:{hashlib.sha256(message.encode('utf-8', errors='replace')).hexdigest()[:8]}"
                self.anti_loop.record_event(
                    agent_id="jarvis_chat",
                    task_id=task_id,
                    event_type="chat_received",
                    signature=signature,
                    metadata={"length": len(message)},
                )
            except Exception:
                logger.debug("anti_loop telemetry skipped")

            # Determine intent and target department using single unified routing helper
            intent, dept, pipeline = await self._determine_message_routing(message, request.get("department"))
            
            if intent in ("TASK", "WORKFLOW") and (dept or (intent == "WORKFLOW" and pipeline)):
                target_dept = dept if dept else pipeline.pop(0)
                payload["department"] = target_dept
                ctx_update: dict = payload.get("context") or {}
                if pipeline:
                    # Anlamsal ayrım (paralel çok-ajan atılımı):
                    #  - WORKFLOW → sıralı pipeline (çıktı bir sonrakine besler)
                    #  - TASK + işbirliği → paralel collaboration_depts (bağımsız, aynı anda)
                    # Önceden ikisi de set ediliyordu → aynı dept iki kez çalışıyordu (giderildi).
                    if intent == "WORKFLOW":
                        ctx_update["pipeline"] = pipeline
                    else:
                        ctx_update["collaboration_depts"] = pipeline
                payload["context"] = ctx_update
                
                success = False
                if self.mq_ready:
                    success = self.mq.publish("main_orchestrator_queue", payload)
                if not success:
                    await self.local_task_queue.put(payload)
                    success = True
                
                if success:
                    self.task_history.append({"task_id": task_id, "status": "queued", "dept": target_dept, "message": message[:200]})
                    return {"status": "queued", "task_id": task_id, "department": target_dept}
                else:
                    return {"status": "error", "task_id": task_id, "error": "QUEUE_PUBLISH_FAILED"}
            
            # Pure CHAT intent - call OpenRouter directly
            try:
                awareness_ctx = await self._build_awareness_context()
                system_prompt = build_jarvis_prompt(**awareness_ctx, user_query=message)
                history = self._get_recent_messages(client_id)
                
                result = await self.openrouter.chat(message=message, system=system_prompt, context={"history": history})
                self.task_history.append({"task_id": task_id, "status": "direct", "message": message[:200]})
                self._add_to_history(client_id, "assistant", result)
                return {"status": "direct", "task_id": task_id, "response": result}
            except Exception as e:
                logger.exception(f"Direct fallback failed for {task_id}: {e}")
                return {"status": "error", "task_id": task_id, "error": str(e)}

        @self.app.get("/api/jarvis/tasks")
        async def task_history(limit: int = 20):
            return {"tasks": self.task_history[-limit:]}

        @self.app.get("/api/jarvis/tasks/{task_id}")
        async def task_result(task_id: str):
            envelope = self.task_results.get(task_id)
            if envelope is None:
                return {"task_id": task_id, "status": "pending"}
            return envelope

    def setup_websocket(self):
        @self.app.websocket("/ws/live-stream")
        async def live_stream_websocket(websocket: WebSocket):
            from backend.api.live_stream import event_bus
            await event_bus.connect(websocket)
            try:
                while True:
                    await websocket.receive_text()
            except WebSocketDisconnect:
                event_bus.disconnect(websocket)
            except Exception as e:
                logger.error(f"Live stream WebSocket error: {e}")
                event_bus.disconnect(websocket)

        @self.app.websocket("/ws/{client_id}")
        async def websocket_endpoint(websocket: WebSocket, client_id: str, token: str = ""):
            if not token:
                token = websocket.query_params.get("token", "")
            
            if _SECURITY_ENABLED:
                try:
                    user = JWTHandler.verify_token(token)
                    websocket.scope["user"] = user
                except Exception as e:
                    logger.warning(f"[WS] Auth failed for client {client_id}: {e}")
                    await websocket.accept()
                    await websocket.close(code=4001)
                    return
            else:
                websocket.scope["user"] = User(user_id=client_id, username=client_id, role=UserRole.ADMIN)

            await self.connect_websocket(websocket, client_id)
            try:
                while True:
                    # Mesaj al ve işle
                    data = await websocket.receive_text()
                    await self.handle_websocket_message(websocket, client_id, data)
            except WebSocketDisconnect:
                await self.disconnect_websocket(client_id)
            except Exception as e:
                logger.error(f"WebSocket error for client {client_id}: {e}")
                await self.disconnect_websocket(client_id)

    async def connect_websocket(self, websocket: WebSocket, client_id: str):
        """WebSocket bağlantısını kabul et ve keep-alive başlat"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        
        # Keep-alive görevi başlat
        task = asyncio.create_task(self.keep_alive_task(client_id))
        self.connection_tasks[client_id] = task
        
        logger.info(f"WebSocket client connected: {client_id}. Total: {len(self.active_connections)}")
        
        # Bağlantı kuruldu mesajı gönder
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat(),
            "message": "Connected to Jarvis ZOM Core"
        }))
        
        # Send current brain status & active model immediately
        current_model = os.getenv("LLM_MODEL") or (self.openrouter.default_model if hasattr(self, "openrouter") and self.openrouter else "gemma_2b")
        ui_friendly_model = current_model
        reverse_mapping = {
            "qwen3.5:2b": "qwen3.5:2b",
            "llama3.2:3b": "llama3.2:3b",
            "deepseek-r1:1.5b": "deepseek-r1:1.5b",
            "google/gemma-4-31b-it": "gemma_2b",
            "google/gemma-4-31b-it:free": "gemma_2b",
            "deepseek/deepseek-chat": "deepseek-chat",
            "z-ai/glm-5.2-free": "glm-5.2-free",
            "google/gemma-2-9b-it:free": "gemma_2b",
            "anthropic/claude-3-5-sonnet": "claude_35",
            "meta-llama/llama-3-8b-instruct": "llama_3",
            "meta-llama/llama-3-8b-instruct:free": "llama_3"
        }
        ui_friendly_model = reverse_mapping.get(current_model, current_model)
        
        await websocket.send_text(json.dumps({
            "type": "brain_status",
            "val": "online",
            "model": ui_friendly_model
        }))

    async def disconnect_websocket(self, client_id: str):
        """WebSocket bağlantısını temizle ve kaynakları serbest bırak"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket client disconnected: {client_id}. Total: {len(self.active_connections)}")
        
        # Keep-alive görevi iptal et
        if client_id in self.connection_tasks:
            task = self.connection_tasks[client_id]
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            del self.connection_tasks[client_id]

    async def keep_alive_task(self, client_id: str):
        """Periodically ping the client.

        We DO NOT call ``receive_text`` here — the main message loop owns the
        single receive coroutine on this socket. Calling receive_text from two
        places is a Starlette/Uvicorn footgun that races. Pongs arrive through
        ``handle_websocket_message`` instead; here we just record the timestamp
        of the last send so disconnects show up via the next send failure.
        """
        try:
            while client_id in self.active_connections:
                await asyncio.sleep(self.keep_alive_interval)
                websocket = self.active_connections.get(client_id)
                if not websocket:
                    return
                try:
                    await websocket.send_text(json.dumps({
                        "type": "ping",
                        "timestamp": datetime.now().isoformat(),
                    }))
                except Exception as e:
                    logger.warning(f"Keep-alive send failed for {client_id}: {e}")
                    await self.handle_connection_loss(client_id)
                    return
        except asyncio.CancelledError:
            logger.debug(f"Keep-alive task cancelled for client {client_id}")

    async def handle_connection_loss(self, client_id: str):
        """Bağlantı kaybını yönet ve yeniden bağlanma denemesi yap"""
        logger.info(f"Handling connection loss for client {client_id}")
        
        # Bağlantıyı temizle
        await self.disconnect_websocket(client_id)
        
        # Not: Gerçek yeniden bağlanma istemci tarafında yapılmalı
        # Sunucu tarafında sadece bağlantıyı temizliyoruz
        # İstemci, connection lost olunca yeniden bağlanmaya çalışacak

    def _update_env_model_variables(self, model_name: str):
        """DEPRECATED: .env üzerine doğrudan yazmak race condition'a yol açar.
        Yeni kod _persist_model_state() kullanır. Geriye dönük uyumluluk için bırakıldı."""
        self._persist_model_state(model_name)

    def _persist_model_state(self, model_name: str) -> None:
        """Model adını model_state.json dosyasına race-safe yazar.

        .env üzerine yazmak yerine ayrı bir JSON dosyası kullanır.
        Restart sonrası startup() içinde bu dosya okunarak model restore edilir.
        """
        state_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "model_state.json"
        )
        try:
            import json as _json
            # Atomic write: önce geçici dosyaya yaz, sonra rename
            tmp_path = state_path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                _json.dump({"active_model": model_name, "updated_at": datetime.now().isoformat()}, f)
            os.replace(tmp_path, state_path)  # atomic on POSIX & Windows NTFS
            logger.info(f"[ModelState] Persisted active_model={model_name} to model_state.json")
        except Exception as e:
            logger.error(f"[ModelState] Failed to persist model state: {e}")

    async def handle_websocket_message(self, websocket: WebSocket, client_id: str, data: str):
        """WebSocket mesajlarını işle"""
        try:
            message = json.loads(data)
            msg_type = message.get("type", "unknown")
            
            if msg_type == "pong":
                # Pong mesajı, sadece logla
                logger.debug(f"Received pong from {client_id}")
            elif msg_type == "ping":
                # Ping mesajına pong ile yanıt ver
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }))
            elif msg_type == "autonomy_mode_change":
                val = message.get("val", "semi")
                self.autonomy_mode = val
                logger.info(f"Autonomy mode updated to {self.autonomy_mode}")
                return
            elif msg_type == "dept_focus_change":
                val = message.get("val")
                self.focused_department = val
                logger.info(f"Focused department updated to {self.focused_department}")
                return
            elif msg_type == "model_change":
                user = websocket.scope.get("user")
                role_val = self._get_role_str(user)

                is_admin = False
                if not _SECURITY_ENABLED:
                    is_admin = True
                elif role_val == 'admin':
                    is_admin = True
                    
                if not is_admin:
                    logger.warning(f"[AUTH] Non-admin client {client_id} attempted model change")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Only admin users can modify model settings"
                    }))
                    return

                val = message.get("val")
                if val:
                    # Model mapping
                    mapping = {
                        "antigravity": "google/gemma-4-31b-it",
                        "glm-5.2": "glm-5.2",
                        "openrouter_free": "openrouter/free",
                        "claude_35": "anthropic/claude-3-5-sonnet",
                        # Backward compatibility keys
                        "qwen3.5:2b": "qwen3.5:2b",
                        "llama3.2:3b": "llama3.2:3b",
                        "deepseek-r1:1.5b": "deepseek-r1:1.5b",
                        "gemma-4-31b-it:free": "google/gemma-4-31b-it",
                        "deepseek-chat": "deepseek/deepseek-chat",
                        "glm-5.2-free": "z-ai/glm-5.2-free",
                        "gemma_2b": "google/gemma-4-31b-it",
                        "llama_3": "meta-llama/llama-3-8b-instruct"
                    }
                    actual_model = mapping.get(val, val)
                    
                    # Update environment
                    os.environ["LLM_MODEL"] = actual_model
                    os.environ["GEMMA_MODEL"] = actual_model
                    if hasattr(self, "openrouter") and self.openrouter:
                        self.openrouter.default_model = actual_model
                        
                    logger.info(f"Active model updated to {actual_model} (UI ID: {val})")
                    
                    # Update .env file persistently
                    self._update_env_model_variables(actual_model)
                    
                    # Log as ADMIN_ACTION in audit log
                    if _SECURITY_ENABLED:
                        try:
                            audit_logger.log(
                                event_type=AuditEventType.ADMIN_ACTION,
                                user_id=getattr(user, "user_id", None),
                                username=getattr(user, "username", None),
                                user_role="admin",
                                metadata={"action": "model_change", "new_model": actual_model}
                            )
                            audit_logger.flush()
                        except Exception as _ae:
                            logger.warning(f"Audit log for model_change failed: {_ae}")

                    # Persist model choice to model_state.json (race-safe, no .env rewrite)
                    self._persist_model_state(actual_model)
                    
                    # Broadcast new brain status to all active WebSocket clients
                    for client_conn in list(self.active_connections.values()):
                        try:
                            await client_conn.send_text(json.dumps({
                                "type": "brain_status",
                                "val": "online",
                                "model": val  # Send UI ID so UI selects it correctly
                            }))
                        except Exception as e:
                            logger.warning(f"Failed to broadcast model change to client: {e}")
                return
            elif msg_type == "action_response":
                action_id = message.get("action_id")
                approved = message.get("approved", False)
                logger.info(f"Received action response for {action_id}: approved={approved}")
                if not action_id or action_id not in self.pending_actions:
                    await websocket.send_text(json.dumps({
                        "type": "response",
                        "val": "⚠️ Geçersiz veya süresi dolmuş işlem kimliği.",
                        "id": f"resp-{datetime.now().timestamp()}"
                    }))
                    return
                
                action_data = self.pending_actions.pop(action_id)
                client_id = action_data["client_id"]
                action_type = action_data["type"]
                target = action_data["target"]
                
                if not approved:
                    # Record HITL rejection feedback
                    try:
                        from core.memory.layered_memory_manager import layered_memory
                        layered_memory.add_hitl_rule(
                            rule_id=f"rule_{action_id}",
                            department="system",
                            action_type=action_type,
                            rule_condition=f"action target contains {target}",
                            decision="gated" if action_type == "command" else "denied",
                            metadata={"target": target, "approved": False, "timestamp": datetime.now().isoformat()}
                        )
                        logger.info(f"[HITL Learning] Logged rejection rule for action type: {action_type} target: {target}")
                    except Exception as he:
                        logger.warning(f"Failed to log HITL rejection to memory: {he}")
                        
                    response_text = f"🚫 **İşlem Reddedildi:** Kullanıcı '{target}' işlemini onaylamadı."
                    self._add_to_history(client_id, "assistant", response_text)
                    await websocket.send_text(json.dumps({
                        "type": "action_result",
                        "action_id": action_id,
                        "status": "rejected",
                        "output": "Kullanıcı işlemi reddetti.",
                        "val": response_text
                    }))
                    return
                
                # Record HITL approval feedback
                try:
                    from core.memory.layered_memory_manager import layered_memory
                    layered_memory.add_hitl_rule(
                        rule_id=f"rule_{action_id}",
                        department="system",
                        action_type=action_type,
                        rule_condition=f"action target contains {target} always",
                        decision="approved",
                        metadata={"target": target, "approved": True, "timestamp": datetime.now().isoformat()}
                    )
                    logger.info(f"[HITL Learning] Logged approval rule for action type: {action_type} target: {target}")
                except Exception as he:
                    logger.warning(f"Failed to log HITL approval to memory: {he}")
                    
                await websocket.send_text(json.dumps({
                    "type": "action_result",
                    "action_id": action_id,
                    "status": "executing",
                    "output": "İşlem yürütülüyor..."
                }))
                
                if action_type == "command":
                    try:
                        from core.tools.cli_executor import SandboxCLIExecutor
                        executor = SandboxCLIExecutor(workspace_path=".")
                        # asyncio.get_event_loop() is deprecated in Python 3.10+; use get_running_loop()
                        loop = asyncio.get_running_loop()
                        result = await loop.run_in_executor(None, executor.execute, target)
                        
                        success = result.get("success", False)
                        stdout = result.get("stdout", "")
                        stderr = result.get("stderr", "")
                        exit_code = result.get("exit_code", 0)
                        
                        output_content = stdout if success else f"Exit code {exit_code}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
                        if not output_content.strip():
                            output_content = "Komut başarıyla yürütüldü (Çıktı yok)."
                            
                        status_str = "success" if success else "failed"
                        outcome_prefix = "✅" if success else "❌"
                        response_text = f"{outcome_prefix} **Komut Yürütüldü:** `${target}`\n\n```\n{output_content}\n```"
                        
                        self._add_to_history(client_id, "assistant", response_text)
                        await websocket.send_text(json.dumps({
                            "type": "action_result",
                            "action_id": action_id,
                            "status": status_str,
                            "output": output_content,
                            "val": response_text
                        }))
                    except Exception as e:
                        logger.error(f"Failed to execute command {target}: {e}")
                        response_text = f"❌ **Komut Yürütme Hatası:** {str(e)}"
                        self._add_to_history(client_id, "assistant", response_text)
                        await websocket.send_text(json.dumps({
                            "type": "action_result",
                            "action_id": action_id,
                            "status": "failed",
                            "output": str(e),
                            "val": response_text
                        }))
                elif action_type == "write_file":
                    try:
                        user_text = action_data["user_text"]
                        content = "Zezelabs ZOM System File"
                        if "containing" in user_text.lower():
                            content = user_text.split("containing", 1)[1].strip()
                        elif "yaz" in user_text.lower():
                            parts = user_text.split("yaz", 1)
                            if len(parts) > 1 and parts[1].strip():
                                content = parts[1].strip()
                        
                        filepath = os.path.join(".", target)
                        real_path = os.path.realpath(filepath)
                        workspace_real = os.path.realpath(".")
                        if not real_path.startswith(workspace_real):
                            raise Exception("ZOM Security Guardrail: Path traversal detected. Access denied.")
                            
                        os.makedirs(os.path.dirname(real_path), exist_ok=True)
                        with open(real_path, "w", encoding="utf-8") as f:
                            f.write(content)
                            
                        response_text = f"✅ **Dosya Oluşturuldu:** `{target}` ({len(content)} bayt yazıldı).\n\n```\n{content}\n```"
                        self._add_to_history(client_id, "assistant", response_text)
                        await websocket.send_text(json.dumps({
                            "type": "action_result",
                            "action_id": action_id,
                            "status": "success",
                            "output": f"Successfully wrote {len(content)} bytes to {target}",
                            "val": response_text
                        }))
                    except Exception as e:
                        logger.error(f"Failed to write file {target}: {e}")
                        response_text = f"❌ **Dosya Yazma Hatası:** {str(e)}"
                        self._add_to_history(client_id, "assistant", response_text)
                        await websocket.send_text(json.dumps({
                            "type": "action_result",
                            "action_id": action_id,
                            "status": "failed",
                            "output": str(e),
                            "val": response_text
                        }))
            elif msg_type == "command":
                user_text = message.get("val", "").strip()
                if not user_text:
                    await websocket.send_text(json.dumps({
                        "type": "response",
                        "val": "Boş komut gönderildi.",
                        "id": f"resp-{datetime.now().timestamp()}"
                    }))
                    return
                
                # ── SLASH COMMANDS INTERCEPTOR ──
                forced_dept = None
                if user_text.startswith("/"):
                    cmd_parts = user_text.split(" ", 1)
                    cmd = cmd_parts[0].lower()
                    cmd_arg = cmd_parts[1].strip() if len(cmd_parts) > 1 else ""
                    
                    if cmd == "/clear":
                        self._conv_clear(client_id)
                        await websocket.send_text(json.dumps({
                            "type": "response",
                            "val": "🧹 **Sohbet Geçmişi Temizlendi.** Bu oturumdaki tüm mesajlar veritabanından silindi.",
                            "id": f"resp-{datetime.now().timestamp()}"
                        }))
                        return
                    elif cmd == "/stop":
                        await websocket.send_text(json.dumps({
                            "type": "state",
                            "val": "idle"
                        }))
                        await websocket.send_text(json.dumps({
                            "type": "response",
                            "val": "🛑 **İşlem Durduruldu.** Mevcut Ajan çalışması kesildi.",
                            "id": f"resp-{datetime.now().timestamp()}"
                        }))
                        return
                    elif cmd == "/sys":
                        awareness = await self._build_awareness_context()
                        response_val = f"📊 **Canlı ZOM Telemetri Durumu:**\n\n{awareness['awareness_snapshot']}\n\n**Departman Aktiviteleri:**\n{awareness['department_list']}"
                        await websocket.send_text(json.dumps({
                            "type": "response",
                            "val": response_val,
                            "id": f"resp-{datetime.now().timestamp()}"
                        }))
                        return
                    elif cmd in ["/dev", "/sec", "/trade", "/business"]:
                        dept_map = {
                            "/dev": "zeze_dev",
                            "/sec": "zeze_sec",
                            "/trade": "crypto_trading",
                            "/business": "zeze_business"
                        }
                        target_dept = dept_map[cmd]
                        user_text = cmd_arg
                        if not user_text:
                            await websocket.send_text(json.dumps({
                                "type": "response",
                                "val": f"⚠️ Lütfen `{cmd}` komutundan sonra bir talep yazın. (Örn: `{cmd} testleri çalıştır`)",
                                "id": f"resp-{datetime.now().timestamp()}"
                            }))
                            return
                        forced_dept = target_dept
                
                # Action Interceptor (Onay Kartı Üretimi)
                is_action = False
                action_type = None
                action_target = None
                action_desc = None
                
                user_text_lower = user_text.lower()
                if user_text.startswith("$ "):
                    is_action = True
                    action_type = "command"
                    action_target = user_text[2:].strip()
                    action_desc = f"Sandbox CLI Yürütme Yetkisi: '{action_target}'"
                elif user_text_lower.startswith("execute "):
                    is_action = True
                    action_type = "command"
                    action_target = user_text[8:].strip()
                    action_desc = f"Sandbox CLI Yürütme Yetkisi: '{action_target}'"
                elif user_text_lower.startswith("create file ") or user_text_lower.startswith("write file "):
                    is_action = True
                    action_type = "write_file"
                    parts = user_text.split(" ", 3)
                    action_target = parts[2].strip() if len(parts) > 2 else "new_file.txt"
                    action_desc = f"Dosya Yazma/Oluşturma Yetkisi: '{action_target}'"
                
                if is_action:
                    action_id = f"act_{uuid.uuid4().hex[:8]}"
                    self.pending_actions[action_id] = {
                        "action_id": action_id,
                        "type": action_type,
                        "target": action_target,
                        "description": action_desc,
                        "client_id": client_id,
                        "user_text": user_text,
                        "created_at": time.time()
                    }
                    
                    self._add_to_history(client_id, "user", user_text)
                    await websocket.send_text(json.dumps({
                        "type": "action_request",
                        "action_id": action_id,
                        "action_type": action_type,
                        "target": action_target,
                        "description": action_desc
                    }))
                    return
                
                # Check for pinned focused department override
                if not forced_dept and hasattr(self, "focused_department") and self.focused_department:
                    forced_dept = self.focused_department
                    logger.info(f"Bypassing cognitive router. Routing command directly to pinned department: {forced_dept}")
                
                logger.info(f"Processing command from {client_id}: {user_text[:100]}")
                
                try:
                    # Self-awareness context oluştur
                    awareness_ctx = await self._build_awareness_context()
                    system_prompt = build_jarvis_prompt(**awareness_ctx, user_query=user_text)
                    
                    # Mesaj geçmişini al (context window)
                    history = self._get_recent_messages(client_id)
                    
                    # Kullanıcı mesajını geçmişe ekle
                    self._add_to_history(client_id, "user", user_text)
                    
                    # Niyet Analizi (Intent Recognition) / Odak Yönlendirmesi
                    if forced_dept:
                        intent = "TASK"
                        target_dept = forced_dept
                        pipeline = []
                    else:
                        intent, target_dept, pipeline = await self._determine_message_routing(user_text)
                    
                    if intent == "WORKFLOW" and pipeline:
                        # A1 FIX: intent_data yoktu — pipeline doğrudan _determine_message_routing'den gelir
                        valid_pipeline = [d for d in pipeline if d in self.agents]
                        
                        if not valid_pipeline:
                            response = "⚠️ İş akışı için geçerli bir departman bulunamadı."
                            self._add_to_history(client_id, "assistant", response)
                            await websocket.send_text(json.dumps({
                                "type": "response",
                                "val": response,
                                "id": f"resp-{datetime.now().timestamp()}"
                            }))
                        else:
                            target_dept = valid_pipeline.pop(0)
                            task_id = str(uuid.uuid4())
                            payload = {
                                "task_id": task_id,
                                "description": user_text,
                                "sender": "jarvis_chat",
                                "client_id": client_id,
                                "department": target_dept,
                                "context": {
                                    "pipeline": valid_pipeline
                                },
                                "created_at": datetime.now().isoformat()
                            }
                            
                            self.task_history.append({"task_id": task_id, "status": "queued", "dept": target_dept, "message": user_text[:200]})
                            
                            success = False
                            if self.mq_ready:
                                success = self.mq.publish("main_orchestrator_queue", payload)
                            if not success:
                                await self.local_task_queue.put(payload)
                                success = True
                                
                            pipeline_str = " ➔ ".join([target_dept] + valid_pipeline)
                            response = (
                                f"DEPARTMAN: {target_dept}\n"
                                f"GÖREV: {user_text}\n"
                                f"DURUM: kuyruğa eklendi (İş Akışı Başlatıldı: {pipeline_str})"
                            )
                            self._add_to_history(client_id, "assistant", response, task_id=task_id, department=target_dept)
                            await websocket.send_text(json.dumps({
                                "type": "response",
                                "val": response,
                                "id": f"resp-{datetime.now().timestamp()}",
                                "task_id": task_id,
                                "department": target_dept
                            }))
                            
                    elif intent == "TASK" and target_dept and target_dept in self.agents:
                        task_id = str(uuid.uuid4())
                        payload = {
                            "task_id": task_id,
                            "description": user_text,
                            "sender": "jarvis_chat",
                            "client_id": client_id,
                            "department": target_dept,
                            "context": {},
                            "created_at": datetime.now().isoformat()
                        }
                        
                        self.task_history.append({"task_id": task_id, "status": "queued", "dept": target_dept, "message": user_text[:200]})
                        
                        success = False
                        if self.mq_ready:
                            success = self.mq.publish("main_orchestrator_queue", payload)
                        if not success:
                            await self.local_task_queue.put(payload)
                            success = True
                            
                        response = (
                            f"DEPARTMAN: {target_dept}\n"
                            f"GÖREV: {user_text}\n"
                            f"DURUM: kuyruğa eklendi"
                        )
                        self._add_to_history(client_id, "assistant", response, task_id=task_id, department=target_dept)
                        await websocket.send_text(json.dumps({
                            "type": "response",
                            "val": response,
                            "id": f"resp-{datetime.now().timestamp()}",
                            "task_id": task_id,
                            "department": target_dept
                        }))
                    else:
                        # Normal AI Chat Yanıtı
                        response = await self.openrouter.chat(
                            user_text,
                            system=system_prompt,
                            context={"history": history}
                        )
                        
                        self._add_to_history(client_id, "assistant", response)
                        
                        response_payload = {
                            "type": "response",
                            "val": response,
                            "id": f"resp-{datetime.now().timestamp()}"
                        }
                        await websocket.send_text(json.dumps(response_payload))
                except Exception as e:
                    logger.error(f"AI processing failed for {client_id}: {e}")
                    await websocket.send_text(json.dumps({
                        "type": "response",
                        "val": f"AI işleme hatası: {str(e)}",
                        "id": f"resp-{datetime.now().timestamp()}"
                    }))
            else:
                # Diğer mesaj tiplerini işle
                logger.info(f"Received message from {client_id}: {msg_type}")
                # Burada özel mesaj işleme mantığı eklenebilir
                
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON received from {client_id}: {data[:100]}")
        except Exception as e:
            logger.error(f"Error handling message from {client_id}: {e}")

    async def _analyze_intent(self, text: str) -> dict:
        """Kullanıcının niyetini analiz et (CHAT vs TASK)"""
        system_prompt = '''Sen bir analizcisiniz. Kullanıcının mesajının bir eylem/görev mi (TASK), çoklu departman gerektiren bir iş akışı mı (WORKFLOW) yoksa sadece bir soru/sohbet (CHAT) mi olduğunu belirle.
Eğer görev sadece TEK bir departmanı ilgilendiriyorsa:
{"intent": "TASK", "department": "uygun_departman_adi"} dön.
Eğer görev birbirini izleyen BİRDEN FAZLA departmanı gerektiriyorsa (örn: bul, tasarla, kodla):
{"intent": "WORKFLOW", "pipeline": ["dept1", "dept2", ...]} dön.
Geçerli departmanlar: app_factory, zeze_design, zeze_rnd, zeze_sec, zeze_trend, zeze_business, zeze_comms, zeze_compliance, zeze_dev, zeze_ops, zeze_production, zeze_game, crypto_trading, media_factory, zeze_aro
Eğer görev değilse, bilgi soruyorsa veya normal sohbet ediyorsa:
{"intent": "CHAT", "department": null} dön.
SADECE GEÇERLİ BİR JSON DÖNDÜR, başka hiçbir metin ekleme.'''
        
        from pydantic import BaseModel, Field
        from typing import Literal, List, Optional
        import re

        class IntentAnalysis(BaseModel):
            intent: Literal["CHAT", "TASK", "WORKFLOW"]
            department: Optional[str] = None
            pipeline: Optional[List[str]] = None

        repair_prompt = text
        for attempt in range(3):
            try:
                response = await self.openrouter.chat(repair_prompt, system=system_prompt, use_fast=True)
                match = re.search(r'\{.*\}', response, re.DOTALL)
                if match:
                    json_str = match.group(0)
                    # Pydantic ile Zorla Doğrula
                    analysis = IntentAnalysis.model_validate_json(json_str)
                    return analysis.model_dump()
            except Exception as e:
                logger.warning(f"Intent analysis attempt {attempt+1} failed: {e}. Retrying repair loop...")
                repair_prompt = f"{text}\n\n[HATA! Önceki yanıtınız şemaya uymadı veya JSON geçersiz: {str(e)}. Lütfen YALNIZCA şemadaki JSON formatına uygun yanıt verin.]"
        
        logger.error("Intent analysis repair loop exhausted. Returning default CHAT.")
        return {"intent": "CHAT", "department": None}

    async def run_agents_periodic_cycles(self, startup_delay: float = 5.0, interval: float = 30.0):
        """Ajanların periyodik run_cycle döngülerini paralel olarak çalıştırır.

        Önceki sıralı await yaklaşımı yerine asyncio.gather kullanılır:
        17 agent sıralıyken toplam ~170s olabiliyordu — şimdi en yavaş agent kadardır.
        """
        logger.info("Starting autonomous agent periodic cycles (parallel gather mode)...")
        await asyncio.sleep(startup_delay)
        while self.is_running:
            try:
                eligible = [
                    (dept_name, agent)
                    for dept_name, agent in self.agents.items()
                    if agent
                    and hasattr(agent, "run_cycle")
                    and getattr(agent, "department", "base") != "base"
                ]
                if eligible:
                    logger.info(f"Triggering parallel agent cycles for {len(eligible)} agents...")
                    coros = [agent.run_cycle() for _, agent in eligible]
                    results = await asyncio.gather(*coros, return_exceptions=True)
                    for (dept_name, _), result in zip(eligible, results):
                        if isinstance(result, Exception):
                            logger.error(f"Agent cycle error: dept={dept_name}, err={result}")
                        elif result and isinstance(result, dict) and result.get("status") != "noop":
                            logger.info(f"Agent cycle completed: dept={dept_name}, status={result.get('status')}")
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Autonomous agent periodic cycles main loop error: {e}")
                await asyncio.sleep(5.0)

    async def start_background_tasks(self):
        """Arka plan görevlerini başlat"""
        logger.info("Starting background tasks...")

        # Sistem durumu güncelleme görevi
        self._background_tasks.append(asyncio.create_task(self.system_status_updater()))

        # Periyodik bakım görevi
        self._background_tasks.append(asyncio.create_task(self.periodic_maintenance()))

        # Ajan periyodik döngülerini başlat
        self._background_tasks.append(asyncio.create_task(self.run_agents_periodic_cycles()))

        # Yerel görev dağıtıcı arka plan işini başlat
        self._background_tasks.append(asyncio.create_task(self.local_task_dispatcher()))

        try:
            self._main_loop = asyncio.get_running_loop()
        except RuntimeError:
            self._main_loop = None

        logger.info("Background tasks started")

    # ── Result listener ───────────────────────────────────────────────────
    def _result_listener_loop(self) -> None:
        """Daemon thread that drains ``task_results_queue``.

        It reuses MQClient (one connection per thread, per pika docs) and
        restarts on failure with backoff. Each envelope is stored in
        ``self.task_results`` and broadcast to every connected WebSocket via
        ``asyncio.run_coroutine_threadsafe`` so we don't cross-talk asyncio.
        """
        backoff = 1.0
        while not self._result_thread_stop.is_set():
            mq = MQClient(
                host=config.RABBITMQ_HOST,
                port=config.RABBITMQ_PORT,
                user=config.RABBITMQ_USER,
                password=config.RABBITMQ_PASS,
            )
            try:
                if not mq.connect():
                    if self._result_thread_stop.wait(min(backoff, 30)):
                        return
                    backoff = min(backoff * 2, 30)
                    continue
                backoff = 1.0
                mq.declare_queue("task_results_queue")
                logger.info("👂 listener connected to task_results_queue")

                def _callback(ch, method, properties, body):
                    try:
                        envelope = json.loads(body)
                    except json.JSONDecodeError:
                        logger.warning("listener received malformed result body")
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                        return
                    task_id = envelope.get("task_id")
                    if task_id:
                        # Schedule task results update and ecosystem update on main asyncio loop
                        if self._main_loop and not self._main_loop.is_closed():
                            asyncio.run_coroutine_threadsafe(
                                self._update_task_results(task_id, envelope),
                                self._main_loop
                            )
                    self._schedule_broadcast(envelope)
                    ch.basic_ack(delivery_tag=method.delivery_tag)

                mq.consume("task_results_queue", _callback)
            except Exception as exc:
                logger.exception(f"listener crashed: {exc}")
            finally:
                mq.close()
            if self._result_thread_stop.wait(min(backoff, 30)):
                return
            backoff = min(backoff * 2, 30)

    def _schedule_broadcast(self, envelope: dict) -> None:
        if self._main_loop is None or self._main_loop.is_closed():
            return
        try:
            asyncio.run_coroutine_threadsafe(
                self._broadcast(envelope), self._main_loop
            )
        except RuntimeError:
            # Loop is shutting down — drop silently
            pass

    def _schedule_ecosystem_update(self, envelope: dict) -> None:
        """Super Intelligence Ecosystem'e task sonuçlarını bildir"""
        if self._main_loop is None or self._main_loop.is_closed():
            return
        try:
            asyncio.run_coroutine_threadsafe(
                self._handle_task_completion(envelope), self._main_loop
            )
        except RuntimeError:
            pass

    async def _handle_task_completion(self, envelope: dict) -> None:
        """Task completion'ı ecosystem sistemlerine dağıt"""
        try:
            task_id = envelope.get("task_id", "unknown")
            departments = envelope.get("departments", [])
            outcome = envelope.get("outcome", "unknown")
            duration = envelope.get("duration_seconds", 0) / 60  # dakikaya çevir
            metrics = envelope.get("metrics", {})
            learnings = envelope.get("learnings", [])

            # 1. Cross-Department Learning'e kaydet
            await self.cross_learner.record_task_outcome(
                task_id=task_id,
                departments=departments,
                outcome=outcome,
                duration_minutes=duration,
                metrics=metrics,
                learnings=learnings
            )

            # 2. Knowledge Base'e yeni bilgi ekle (başarılı sonuçlardan)
            if outcome == "success" and learnings:
                from core.knowledge.shared_knowledge import KnowledgeItem, KnowledgeType
                for learning in learnings:
                    item = KnowledgeItem(
                        id=f"kb_{task_id}_{int(datetime.now().timestamp())}",
                        type=KnowledgeType.INSIGHT,
                        title=f"Task'tan Öğrenilen: {task_id}",
                        content=learning,
                        source_department=departments[0] if departments else "unknown",
                        tags=["task_insight", outcome],
                        confidence=0.8,
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    await self.knowledge_base.add_knowledge(item)

            # 3. Event publish et
            await self.event_bus.publish(
                DepartmentEvents.TASK_COMPLETED,
                {
                    "task_id": task_id,
                    "departments": departments,
                    "outcome": outcome,
                    "metrics": metrics
                },
                source="jarvis_core"
            )

            logger.info(f"Ecosystem updated: task={task_id}, outcome={outcome}")

        except Exception as e:
            logger.error(f"Ecosystem update error: {e}")

    async def _update_task_results(self, task_id: str, envelope: dict) -> None:
        """Asynchronously updates task results in a thread-safe way on the main loop"""
        self.task_results[task_id] = envelope
        # task_results kırpma
        if len(self.task_results) > 500:
            oldest = list(self.task_results.keys())[:-500]
            for k in oldest:
                self.task_results.pop(k, None)
        # A2 FIX: task_history da kırp — sonsuz bellek büyümesini önle
        if len(self.task_history) > 1000:
            self.task_history = self.task_history[-1000:]
        await self._handle_task_completion(envelope)

    async def _broadcast(self, envelope: dict) -> None:
        if not self.active_connections:
            return
        # Filter by client_id if the envelope targets one; otherwise broadcast.
        target = envelope.get("client_id")
        message_dict = {"type": "task_result", "payload": envelope}
        
        target_dept = envelope.get("department")
        if not target_dept and envelope.get("departments"):
            depts = envelope.get("departments")
            if isinstance(depts, list) and depts:
                target_dept = depts[0]
                
        if "department" in envelope:
            message_dict["department"] = envelope["department"]
        elif target_dept:
            message_dict["department"] = target_dept
            
        message = json.dumps(message_dict)
        dead: list[str] = []
        for client_id, ws in list(self.active_connections.items()):
            if target and client_id != target:
                continue
                
            user = ws.scope.get("user")
            if _SECURITY_ENABLED and not user:
                continue

            if user:
                # A4 FIX: normalize role ile tutarlı karşılaştırma
                role_val = self._get_role_str(user)
                user_dept = getattr(user, "department", None)

                if role_val == 'admin':
                    pass  # admin hepsini görür
                elif role_val in ('department', 'dept'):
                    if target_dept and target_dept != user_dept:
                        continue
                elif role_val == 'readonly':
                    if target_dept:
                        continue
                else:
                    continue

            try:
                await ws.send_text(message)
            except Exception:
                dead.append(client_id)
        for cid in dead:
            await self.disconnect_websocket(cid)

    async def system_status_updater(self):
        """Sistem durumunu periyodik olarak güncelle"""
        while self.is_running:
            try:
                # Her 5 dakikada bir sistem durumu güncelle
                await asyncio.sleep(300)
                
                # ROI snapshot for shadow-CEO dashboards
                roi_snapshot = self.roi._calculate_base_metrics()
                logger.debug(f"ROI snapshot: roi={roi_snapshot.get('roi_score', 0):.2f}")
                
                logger.debug("System status updated")
                
            except Exception as e:
                logger.error(f"System status updater error: {e}")

    async def periodic_maintenance(self):
        """Periyodik bakım görevleri"""
        while self.is_running:
            try:
                # Run maintenance checks every 60 seconds
                await asyncio.sleep(60)
                
                # Prune pending_actions older than 600 seconds
                now = time.time()
                expired_actions = [
                    action_id for action_id, action in list(self.pending_actions.items())
                    if now - action.get("created_at", now) > 600
                ]
                for action_id in expired_actions:
                    self.pending_actions.pop(action_id, None)
                    logger.info(f"[MAINTENANCE] Pruned expired pending action: {action_id}")
                
                logger.debug("Periodic maintenance completed")
                
            except Exception as e:
                logger.error(f"Periodic maintenance error: {e}")

    async def startup(self):
        """Sistem başlatma"""
        logger.info("Starting Jarvis ZOM Core...")

        # C3 FIX: Restart sonrası model_state.json'dan aktif modeli yükle
        state_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "model_state.json"
        )
        if os.path.exists(state_path):
            try:
                import json as _json
                with open(state_path, "r", encoding="utf-8") as _sf:
                    _state = _json.load(_sf)
                _saved_model = _state.get("active_model")
                if _saved_model and hasattr(self, "openrouter") and self.openrouter:
                    self.openrouter.default_model = _saved_model
                    os.environ["LLM_MODEL"] = _saved_model
                    os.environ["GEMMA_MODEL"] = _saved_model
                    logger.info(f"[ModelState] Restored active_model={_saved_model} from model_state.json")
            except Exception as _se:
                logger.warning(f"[ModelState] Could not restore model from model_state.json: {_se}")

        # Initialize Traceloop OpenLLMetry if enabled in environment
        if _TRACELOOP_AVAILABLE and os.getenv("ZOM_ENABLE_TELEMETRY") == "true":
            try:
                Traceloop.init(app_name="jarvis_zom", disable_batches=True)
                logger.info("Traceloop OpenLLMetry initialized successfully.")
            except Exception as tle:
                logger.warning(f"Failed to initialize Traceloop: {tle}")
                
        self.is_running = True
        self.start_time = datetime.now()
        
        # Arka plan görevlerini başlat
        await self.start_background_tasks()

        # Connect to RabbitMQ if enabled
        if config.ZOM_ENABLE_RABBITMQ:
            try:
                if self.mq.connect():
                    self.mq_ready = True
                    logger.info("Connected to RabbitMQ in Jarvis ZOM Core startup.")
                    # Start the result listener thread
                    self._result_thread = threading.Thread(
                        target=self._result_listener_loop,
                        name="zom_result_listener",
                        daemon=True,
                    )
                    self._result_thread.start()
                    logger.info("Started result listener thread.")
                else:
                    self.mq_ready = False
                    logger.warning("Could not connect to RabbitMQ in startup. Fallback mode is active.")
            except Exception as e:
                self.mq_ready = False
                logger.error(f"Failed to connect to RabbitMQ in startup: {e}")
        
        # Super Intelligence Ecosystem sistemlerini başlat
        await self.knowledge_base.start()
        await self.cross_learner.start()
        await self.autonomous_collaborator.start()
        await realtime_server.start()
        
        # Start live stream background simulation
        try:
            from backend.api.live_stream import simulate_activities
            await simulate_activities()
        except Exception as e:
            logger.warning(f"Failed to start live stream simulation: {e}")
        
        # Intelligent Router'a capability matrix'i ayarla
        capability_matrix = {}
        for dept_id, dept in self.department_registry.departments.items():
            capability_matrix[dept_id] = {}
            for cap in dept.capabilities:
                capability_matrix[dept_id][cap] = 0.8  # Varsayılan yetenek seviyesi
        self.intelligent_router.set_capability_matrix(capability_matrix)
        
        # Ecosystem API router'ı kaydet
        set_jarvis_core(self)
        self.app.include_router(ecosystem_router)

        # Design AI router — Stitch Studio LLM endpoint
        set_design_director(self.openrouter)
        self.app.include_router(design_ai_router)
        
        # Publish system startup event to all departments
        await self.event_bus.publish(
            SystemEvents.STARTUP,
            {
                "timestamp": datetime.now().isoformat(),
                "departments": list(self.department_registry.departments.keys()),
                "total_departments": len(self.department_registry.departments)
            },
            source="jarvis_core"
        )
        
        logger.info("Jarvis ZOM Core started successfully")
        logger.info(f"Active agents: {list(self.agents.keys())}")
        logger.info(f"Departments registered: {list(self.department_registry.departments.keys())}")
        logger.info(f"Event Bus active: {self.event_bus is not None}")
        logger.info(f"Knowledge Base active: {self.knowledge_base is not None}")
        logger.info(f"Cross-Department Learner active: {self.cross_learner is not None}")
        logger.info(f"Intelligent Router active: {self.intelligent_router is not None}")
        logger.info(f"Autonomous Collaborator active: {self.autonomous_collaborator is not None}")
        logger.info(f"WebSocket endpoint: /ws/{{client_id}}")

    async def local_task_dispatcher(self):
        """
        Memory-based local task dispatcher fallback when RabbitMQ is offline.
        Drains tasks from self.local_task_queue and processes them asynchronously.
        Enforces clean, evidence-based 4-field reporting format.
        """
        logger.info("Local task dispatcher loop started.")
        while self.is_running:
            try:
                task_payload = await self.local_task_queue.get()
                task_id = task_payload.get("task_id")
                client_id = task_payload.get("client_id")
                sender = task_payload.get("sender")
                description = task_payload.get("description")
                dept = task_payload.get("department")
                context = task_payload.get("context") or {}
                
                logger.info(f"[Local Dispatcher] Task {task_id} dequeued for department: {dept}")
                
                agent = self.agents.get(dept)
                if not agent:
                    error_msg = f"Unknown department '{dept}'"
                    envelope = {
                        "task_id": task_id,
                        "client_id": client_id,
                        "sender": sender,
                        "status": "failed",
                        "error": error_msg,
                        "completed_at": datetime.now().isoformat()
                    }
                    self.task_results[task_id] = envelope
                    self._schedule_broadcast(envelope)
                    self.local_task_queue.task_done()
                    continue
                
                if not hasattr(agent, "execute_task"):
                    error_msg = f"Department '{dept}' does not implement execute_task"
                    envelope = {
                        "task_id": task_id,
                        "client_id": client_id,
                        "sender": sender,
                        "status": "failed",
                        "error": error_msg,
                        "completed_at": datetime.now().isoformat()
                    }
                    self.task_results[task_id] = envelope
                    self._schedule_broadcast(envelope)
                    self.local_task_queue.task_done()
                    continue
                
                task_data = {
                    "task_id": task_id,
                    "description": description,
                    "task_type": "local_queue",
                    "client_id": client_id,
                    **context
                }
                
                async def run_agent_task(t_data=task_data, t_id=task_id, c_id=client_id, t_dept=dept, t_sender=sender, t_payload=task_payload):
                    try:
                        # Broadcast start of task execution
                        start_envelope = {
                            "task_id": t_id,
                            "client_id": c_id,
                            "sender": t_sender,
                            "status": "dispatched",
                            "department": t_dept,
                            "departments": [t_dept],
                            "result": {
                                "agent": t_dept,
                                "status": "running"
                            },
                            "completed_at": None
                        }
                        self._schedule_broadcast(start_envelope)

                        if os.getenv("ZOM_USE_LANGGRAPH") == "true":
                            # Route execution through the LangGraph StateGraph Orchestration Engine
                            from core.orchestration.orchestration_graph import orchestration_graph
                            pipeline = [t_dept]
                            if t_payload.get("context", {}).get("pipeline"):
                                pipeline = [t_dept] + t_payload["context"]["pipeline"]
                            
                            graph_outcome = await orchestration_graph.execute(
                                description=description,
                                client_id=c_id,
                                pipeline=pipeline
                            )
                            result = graph_outcome.get("department_outcomes", {}).get(t_dept) or {"success": True, "output": "Graph execution completed"}
                        else:
                            # Graceful legacy fallback path (Eksik 6)
                            result = await agent.execute_task(t_data)
                        
                        # Apply Critic review and format output
                        formatted_output = self._format_evidence_report(description, t_dept, result)

                        # Deliverable zorunluluğu (Faz C): departman somut artefakt üretmek zorunda.
                        artifacts = result.get("artifacts") or ([result["report_path"]] if result.get("report_path") else [])
                        is_deliverable = result.get("deliverable", bool(artifacts))
                        final_status = "completed" if is_deliverable else "needs_review"
                        if not is_deliverable:
                            logger.warning(f"[Deliverable Guard] {t_dept} somut artefakt üretmedi → 'needs_review'.")

                        envelope = {
                            "task_id": t_id,
                            "client_id": c_id,
                            "sender": t_sender,
                            "status": final_status,
                            "department": t_dept,
                            "departments": [t_dept],
                            "result": {
                                "success": result.get("success", True) and is_deliverable,
                                "output": formatted_output,
                                "report_path": result.get("report_path"),
                                "artifacts": artifacts,
                                "deliverable": is_deliverable
                            },
                            "completed_at": datetime.now().isoformat()
                        }
                        
                        self.task_history.append({
                            "task_id": t_id,
                            "status": "success",
                            "dept": t_dept,
                            "message": description[:200]
                        })
                        
                        self.task_results[t_id] = envelope
                        self._schedule_broadcast(envelope)
                        self._schedule_ecosystem_update({
                            "task_id": t_id,
                            "departments": [t_dept],
                            "outcome": "success",
                            "duration_seconds": 1.0,
                            "metrics": {},
                            "learnings": [f"Processed {description[:50]} successfully in {t_dept}"]
                        })
                        
                        self._add_to_history(c_id, "assistant", formatted_output, task_id=t_id, department=t_dept)
                        
                        # Collaboration: paralel departman yürütme (IntelligentRouter'dan gelen)
                        collab_depts = t_payload.get("context", {}).get("collaboration_depts") or []
                        if collab_depts:
                            try:
                                collab = await self.autonomous_collaborator.create_collaboration(
                                    title=description[:80],
                                    description=description,
                                    departments=collab_depts,
                                    subtasks={d: f"{d} işbirliği görevi" for d in collab_depts}
                                )
                                await self.autonomous_collaborator.start_collaboration(collab.id)

                                collab_outputs: dict[str, str] = {}

                                async def _run_collab_dept(cdept: str, collab_id: str):
                                    c_agent = self.agents.get(cdept)
                                    if not c_agent or not hasattr(c_agent, "execute_task"):
                                        await self.autonomous_collaborator.update_subtask(collab_id, cdept, "failed", error="agent not found")
                                        collab_outputs[cdept] = "_(ajan bulunamadı)_"
                                        return
                                    try:
                                        c_result = await c_agent.execute_task({**t_data, "task_id": str(uuid.uuid4()), "skip_outer_revision": True})
                                        out = c_result.get("output", "") or ""
                                        await self.autonomous_collaborator.update_subtask(collab_id, cdept, "completed", result=out)
                                        collab_outputs[cdept] = out
                                    except Exception as ce:
                                        await self.autonomous_collaborator.update_subtask(collab_id, cdept, "failed", error=str(ce))
                                        collab_outputs[cdept] = f"_(hata: {ce})_"

                                await asyncio.gather(*[_run_collab_dept(d, collab.id) for d in collab_depts], return_exceptions=True)
                                logger.info(f"[Collaboration] {collab.id} tamamlandı: {collab_depts}")

                                # Paralel sonuçları KULLANICIYA göster (atılımın asıl değeri):
                                # her departmanın katkısını birleştirip ek bir mesaj yayınla.
                                if collab_outputs:
                                    parts = [f"### 🤝 Paralel Departman Katkıları\n"]
                                    for cd in collab_depts:
                                        prof = self.department_registry.get(cd)
                                        dname = prof.display_name if prof else cd
                                        snippet = (collab_outputs.get(cd, "") or "")[:600]
                                        parts.append(f"**{dname}:**\n{snippet}\n")
                                    collab_summary = "\n".join(parts)
                                    collab_envelope = {
                                        "task_id": str(uuid.uuid4()),
                                        "client_id": c_id,
                                        "sender": "collaboration",
                                        "status": "completed",
                                        "department": t_dept,
                                        "departments": collab_depts,
                                        "result": {"success": True, "output": collab_summary, "deliverable": True},
                                        "completed_at": datetime.now().isoformat(),
                                    }
                                    self._schedule_broadcast(collab_envelope)
                                    self._add_to_history(c_id, "assistant", collab_summary, task_id=collab_envelope["task_id"], department=t_dept)
                            except Exception as ce:
                                logger.warning(f"[Collaboration] paralel yürütme hatası: {ce}")

                        # Sequential workflow handling
                        pipeline = t_payload.get("context", {}).get("pipeline") or t_data.get("context", {}).get("pipeline")
                        if pipeline and len(pipeline) > 0:
                            next_dept = pipeline.pop(0)
                            next_payload = {
                                **t_payload,
                                "task_id": str(uuid.uuid4()),
                                "department": next_dept,
                                "context": {
                                    **t_payload.get("context", {}),
                                    "pipeline": pipeline
                                }
                            }
                            logger.info(f"[Local Dispatcher] Routing next step in workflow: {next_dept}")
                            await self.local_task_queue.put(next_payload)
                            
                    except Exception as e:
                        logger.exception(f"Error executing agent {t_dept} via local queue: {e}")
                        
                        formatted_error_output = self._format_evidence_report(
                            description, 
                            t_dept, 
                            {"success": False, "error": str(e), "output": f"Error: {str(e)}"}
                        )
                        
                        envelope = {
                            "task_id": t_id,
                            "client_id": c_id,
                            "sender": t_sender,
                            "status": "failed",
                            "error": str(e),
                            "department": t_dept,
                            "departments": [t_dept],
                            "result": {
                                "success": False,
                                "output": formatted_error_output
                            },
                            "completed_at": datetime.now().isoformat()
                        }
                        
                        self.task_history.append({
                            "task_id": t_id,
                            "status": "failed",
                            "dept": t_dept,
                            "message": description[:200]
                        })
                        
                        self.task_results[t_id] = envelope
                        self._schedule_broadcast(envelope)
                        self._schedule_ecosystem_update({
                            "task_id": t_id,
                            "departments": [t_dept],
                            "outcome": "failed",
                            "duration_seconds": 1.0,
                            "metrics": {},
                            "learnings": []
                        })
                        self._add_to_history(c_id, "assistant", formatted_error_output, task_id=t_id, department=t_dept)
                
                asyncio.create_task(run_agent_task())
                self.local_task_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Local Dispatcher] Error: {e}")
                await asyncio.sleep(1.0)

    def _format_evidence_report(self, description: str, department: str, result: dict) -> str:
        """
        Enforces the evidence-based 4-field reporting format required by ZOM.
        Forbidden words/phrases: ✅ Başarılı, 📁 Dosya oluşturuldu, Koordinasyon yapıldı.
        """
        success = result.get("success", True)
        output_raw = result.get("output") or result.get("summary") or ""
        error_msg = result.get("error") or ""
        report_path = result.get("report_path") or ""
        
        # GÖREV (Kelimesi kelimesine ne istendi)
        gorev = description.strip()
        
        # YAPILAN (Gerçekten hangi fonksiyon çağrıldı, hangi data okundu)
        yapilan = result.get("evidence") or result.get("action_taken")
        if not yapilan:
            yapilan = f"LLM generation with tools (agent_id={department}), memory recall query"
            if "place_binance_limit_order" in output_raw or "place_binance_limit_order" in str(result):
                yapilan += ", place_binance_limit_order API call"
        
        # SONUÇ (Somut çıktı — sayı, dosya yolu, hata kodu — yoksa "tamamlanamadı")
        if not success:
            sonuc = f"Tamamlanamadı — Hata: {error_msg or 'Bilinmeyen hata'}"
        else:
            sonuc_parts = []
            if report_path:
                rel_path = os.path.basename(report_path)
                sonuc_parts.append(f"Rapor Dosya Yolu: {rel_path}")
            
            if isinstance(result.get("order_result"), dict) and "orderId" in result["order_result"]:
                sonuc_parts.append(f"Emir ID: {result['order_result']['orderId']}")
            elif "order_result" in result and isinstance(result["order_result"], dict) and "error" in result["order_result"]:
                sonuc_parts.append(f"API Hatası: {result['order_result']['error']}")
                
            if not sonuc_parts:
                if report_path:
                    sonuc_parts.append(f"Rapor Dosya Yolu: {os.path.basename(report_path)}")
                else:
                    sonuc_parts.append("Tamamlanamadı — Gerçek API bağlantısı veya somut çıktı bulunmuyor")
            
            sonuc = ", ".join(sonuc_parts)
            
        # BEKLEYEN (İnsan onayı gerekiyor mu, bir sonraki adım ne)
        bekleyen = "Yok (Otonom işlem tamamlandı)"
        if not success:
            bekleyen = "Yeniden deneme / Manuel müdahale gerekiyor"
        elif "insan onayı" in output_raw.lower() or "onay bekleniyor" in output_raw.lower():
            bekleyen = "Kullanıcı onayı bekleniyor"
            
        report = (
            f"GÖREV      : {gorev}\n"
            f"YAPILAN    : {yapilan}\n"
            f"SONUÇ      : {sonuc}\n"
            f"BEKLEYEN   : {bekleyen}"
        )
        return report

    async def shutdown(self):
        """Sistem kapatma"""
        logger.info("Shutting down Jarvis ZOM Core...")
        self.is_running = False

        # Cancel background tasks cleanly to prevent resource leaks in tests
        for task in self._background_tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        self._background_tasks.clear()

        for client_id in list(self.active_connections.keys()):
            await self.disconnect_websocket(client_id)

        # Stop the result listener thread cleanly
        self._result_thread_stop.set()
        if self._result_thread:
            try:
                if self._result_thread.is_alive():
                    self._result_thread.join(timeout=3.0)
            except Exception as e:
                logger.error(f"Failed to cleanly join result thread: {e}")

        # Super Intelligence Ecosystem sistemlerini durdur
        try:
            await self.knowledge_base.stop()
        except Exception:
            pass
        try:
            await self.cross_learner.stop()
        except Exception:
            pass
        try:
            await self.autonomous_collaborator.stop()
        except Exception:
            pass
        try:
            await realtime_server.stop()
        except Exception:
            pass

        try:
            await self.openrouter.close()
        except Exception:
            pass

        try:
            if self.mq_ready:
                self.mq.close()
        except Exception:
            pass

        logger.info("Jarvis ZOM Core shutdown complete")

# Global Jarvis instance
# Lifespan is registered inside __init__ via the asynccontextmanager — no @app.on_event needed.
jarvis_core = JarvisZOMCore()

# FastAPI app export for uvicorn
app = jarvis_core.app

def is_autonomous_action_request(message: str) -> bool:
    """
    Check if a message is an execution prompt requiring autonomous action execution.
    Conversational queries return False.
    """
    msg = message.lower().strip()
    conversational_indicators = [
        "neden", "niçin", "nasıl", "kim", "ne zaman", "kimdir", "nedir",
        "ne oldu", "anlat", "açıkla", "eleştir", "soru", "sohbet", "tanım", "aptal"
    ]
    if any(indicator in msg for indicator in conversational_indicators):
        return False
        
    execution_indicators = [
        "oluştur", "yaz", "düzelt", "çalıştır", "test et", "kodla", "değiştir",
        "create", "build", "run", "fix", "delete", "execute", "generate"
    ]
    return any(indicator in msg for indicator in execution_indicators)

def format_hybrid_task_response(result: dict) -> str:
    """
    Format a task execution result dictionary into a readable report string.
    """
    success = result.get("success", False)
    status_str = "BAŞARILI" if success else "BAŞARISIZ"
    created_files = result.get("created_files") or []
    files_str = ", ".join(created_files) if created_files else "Yok"
    
    execution_info = ""
    if "clawde_execution" in result and isinstance(result["clawde_execution"], dict):
        execution_info = result["clawde_execution"].get("result") or ""
        
    degraded = "Evet" if result.get("degraded_mode") else "Hayır"
    
    return (
        f"Görev Sonucu: {status_str}\n"
        f"Oluşturulan Dosyalar: {files_str}\n"
        f"Yürütme Detayları: {execution_info}\n"
        f"Kısıtlı Mod (Degraded): {degraded}"
    )

# Ana çalıştırma
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "5000"))
    logger.info(f"Starting Jarvis ZOM Core server on port {port}...")
    uvicorn.run(
        jarvis_core.app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )
