"""
ZOM Task Classifier - Görev Otomatik Sınıflandırma
NLP tabanlı görev türü ve öncelik belirleme
"""

import os
import re
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class TaskCategory(str, Enum):
    """Görev kategorileri"""
    CODE = "code"                    # Kodlama/geliştirme
    DESIGN = "design"                # Tasarım
    CONTENT = "content"              # İçerik/metin
    DATA = "data"                    # Veri analizi
    DEPLOY = "deploy"                # Dağıtım
    RESEARCH = "research"            # Araştırma
    SECURITY = "security"           # Güvenlik
    MAINTENANCE = "maintenance"      # Bakım
    COMMUNICATION = "communication"  # İletişim
    CREATIVE = "creative"            # Yaratıcı
    UNKNOWN = "unknown"


class TaskPriority(str, Enum):
    """Görev öncelikleri"""
    CRITICAL = "critical"  # Acil, hemen
    HIGH = "high"          # Yüksek
    MEDIUM = "medium"      # Normal
    LOW = "low"            # Düşük


@dataclass
class ClassificationResult:
    """Sınıflandırma sonucu"""
    category: TaskCategory
    priority: TaskPriority
    confidence: float  # 0.0 - 1.0
    suggested_departments: List[str]
    keywords: List[str]
    reasoning: str


class TaskClassifier:
    """
    Görev metninden kategori, öncelik ve departman önerisi çıkarır.
    Rule-based + keyword matching (LLM-free fallback).
    """

    # Kategori anahtar kelimeleri
    CATEGORY_PATTERNS: Dict[TaskCategory, List[str]] = {
        TaskCategory.CODE: [
            "kod", "code", "python", "javascript", "react", "api", "backend",
            "frontend", "function", "class", "debug", "fix bug", "refactor",
            "implement", "feature", "endpoint", "database", "sql", "query"
        ],
        TaskCategory.DESIGN: [
            "tasarım", "design", "ui", "ux", "figma", "layout", "component",
            "renk", "font", "görsel", "visual", "mockup", "wireframe"
        ],
        TaskCategory.CONTENT: [
            "içerik", "content", "yazı", "text", "blog", "makale", "döküman",
            "documentation", "readme", "açıklama", "description"
        ],
        TaskCategory.DATA: [
            "veri", "data", "analiz", "analytics", "rapor", "report", "chart",
            "grafik", "metric", "istatistik", "statistics", "csv", "excel"
        ],
        TaskCategory.DEPLOY: [
            "deploy", "dağıt", "yayın", "production", "server", "hosting",
            "docker", "kubernetes", "ci/cd", "pipeline", "build"
        ],
        TaskCategory.RESEARCH: [
            "araştır", "research", "incele", "investigate", "analiz et",
            "benchmark", "compare", "karşılaştır", "evaluate"
        ],
        TaskCategory.SECURITY: [
            "güvenlik", "security", "auth", "authentication", "şifre", "password",
            "encrypt", "sandbox", "validate", "sanitize", "xss", "sql injection"
        ],
        TaskCategory.MAINTENANCE: [
            "bakım", "maintenance", "update", "güncelle", "upgrade", "patch",
            "fix", "düzelt", "cleanup", "temizle", "optimize"
        ],
        TaskCategory.COMMUNICATION: [
            "通知", "bildirim", "notification", "email", "通知", "mesaj", "message",
            "telegram", "slack", "discord", "alert", "uyarı"
        ],
        TaskCategory.CREATIVE: [
            "video", "görsel", "image", "photo", "resim", "medya", "media",
            "creative", "yaratıcı", "animation", "animasyon", "thumbnail"
        ],
    }

    # Öncelik anahtar kelimeleri
    PRIORITY_PATTERNS: Dict[TaskPriority, List[str]] = {
        TaskPriority.CRITICAL: [
            "acil", "critical", "emergency", "immediately", "şimdi", "now",
            "blocking", "production down", "critical bug", "acil"
        ],
        TaskPriority.HIGH: [
            "önemli", "important", "high priority", "soon", "yakında",
            "critical", "urgent", "asap"
        ],
        TaskPriority.MEDIUM: [
            "normal", "standard", "routine", "when possible", "mümkünse"
        ],
        TaskPriority.LOW: [
            "düşük", "low priority", "nice to have", "optional", "eventually"
        ],
    }

    # Departman eşleştirmeleri
    DEPARTMENT_PATTERNS: Dict[str, List[str]] = {
        "zeze_eng": [
            "kod", "code", "python", "javascript", "api", "backend", "frontend",
            "debug", "feature", "deploy", "server", "database"
        ],
        "zeze_design": [
            "tasarım", "design", "ui", "ux", "figma", "layout", "component",
            "görsel", "visual", "mockup", "renk", "font"
        ],
        "zeze_media": [
            "video", "medya", "media", "içerik", "content", "image", "resim",
            "thumbnail", "animation", "animasyon", "script", "senaryo"
        ],
        "zeze_rnd": [
            "araştır", "research", "test", "deney", "experiment", "prototype",
            "prototype", "ml", "ai", "model", "algorithm"
        ],
        "zeze_fin": [
            "finans", "financial", "para", "money", "budget", "bütçe",
            "cost", "maliyet", "revenue", "gelir", "trading", "trade"
        ],
        "zeze_sec": [
            "güvenlik", "security", "auth", "encrypt", "sandbox", "validate",
            "protect", "koruma", "firewall", "scan", "vulnerability"
        ],
    }

    def classify(self, text: str) -> ClassificationResult:
        """Görev metnini sınıflandır"""
        if not text:
            return ClassificationResult(
                category=TaskCategory.UNKNOWN,
                priority=TaskPriority.MEDIUM,
                confidence=0.0,
                suggested_departments=[],
                keywords=[],
                reasoning="Boş metin",
            )

        text_lower = text.lower()

        # Kategori belirleme
        category_scores: Dict[TaskCategory, float] = {}
        for category, keywords in self.CATEGORY_PATTERNS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                category_scores[category] = score

        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            confidence = min(category_scores[best_category] / 3.0, 1.0)
        else:
            best_category = TaskCategory.UNKNOWN
            confidence = 0.0

        # Öncelik belirleme
        priority_scores: Dict[TaskPriority, float] = {}
        for priority, keywords in self.PRIORITY_PATTERNS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                priority_scores[priority] = score

        if priority_scores:
            best_priority = max(priority_scores, key=priority_scores.get)
        else:
            best_priority = TaskPriority.MEDIUM

        # Departman önerisi — TEK KAYNAK: core.registry.routing (eski yanlış-isimli
        # DEPARTMENT_PATTERNS terk edildi; routing.route ile 17 departman tutarlı).
        try:
            from core.registry.routing import route
            best_dept, _score, _ = route(text_lower)
            suggested_departments = [best_dept]
        except Exception:
            suggested_departments = []

        # Anahtar kelimeleri çıkar
        keywords = self._extract_keywords(text_lower)

        # Reasoning oluştur
        reasoning = self._build_reasoning(
            best_category, best_priority, suggested_departments
        )

        return ClassificationResult(
            category=best_category,
            priority=best_priority,
            confidence=confidence,
            suggested_departments=suggested_departments,
            keywords=keywords,
            reasoning=reasoning,
        )

    def _extract_keywords(self, text: str) -> List[str]:
        """Metinden anahtar kelimeleri çıkar"""
        # Stop words (Türkçe + İngilizce)
        stop_words = {
            "ve", "the", "bir", "bu", "ile", "için", "olan", "olarak",
            "to", "is", "are", "a", "an", "of", "in", "on", "at", "by",
            "for", "with", "from", "or", "but", "if", "then", "else"
        }

        words = re.findall(r'\b\w{3,}\b', text)
        keywords = [w for w in words if w not in stop_words]
        return list(set(keywords))[:10]  # Max 10 keyword

    def _build_reasoning(
        self,
        category: TaskCategory,
        priority: TaskPriority,
        departments: List[str]
    ) -> str:
        """Sınıflandırma gerekçesi oluştur"""
        parts = [
            f"Kategori: {category.value}",
            f"Öncelik: {priority.value}",
        ]
        if departments:
            parts.append(f"Önerilen departmanlar: {', '.join(departments)}")
        return " | ".join(parts)

    async def classify_with_llm(
        self,
        text: str,
        openrouter_api_key: Optional[str] = None
    ) -> ClassificationResult:
        """
        LLM destekli sınıflandırma (daha doğru ama daha yavaş).
        Fallback: rule-based.
        """
        # Basitçe rule-based'e yönlendir
        return self.classify(text)


# Global instance
task_classifier = TaskClassifier()
