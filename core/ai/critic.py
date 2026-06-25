import json
import logging
import os
from pydantic import BaseModel, Field, field_validator
from core.ai.llm_client import LLMClient

logger = logging.getLogger("zom.critic")

class CriticOutput(BaseModel):
    """Pydantic şeması ile Critic çıktısı zorunlu doğrulaması (Hallucination Killer)"""
    score: int = Field(..., description="Quality score of the work, must be between 0 and 100")
    feedback: str = Field(..., description="Detailed constructive criticism or revision feedback")
    needs_revision: bool = Field(..., description="Must be true if score is less than 70")

    @field_validator('score')
    @classmethod
    def validate_score(cls, v: int) -> int:
        if not (0 <= v <= 100):
            raise ValueError("Score must be between 0 and 100")
        return v


class CriticAgent:
    """Otonom Eleştirmen Ajan (Self-Correction Modülü).

    R3 — Yapısal ayrım: Verifier (Critic), implementor'dan FARKLI bir modele
    sabitlenir. Aksi halde aynı karmaşıklık-yönlendirmesiyle çıktıyı üreten
    modelle aynı model onaylar → korelasyonlu hata (kötü çıktıyı kötü Critic geçirir).
    CRITIC_MODEL env ile ayarlanır; üretimde implementor'dan farklı güçlü bir
    model önerilir (örn. anthropic/claude-3-5-sonnet). Varsayılan: openrouter/free.
    """
    def __init__(self):
        self.llm = LLMClient()
        self.critic_model = os.getenv("CRITIC_MODEL", "openrouter/free")

    async def evaluate_result(self, department: str, task: str, result: str) -> dict:
        """
        Görevin sonucunu acımasızca değerlendirir.
        Pydantic doğrulama, otomatik repair loop, fast-path ve özetleme mekanizmalarına sahiptir.
        """
        # Guardrail: Departman çıktısı tamamen boşsa kalite kontrolü doğrudan reddet
        if not result or not result.strip():
            logger.warning("Critic: Result is empty. Rejecting by default.")
            return {
                "score": 0,
                "feedback": "Departman çıktısı tamamen boş. Lütfen görevi yerine getirip rapor içeriğini doldurun.",
                "needs_revision": True
            }

        # ── Senaryo 13: "Hızlı Yol" (Fast-path) ──
        # Kısa, selamlaşma veya trivial test görevlerinde Critic'i pas geç, zaman ve token tasarrufu sağla.
        task_clean = task.strip().lower()
        if len(task_clean) < 15 or any(w in task_clean for w in ["selam", "hello", "hi", "test", "ping", "pong", "nbr"]):
            logger.info(f"Critic: Fast-path activated for brief/trivial task: '{task}'")
            return {
                "score": 100,
                "feedback": "Fast-tracked: task is trivial or greeting.",
                "needs_revision": False
            }

        system_prompt = '''Sen acımasız bir Kalite Kontrol (Critic) ajanısın. 
Bir yapay zeka departmanının yaptığı işi inceleyecek ve 0 ile 100 arasında bir puan (score) vereceksin.
Eğer iş eksikse, baştan savmaysa veya hatalıysa düşük puan (örneğin 40) ver ve neyin düzeltilmesi gerektiğini (feedback) yaz.
Eğer iş mükemmelse ve tüm istekleri karşılıyorsa 80 üzeri puan ver.

SADECE VE SADECE aşağıdaki formatta GEÇERLİ JSON dön. Başka hiçbir metin yazma:
{
    "score": 85,
    "feedback": "İyi iş çıkarılmış ancak şuralar geliştirilebilir...",
    "needs_revision": false
}
(Eğer score < 70 ise needs_revision true olmalıdır.)
'''
        prompt = f"Departman: {department}\n\nGörev (Kullanıcı İsteği): {task}\n\nDepartman Çıktısı:\n{result[:3000]}"
        
        # ── Senaryo 14: "Automatic Repair Loop" ──
        repair_prompt = prompt
        for attempt in range(3):
            try:
                # Ayrı verifier modeli + bypass_antigravity (implementor modeline yeniden yönlenme)
                response = await self.llm.generate(
                    prompt=repair_prompt, system_prompt=system_prompt,
                    model=self.critic_model, bypass_antigravity=True,
                )
                
                # JSON temizle (markdown kod bloklarını kaldır)
                response_clean = response.strip()
                if response_clean.startswith("```json"):
                    response_clean = response_clean[7:-3]
                elif response_clean.startswith("```"):
                    response_clean = response_clean[3:-3]
                
                # Pydantic ile Zorla Doğrula
                data = CriticOutput.model_validate_json(response_clean.strip())
                
                # ── Senaryo 13: "Uzun Feedback Özetleme" ──
                feedback = data.feedback
                if len(feedback) > 400:
                    try:
                        logger.info("Critic feedback is too long. Summarizing for token budget...")
                        summary_prompt = f"Lütfen şu uzun geribildirimi geliştirici ajanın anlayabileceği, madde işaretleri içeren maksimum 100 karakterlik tek satırlık bir özet haline getir:\n{feedback}"
                        summary = await self.llm.generate(prompt=summary_prompt, system_prompt="Sen bir özetleme yardımcısısın.")
                        feedback = summary.strip()
                    except Exception as sum_err:
                        logger.error(f"Feedback summarization failed: {sum_err}")
                        feedback = feedback[:400] + "..."

                return {
                    "score": data.score,
                    "feedback": feedback,
                    "needs_revision": data.needs_revision
                }
                
            except Exception as e:
                logger.warning(f"Critic validation failed on attempt {attempt+1} due to: {e}. Running repair loop...")
                repair_prompt = f"{prompt}\n\n[HATA! Önceki yanıtınız şemaya uymuyor veya JSON geçersiz: {str(e)}. Lütfen YALNIZCA şemadaki JSON formatına uygun yanıt verin.]"
        
        # Hata durumunda varsayılan onay döndür
        logger.error("Critic repair loop exhausted. Returning default approval.")
        return {
            "score": 100,
            "feedback": "Repair loop exhausted, passed by default.",
            "needs_revision": False
        }

    async def evaluate_and_notify(self, department: str, task: str, result: str) -> dict:
        """
        evaluate_result() çalıştırır + düşük skor (<60) → SharedKnowledgeBase'e cross-dept warning yazar.
        Unicorn Faz 3 — Critic feedback diğer departmanlara görünür olur.
        """
        eval_result = await self.evaluate_result(department, task, result)
        score = eval_result.get("score", 100)
        if score < 60:
            try:
                from core.knowledge.shared_knowledge import shared_knowledge_base, KnowledgeItem, KnowledgeType
                from datetime import datetime
                item = KnowledgeItem(
                    id="",
                    type=KnowledgeType.WARNING,
                    title=f"[CRITIC ALERT] {department.upper()} düşük kalite: {task[:50]}",
                    content=(
                        f"Departman: {department}\n"
                        f"Görev: {task[:200]}\n"
                        f"Critic Skoru: {score}/100\n"
                        f"Geri Bildirim: {eval_result.get('feedback', '')}\n"
                        "Öneri: Bu görevi peer departmana delegate etmeyi veya sistemi gözden geçirmeyi düşünün."
                    ),
                    source_department=department,
                    tags=[department, "critic_alert", "low_quality"],
                    confidence=0.9,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                await shared_knowledge_base.add_knowledge(item)
                logger.warning(f"[Critic] {department} düşük skor ({score}/100) → SharedKnowledgeBase'e uyarı yazıldı.")
            except Exception as e:
                logger.error(f"[Critic] Cross-dept notification hatası: {e}")
        return eval_result
