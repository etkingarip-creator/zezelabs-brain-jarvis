"""
YouTube OAuth Token Alıcı — bir kez çalıştır, tarayıcıda onayla, token kaydedilir.

Önkoşul: Google Cloud Console'dan indirdiğin client_secret.json bu klasörde olmalı.
Çalıştır: python tools\\get_youtube_token.py
Sonuç: youtube_token.json (social_publisher bunu kullanır) + .env'e YOUTUBE_OAUTH_TOKEN=1
"""
import os
import sys

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIENT = os.path.join(ROOT, "client_secret.json")
TOKEN = os.path.join(ROOT, "youtube_token.json")


def main():
    if not os.path.exists(CLIENT):
        print("HATA: client_secret.json bulunamadı. Önce Google Cloud Console'dan OAuth")
        print("istemcisi (Masaüstü uygulaması) oluşturup JSON'u şuraya koy:")
        print("  " + CLIENT)
        sys.exit(1)
    from google_auth_oauthlib.flow import InstalledAppFlow
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT, SCOPES)
    creds = flow.run_local_server(port=0)  # tarayıcı açılır, onay verirsin
    with open(TOKEN, "w", encoding="utf-8") as f:
        f.write(creds.to_json())
    print("BAŞARILI → youtube_token.json kaydedildi.")
    print("Artık YouTube'a gerçek yükleme yapılabilir (YT_PRIVACY=private varsayılan).")


if __name__ == "__main__":
    main()
