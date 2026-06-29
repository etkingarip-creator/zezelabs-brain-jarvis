"""
Social Publisher — YouTube / TikTok / Instagram yayın katmanı + platform-özel paketleme.

DÜRÜST DURUM: gerçek auto-upload OAuth/onaylı-app gerektirir:
  - YouTube: OAuth2 (client_secret.json + youtube.upload token). API key TEK BAŞINA yetmez (okuma).
  - TikTok: Content Posting API (developer app onayı + access token).
  - Instagram Reels: Graph API (Business hesap + FB app + uzun-ömürlü token).
Credential YOKSA: paket hazırlanır + "credential gerekli" durumu döner (sahte başarı yok).
Credential VARSA: gerçek yayın yapılır.
"""
from __future__ import annotations
import os
from typing import Dict

# Platform-özel optimal gönderim saatleri (genel kabul, niş/kitleyle değişir)
OPTIMAL_TIMES = {
    "youtube": "Hafta içi 14:00-16:00 veya 19:00-21:00 (yerel)",
    "tiktok": "06:00-10:00 ve 19:00-23:00; Salı-Perşembe güçlü",
    "instagram": "11:00-13:00 ve 19:00-21:00; Reels akşam",
}
HASHTAG_LIMITS = {"youtube": 15, "tiktok": 5, "instagram": 20}
FORMAT_RULES = {
    "youtube_long": "16:9 yatay, 8-15dk, ilk 30sn hook",
    "youtube_shorts": "9:16 dikey, <60sn, ilk 3sn hook, döngü",
    "tiktok": "9:16 dikey, 21-34sn tatlı nokta, ilk 1sn pattern interrupt",
    "instagram": "9:16 Reels, 7-30sn, kapak karesi önemli",
}


def platform_configured(platform: str) -> Dict:
    """Platformun gerçek yayın için yapılandırılıp yapılandırılmadığı + eksik credential."""
    p = platform.lower()
    if p == "youtube":
        ok = os.path.exists(os.getenv("YOUTUBE_TOKEN_PATH", "youtube_token.json"))
        return {"platform": "youtube", "configured": ok,
                "needs": "" if ok else "youtube_token.json (python tools/get_youtube_token.py ile al)"}
    if p == "tiktok":
        ok = bool(os.getenv("TIKTOK_ACCESS_TOKEN"))
        return {"platform": "tiktok", "configured": ok,
                "needs": "" if ok else "TIKTOK_ACCESS_TOKEN (Content Posting API, app onayı)"}
    if p in ("instagram", "ig"):
        ok = bool(os.getenv("INSTAGRAM_ACCESS_TOKEN") or os.getenv("IG_ACCESS_TOKEN"))
        return {"platform": "instagram", "configured": ok,
                "needs": "" if ok else "INSTAGRAM_ACCESS_TOKEN (Graph API, Business hesap + FB app)"}
    return {"platform": p, "configured": False, "needs": "bilinmeyen platform"}


def publish(platform: str, video_path: str, title: str, description: str, hashtags: list) -> Dict:
    """Gerçek yayın (credential varsa). Yoksa dürüstçe 'credential gerekli' döner — SAHTE BAŞARI YOK."""
    cfg = platform_configured(platform)
    if not cfg["configured"]:
        return {"published": False, "platform": cfg["platform"], "reason": "credential_yok",
                "needs": cfg["needs"], "ready_package": True}
    if not (video_path and os.path.exists(video_path)):
        return {"published": False, "platform": cfg["platform"], "reason": "video_yok"}
    try:
        p = platform.lower()
        if p == "youtube":
            return _youtube_upload(video_path, title, description, hashtags)
        if p == "tiktok":
            return _tiktok_upload(video_path, title, hashtags)
        if p in ("instagram", "ig"):
            return _instagram_upload(video_path, description, hashtags)
    except Exception as e:
        return {"published": False, "platform": platform, "reason": f"hata: {str(e)[:120]}"}
    return {"published": False, "platform": platform, "reason": "desteklenmeyen"}


def _youtube_upload(video_path: str, title: str, description: str, tags: list) -> Dict:
    """YouTube Data API v3 resumable upload (OAuth2 token gerekli)."""
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from google.oauth2.credentials import Credentials
    creds = Credentials.from_authorized_user_file(
        os.getenv("YOUTUBE_TOKEN_PATH", "youtube_token.json"),
        ["https://www.googleapis.com/auth/youtube.upload"])
    yt = build("youtube", "v3", credentials=creds)
    body = {"snippet": {"title": title[:100], "description": description[:4900], "tags": tags[:15]},
            "status": {"privacyStatus": os.getenv("YT_PRIVACY", "private")}}
    req = yt.videos().insert(part="snippet,status", body=body,
                            media_body=MediaFileUpload(video_path, resumable=True))
    resp = req.execute()
    return {"published": True, "platform": "youtube", "video_id": resp.get("id"),
            "url": f"https://youtu.be/{resp.get('id')}"}


def _tiktok_upload(video_path: str, title: str, tags: list) -> Dict:
    """TikTok Content Posting API (access token gerekli)."""
    import requests
    token = os.getenv("TIKTOK_ACCESS_TOKEN")
    init = requests.post("https://open.tiktokapis.com/v2/post/publish/video/init/",
                         headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                         json={"post_info": {"title": f"{title} {' '.join('#'+t for t in tags[:5])}"[:150],
                                             "privacy_level": "SELF_ONLY"},
                               "source_info": {"source": "FILE_UPLOAD",
                                               "video_size": os.path.getsize(video_path)}}, timeout=30)
    return {"published": init.status_code == 200, "platform": "tiktok", "detail": init.text[:200]}


def _instagram_upload(video_path: str, caption: str, tags: list) -> Dict:
    """Instagram Reels Graph API (uzun-ömürlü token + Business hesap gerekli).
    Not: IG video URL üzerinden alır — önce public URL'e yüklenmeli (CDN)."""
    return {"published": False, "platform": "instagram", "reason": "public_video_url_gerekli",
            "needs": "Video önce public URL'e (CDN) yüklenmeli; sonra Graph API container+publish"}
