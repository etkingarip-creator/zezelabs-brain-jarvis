# ZOM v6.4 AgentOps Observer - Observability & Cost Tracking
# Jarvis'in performansını, maliyetlerini ve başarı oranlarını izleyen telemetri merkezi.

import time
import json

class AgentOpsObserver:
    """
    Jarvis'in Operasyonel Gözlemcisi.
    Token kullanımı, gecikme (latency) ve görev başarılarını takip eder.
    """
    def __init__(self):
        self.metrics = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "total_token_usage": 0,
            "avg_latency": 0.0
        }
        print("[AgentOps] Gözlem Kulesi aktif. Metrikler anlık olarak izleniyor.")

    def log_task(self, agent_name, status, duration, tokens=0):
        """Bir görevin metriklerini kaydeder."""
        self.metrics["total_tasks"] += 1
        if status == "SUCCESS":
            self.metrics["successful_tasks"] += 1
        else:
            self.metrics["failed_tasks"] += 1
            
        self.metrics["total_token_usage"] += tokens
        # Hareketli ortalama hesaplama
        self.metrics["avg_latency"] = (self.metrics["avg_latency"] + duration) / 2
        
        print(f"[AgentOps] 📊 Metrik Güncellendi | Ajan: {agent_name} | Durum: {status} | Süre: {duration}s")

    def get_performance_report(self):
        """Holding performans raporunu döndürür."""
        success_rate = (self.metrics["successful_tasks"] / self.metrics["total_tasks"]) * 100 if self.metrics["total_tasks"] > 0 else 0
        return {
            "success_rate": f"%{success_rate:.2f}",
            "total_tokens": self.metrics["total_token_usage"],
            "avg_latency": f"{self.metrics['avg_latency']:.2s}s"
        }

observer = AgentOpsObserver()
