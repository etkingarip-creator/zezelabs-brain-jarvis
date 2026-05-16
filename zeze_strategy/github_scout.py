import json
import time
import requests
import os
import sys

# Proje köküne path ekle
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.mq_client import MQClient

class GitHubScoutAgent:
    """
    ZOM v6.1 GitHub Scout: Dünyadaki açık kaynak fırsatlarını tarayan avcı servis.
    Bulduğu repoları VisionaryAgent'a raporlar.
    """
    def __init__(self):
        self.mq = MQClient()
        self.mq.connect()
        self.github_token = os.getenv("GITHUB_TOKEN", "") # Opsiyonel: Daha yüksek rate limit için
        print("[GitHubScout] Avcı aktif. GitHub radarı çalıştırılıyor...")

    def scout_github(self, query="topic:autonomous-agents", min_stars=100):
        """GitHub'da işimize yarayacak repoları arar."""
        print(f"[GitHubScout] 🔍 Arama Başlatıldı: {query}")
        
        url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc"
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
            
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                results = response.json().get("items", [])
                found_repos = []
                for repo in results[:5]: # En iyi 5 sonuç
                    if repo["stargazers_count"] >= min_stars:
                        repo_info = {
                            "name": repo["full_name"],
                            "url": repo["html_url"],
                            "description": repo["description"],
                            "stars": repo["stargazers_count"]
                        }
                        found_repos.append(repo_info)
                
                if found_repos:
                    print(f"[GitHubScout] 🎯 {len(found_repos)} adet fırsat repo bulundu.")
                    self.report_to_visionary(found_repos)
            else:
                print(f"[GitHubScout] API Hatası: {response.status_code}")
        except Exception as e:
            print(f"[GitHubScout] Arama sırasında hata: {e}")

    def report_to_visionary(self, repos):
        """Bulunan repoları VisionaryAgent'a analiz etmesi için gönderir."""
        for repo in repos:
            task = {
                "id": f"scout_{int(time.time())}_{repo['name'].replace('/', '_')}",
                "task": f"GİTHUB FIRSAT ANALİZİ: {repo['url']} reposunu tara. Ne işimize yarar? Kopyalamalı mıyız yoksa üzerine mi inşa etmeliyiz? Acımasızca eleştir.",
                "source": "github_scout",
                "repo_data": repo
            }
            self.mq.publish("strategy_queue", task)
            print(f"[GitHubScout] 📤 Repo raporlandı: {repo['name']}")

    def run(self):
        while True:
            # Her 6 saatte bir tarama yap (Simüle: Test için 10 saniye sonra başlar)
            self.scout_github()
            print("[GitHubScout] 💤 Tarama tamamlandı. Bir sonraki devriye bekleniyor...")
            time.sleep(21600) # 6 saat

if __name__ == "__main__":
    agent = GitHubScoutAgent()
    agent.run()
