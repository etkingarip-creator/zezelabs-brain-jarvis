"""
NotebookLM Tarayıcı Otomasyonu — departmanın OTONOM sahiplendiği yetenek (Playwright SYNC).

Tüketici NotebookLM'in ücretsiz API'si yok → departman tarayıcıyı kendisi sürer.
Kalıcı profil (user_data_dir) ile Google girişi BİR KEZ yapılır, sonra otonom.

NOT: Windows + Python 3.14'te Playwright ASYNC 'spawn UNKNOWN' veriyor → SYNC API kullanıyoruz.
Agent bunları asyncio.to_thread ile (ayrı thread) çağırır.

Akış:
  1. ensure_login(): NotebookLM aç; giriş yoksa headed tarayıcıda kullanıcı bir kez login olur.
  2. create_audio(source_text, focus_prompt, lang='en'): yeni notebook → kaynak yapıştır →
     Audio Overview (Customize + odak) üret → mp3 indir → yol döndür.

DİKKAT (dürüst): NotebookLM arayüzü değişebilir → seçiciler metin-tabanlı, ilk koşuda ayar gerekebilir.
"""
from __future__ import annotations
import os
import time
from typing import Dict

NOTEBOOKLM_URL = "https://notebooklm.google.com"
_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports", "notebooklm")
PROFILE_DIR = os.path.join(_BASE, "profile")
DL_DIR = os.path.join(_BASE, "inbox")


def _launch(p, headless: bool):
    # Windows'ta bundled Chromium headed modda 'spawn UNKNOWN' veriyor → kurulu Chrome/Edge kanalı.
    os.makedirs(PROFILE_DIR, exist_ok=True)
    os.makedirs(DL_DIR, exist_ok=True)
    last = None
    for ch in ("chrome", "msedge", None):
        try:
            kw = dict(headless=headless, accept_downloads=True,
                      args=["--disable-blink-features=AutomationControlled"],
                      viewport={"width": 1440, "height": 900})
            if ch:
                kw["channel"] = ch
            return p.chromium.launch_persistent_context(PROFILE_DIR, **kw)
        except Exception as e:
            last = e
            continue
    raise last


def _click_first(page, sels, timeout=3000) -> bool:
    for sel in sels:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=timeout):
                el.click()
                return True
        except Exception:
            continue
    return False


def _logged_in(page) -> bool:
    try:
        page.goto(NOTEBOOKLM_URL, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(3500)
        url = page.url
        if "accounts.google.com" in url or "/signin" in url.lower():
            return False
        for sel in ["text=Create new", "text=Create", "text=Yeni", "text=Oluştur", "[aria-label*='Create']"]:
            try:
                if page.locator(sel).first.is_visible(timeout=2500):
                    return True
            except Exception:
                continue
        return "notebooklm.google.com" in url
    except Exception:
        return False


def ensure_login(timeout_min: int = 6) -> Dict:
    """Headed tarayıcı; kullanıcı Google ile giriş yapana kadar bekle. Profil kalıcı."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        ctx = _launch(p, headless=False)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        try:
            if _logged_in(page):
                return {"success": True, "already": True, "msg": "Oturum zaten açık."}
            deadline = time.time() + timeout_min * 60
            while time.time() < deadline:
                page.wait_for_timeout(4000)
                if _logged_in(page):
                    return {"success": True, "msg": "Giriş tamam, profil kaydedildi."}
            return {"success": False, "error": f"{timeout_min} dk içinde giriş yapılmadı."}
        finally:
            ctx.close()


def create_audio(source_text: str, focus_prompt: str = "", lang: str = "en",
                 headless: bool = True, wait_audio_min: int = 12) -> Dict:
    """Yeni notebook → kaynak → Audio Overview üret+indir. mp3 yolunu döndürür."""
    from playwright.sync_api import sync_playwright
    shot = os.path.join(DL_DIR, "_debug.png")
    with sync_playwright() as p:
        ctx = _launch(p, headless=headless)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        try:
            if not _logged_in(page):
                return {"success": False, "error": "Oturum yok — önce notebooklm_login çalıştır."}

            # 1. Yeni notebook (add ikonu) — addSource dialog açılır
            _click_first(page, ["button:has-text('add')", "text=Create new", "[aria-label*='Yeni']", "[aria-label*='Create']"])
            page.wait_for_timeout(5000)

            # 2. Kaynak: "Kopyalanan metin" → textarea → "Ekle"
            _click_first(page, ["text=Kopyalanan metin", "text=Copied text", "text=Pasted text", "text=Metni yapıştır"])
            page.wait_for_timeout(2500)
            try:
                page.locator("textarea").first.fill(source_text[:480000])
            except Exception:
                page.keyboard.type(source_text[:5000])
            page.wait_for_timeout(500)
            _click_first(page, ["button:has-text('Ekle')", "button:has-text('Insert')", "[aria-label*='Ekle']", "[aria-label*='Insert']"])
            page.wait_for_timeout(12000)  # kaynak işlensin

            # 3. Sesli Genel Bakış (Studio paneli) → üret
            _click_first(page, ["text=Sesli Genel Bakış", "text=Sesli genel bakış", "text=Audio Overview",
                                "[aria-label*='Sesli']", "[aria-label*='Audio']"], timeout=6000)
            page.wait_for_timeout(2000)
            if focus_prompt and _click_first(page, ["text=Özelleştir", "text=Customize", "[aria-label*='zelleştir']"], timeout=2500):
                page.wait_for_timeout(1000)
                try:
                    page.locator("textarea, input[type=text]").last.fill(focus_prompt[:1500])
                except Exception:
                    pass
            _click_first(page, ["button:has-text('Oluştur')", "button:has-text('Generate')",
                                "text=Oluştur", "text=Generate", "[aria-label*='Oluştur']"])

            # 4. Üretim bekle → indir
            deadline = time.time() + wait_audio_min * 60
            dl_path = None
            while time.time() < deadline and not dl_path:
                page.wait_for_timeout(8000)
                for sel in ["[aria-label*='Download']", "[aria-label*='İndir']", "text=Download"]:
                    try:
                        el = page.locator(sel).first
                        if el.is_visible(timeout=1500):
                            with page.expect_download(timeout=60000) as di:
                                el.click()
                            d = di.value
                            dl_path = os.path.join(DL_DIR, f"notebooklm_{int(time.time())}.mp3")
                            d.save_as(dl_path)
                            break
                    except Exception:
                        continue
                if not dl_path:
                    try:
                        more = page.locator("[aria-label*='More'], [aria-label*='Diğer']").first
                        if more.is_visible(timeout=1500):
                            more.click(); page.wait_for_timeout(800)
                    except Exception:
                        pass

            if dl_path and os.path.exists(dl_path):
                return {"success": True, "path": dl_path}
            try:
                page.screenshot(path=shot)
            except Exception:
                pass
            return {"success": False, "error": f"Audio indirilemedi (UI değişmiş olabilir). Debug: {shot}"}
        finally:
            ctx.close()
