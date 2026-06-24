"""
ZOM Observability Tracer (LangSmith-inspired)
─────────────────────────────────────────────
Her ajan çağrısı için trace_id, süre, token sayımı (tahmini),
Critic puanı ve hata bilgisini kaydeder.
SQLite'a yazar + stdout'a renkli özet basar.
"""
import time
import uuid
import sqlite3
import os
import json
import logging
from contextlib import asynccontextmanager
from typing import Optional

logger = logging.getLogger("zom.tracer")

_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "traces.db")


_latest_rag_stats = {}

def record_rag_stats(department: str, hits: int, duration_ms: float):
    _latest_rag_stats[department] = (hits, duration_ms)

def _init_db():
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    # Check if table has new columns, if not alter or drop
    try:
        cur = conn.execute("SELECT rag_hits FROM traces LIMIT 1")
    except sqlite3.OperationalError:
        # Table exists but doesn't have new columns. Drop it to recreate safely.
        try:
            conn.execute("DROP TABLE IF EXISTS traces")
            conn.commit()
        except Exception:
            pass

    conn.execute("""
        CREATE TABLE IF NOT EXISTS traces (
            trace_id TEXT PRIMARY KEY,
            department TEXT,
            task_description TEXT,
            started_at REAL,
            ended_at REAL,
            duration_ms REAL,
            critic_score INTEGER,
            critic_revision_count INTEGER,
            tokens_estimated INTEGER,
            rag_hits INTEGER DEFAULT 0,
            rag_duration_ms REAL DEFAULT 0.0,
            status TEXT,
            error TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


_conn = _init_db()


class Trace:
    """Bir ajan çağrısının tam izleme kaydı."""

    def __init__(self, department: str, task_description: str):
        self.trace_id = uuid.uuid4().hex[:12]
        self.department = department
        self.task_description = task_description[:200]
        self.started_at = time.time()
        self.ended_at: Optional[float] = None
        self.duration_ms: Optional[float] = None
        self.critic_score: Optional[int] = None
        self.critic_revision_count: int = 0
        self.tokens_estimated: int = 0
        self.rag_hits: int = 0
        self.rag_duration_ms: float = 0.0
        self.status: str = "running"
        self.error: Optional[str] = None

    def set_critic(self, score: int, revision_count: int):
        self.critic_score = score
        self.critic_revision_count = revision_count

    def estimate_tokens(self, text: str):
        """Kaba tahmin: 4 karakter ≈ 1 token"""
        self.tokens_estimated += len(text) // 4

    def finish(self, status: str = "success", error: Optional[str] = None):
        self.ended_at = time.time()
        self.duration_ms = (self.ended_at - self.started_at) * 1000
        
        # Pull RAG stats if recorded for this department
        try:
            if self.department in _latest_rag_stats:
                self.rag_hits, self.rag_duration_ms = _latest_rag_stats.pop(self.department)
        except Exception:
            pass

        self.status = status
        self.error = error
        self._persist()
        self._log_summary()
        self._emit_live_metric()

    def _persist(self):
        try:
            _conn.execute(
                """INSERT OR REPLACE INTO traces
                   (trace_id, department, task_description, started_at, ended_at,
                    duration_ms, critic_score, critic_revision_count,
                    tokens_estimated, rag_hits, rag_duration_ms, status, error)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    self.trace_id, self.department, self.task_description,
                    self.started_at, self.ended_at, self.duration_ms,
                    self.critic_score, self.critic_revision_count,
                    self.tokens_estimated, self.rag_hits, self.rag_duration_ms,
                    self.status, self.error
                )
            )
            _conn.commit()
        except Exception as e:
            logger.warning(f"[Tracer] Persist failed: {e}")

    def _log_summary(self):
        critic_str = f"Critic:{self.critic_score}/100 (rev:{self.critic_revision_count})" if self.critic_score is not None else "Critic:N/A"
        rag_str = f"RAG:{self.rag_hits} hits ({self.rag_duration_ms:.1f}ms)"
        status_icon = "[OK]" if self.status == "success" else "[FAIL]"
        logger.info(
            f"{status_icon} [TRACE:{self.trace_id}] [{self.department.upper()}] "
            f"dur:{self.duration_ms:.0f}ms | tokens~{self.tokens_estimated} | {critic_str} | {rag_str}"
        )


    def _emit_live_metric(self):
        """Trace tamamlandığında live_stream event bus'a metrik gönder — dashboard canlı güncellenir."""
        try:
            import asyncio
            from backend.api.live_stream import event_bus as _live_bus
            payload = {
                "department": self.department,
                "trace_id": self.trace_id,
                "status": self.status,
                "duration_ms": round(self.duration_ms or 0, 1),
                "critic_score": self.critic_score,
                "tokens_estimated": self.tokens_estimated,
            }
            # Fire-and-forget: event bus async, tracer sync — schedule on running loop
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_live_bus.publish(
                    department=self.department,
                    action="task_completed",
                    status=self.status,
                    message=f"dur:{self.duration_ms:.0f}ms critic:{self.critic_score}/100"
                ))
            except RuntimeError:
                pass  # No running loop — skip (e.g., in tests)
        except Exception:
            pass  # Non-critical — never block task completion


def get_recent_traces(limit: int = 20) -> list:
    """Son N trace kaydını döndürür (UI için)."""
    try:
        cur = _conn.execute(
            "SELECT * FROM traces ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    except Exception as e:
        logger.warning(f"[Tracer] get_recent_traces failed: {e}")
        return []


def get_department_stats() -> dict:
    """Her departman için ortalama süre ve Critic puanını döndürür."""
    try:
        cur = _conn.execute("""
            SELECT department,
                   COUNT(*) as total_tasks,
                   AVG(duration_ms) as avg_duration_ms,
                   AVG(critic_score) as avg_critic_score,
                   SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) as success_count
            FROM traces
            GROUP BY department
            ORDER BY total_tasks DESC
        """)
        cols = [d[0] for d in cur.description]
        return {"stats": [dict(zip(cols, row)) for row in cur.fetchall()]}
    except Exception as e:
        return {"error": str(e)}
