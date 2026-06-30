"""
YouTube OAuth Token Alıcı — bir kez çalıştır, tarayıcıda onayla, token kaydedilir.

Önkoşul: Google Cloud Console'dan indirdiğin client_secret.json bu klasörde olmalı.
Çalıştır: python tools\\get_youtube_token.py
Sonuç: youtube_token.json (social_publisher bunu kullanır) + .env'e YOUTUBE_OAUTH_TOKEN=1
"""
import os
import sys

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.force-ssl"]  # force-ssl = altyazı (caption) yükleme
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIENT = os.path.join(ROOT, "client_secret.json")
TOKEN = os.path.join(ROOT, "youtube_token.json")


def main():
    from google_auth_oauthlib.flow import InstalledAppFlow
    # 1. .env'deki YOUTUBE_CLIENT_ID/SECRET varsa ondan; yoksa client_secret.json'dan
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(ROOT, ".env"))
    except Exception:
        pass
    cid = os.getenv("YOUTUBE_CLIENT_ID", "").strip()
    csec = os.getenv("YOUTUBE_CLIENT_SECRET", "").strip()
    if cid and csec:
        cfg = {"installed": {"client_id": cid, "client_secret": csec,
                             "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                             "token_uri": "https://oauth2.googleapis.com/token",
                             "redirect_uris": ["http://localhost"]}}
        flow = InstalledAppFlow.from_client_config(cfg, SCOPES)
    elif os.path.exists(CLIENT):
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT, SCOPES)
    else:
        print("HATA: ne .env'de YOUTUBE_CLIENT_ID/SECRET ne de client_secret.json var.")
        print("Ya .env'e yapıştır ya da client_secret.json'u şuraya koy: " + CLIENT)
        sys.exit(1)
    creds = flow.run_local_server(port=0)  # tarayıcı açılır, onay verirsin
    with open(TOKEN, "w", encoding="utf-8") as f:
        f.write(creds.to_json())
    print("BASARILI -> youtube_token.json kaydedildi.")
    print("Artık YouTube'a gerçek yükleme yapılabilir (YT_PRIVACY=private varsayılan).")


if __name__ == "__main__":
    main()
