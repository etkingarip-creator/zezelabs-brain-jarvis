# ZOM v6.7 Jarvis Activation Script
# Bu script, Jarvis'in ajanlarını bizzat tetikler ve otonom süreci başlatır.

from core.orchestrator.router_agent import RouterAgent
from zeze_strategy.market_analyst import VisionaryAgent
from zeze_eng.sovereign_coder import SovereignCoder
from zeze_media.director_agent import DirectorAgent
import os

def start_jarvis_production(task_desc):
    print("--- [JARVIS OTONOM MOD AKTİF] ---")
    
    # 1. Router (Crew Manager) Görevi Analiz Eder
    router = RouterAgent()
    selected_agent = router.route_task(task_desc)
    print(f"[Jarvis] 🤖 Karar: Bu görevi '{selected_agent}' birimine atıyorum.")

    # 2. Visionary (Shadow CEO Mind) Senaryoyu Kurgular
    visionary = VisionaryAgent()
    critique = visionary.brutal_critique(task_desc)
    plan = visionary.plan_unicorn_doping(task_desc)
    print(f"[Jarvis] 🧠 Vizyoner Plan: {plan}")

    # 3. Sovereign Coder (OS Warrior) Fiziksel Klasörü Oluşturur
    coder = SovereignCoder()
    desktop_path = os.path.join(os.environ["USERPROFILE"], "Desktop", "drama1")
    print(f"[Jarvis] 💻 Egemen Kodlayıcı Klasörü Hazırlıyor: {desktop_path}")
    coder.execute_terminal_command(f"mkdir \"{desktop_path}\"")

    # 4. Media Director (Everest Standard) Prodüksiyonu Yönetir
    director = DirectorAgent()
    result = director.direct_production("Vertical K-Drama: The Secret of the Golden Ritual")
    
    print("\n--- [PRODÜKSİYON TAMAMLANDI] ---")
    print(f"[Jarvis] 🎬 Sonuç: {result['status']}")
    print(f"[Jarvis] 📁 Klasör: {desktop_path}")
    print(f"[Jarvis] 📝 Not: {result['director_notes']}")

if __name__ == "__main__":
    task = "Masaüstünde drama1 klasörü oluştur ve oraya dikey bir mini K-Drama üret."
    start_jarvis_production(task)
