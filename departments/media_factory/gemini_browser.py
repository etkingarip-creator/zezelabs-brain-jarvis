"""
Gemini Tarayıcı Otomasyonu — TAM OTOMATİK video (Veo) + görsel (Imagen), ücretsiz (Gemini Pro kotası).

Kullanıcı el sürmez: departman Gemini web'i Playwright ile sürer.
Google girişi NotebookLM ile aynı kalıcı profilden gelir (zaten girişli) → gemini.google.com/app.
Ticari + filigransız (Gemini Pro), Kling free'nin filigran/ToS sorunundan kaçınır.

Akış (recon doğrulandı): araç '+' → 'Video oluştur' / 'Görüntü oluştur' → prompt → gönder → bekle → indir.
DİKKAT: Google anti-bot + ToS riski (kullanıcı kabul etti). Kırılırsa selector ayarı gerekir.
"""
from __future__ import annotations
import os
import time
from typing import Dict

from departments.media_factory.notebooklm_browser import _launch, _click_first  # aynı Google profili

GEMINI_URL = "https://gemini.google.com/app"
_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports", "gemini")
OUT_DIR = os.path.join(_BASE, "inbox")


def _open(pg):
    pg.goto(GEMINI_URL, wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(6000)
    return "accounts.google" not in pg.url and "signin" not in pg.url.lower()


def _open_tools(pg) -> bool:
    return _click_first(pg, ["button[aria-label*='araç']", "button[aria-label*='Ekle']",
                             "button[aria-label*='add']", "button[aria-label*='tool']"], timeout=4000)


def _type_prompt(pg, prompt: str):
    # Görünür girdi kutusunu bul (video modunda contenteditable, 2 tane var → görünür olanı seç).
    candidates = [
        pg.get_by_placeholder("Gemini için bir istem girin"),
        pg.get_by_placeholder("Gemini'a sorun"),
        pg.locator("textarea:visible"),
        pg.locator("[contenteditable='true']:visible"),
        pg.locator("[role='textbox']:visible"),
    ]
    for cand in candidates:
        try:
            el = cand.first
            if el.is_visible(timeout=2500):
                # Gemini input'u overlay ile korunuyor → normal click timeout. force=True + JS focus şart.
                try:
                    el.click(force=True)
                except Exception:
                    try:
                        el.evaluate("e=>e.focus()")
                    except Exception:
                        pass
                pg.wait_for_timeout(300)
                pg.keyboard.type(prompt)
                pg.wait_for_timeout(400)
                # yazıldı mı doğrula
                try:
                    if (el.inner_text() or "").strip():
                        return True
                except Exception:
                    return True
        except Exception:
            continue
    return False


def _send(pg):
    _click_first(pg, ["button[aria-label*='Gönder']", "button[aria-label*='Send']",
                      "button[aria-label*='submit']"], timeout=3000) or pg.keyboard.press("Enter")


def _download_latest(pg, out_path: str, wait_min: int, kind: str) -> bool:
    """Üretim bitişini bekle → indir butonundan indir. kind: video|image."""
    deadline = time.time() + wait_min * 60
    while time.time() < deadline:
        pg.wait_for_timeout(8000)
        # indir butonu (üretim bitince çıkar)
        for sel in ["[aria-label*='İndir']", "[aria-label*='Download']", "[aria-label*='indir']",
                    "button:has-text('İndir')"]:
            try:
                el = pg.locator(sel).last
                if el.is_visible(timeout=1500):
                    with pg.expect_download(timeout=90000) as di:
                        el.click()
                    d = di.value
                    d.save_as(out_path)
                    if os.path.exists(out_path) and os.path.getsize(out_path) > 5000:
                        return True
            except Exception:
                continue
        # 3-nokta menü altında olabilir
        for msel in ["[aria-label*='Diğer']", "[aria-label*='More']", "[aria-label*='seçenek']"]:
            try:
                m = pg.locator(msel).last
                if m.is_visible(timeout=1200):
                    m.click(); pg.wait_for_timeout(1000); break
            except Exception:
                continue
    return False


def _generate(prompt: str, tool_label: str, out_path: str, kind: str,
              wait_min: int, headless: bool) -> Dict:
    from playwright.sync_api import sync_playwright
    os.makedirs(OUT_DIR, exist_ok=True)
    with sync_playwright() as p:
        ctx = _launch(p, headless=headless)
        pg = ctx.pages[0] if ctx.pages else ctx.new_page()
        try:
            if not _open(pg):
                return {"success": False, "error": "Gemini oturumu yok (profil girişi gerekli)"}
            if not _open_tools(pg):
                return {"success": False, "error": "araç menüsü açılamadı"}
            pg.wait_for_timeout(1500)
            if not _click_first(pg, [f"text={tool_label}", f"[aria-label*='{tool_label}']"], timeout=4000):
                return {"success": False, "error": f"'{tool_label}' seçilemedi"}
            pg.wait_for_timeout(2500)
            if not _type_prompt(pg, prompt):
                return {"success": False, "error": "prompt yazılamadı"}
            pg.wait_for_timeout(600)
            _send(pg)
            if _download_latest(pg, out_path, wait_min, kind):
                return {"success": True, "path": out_path}
            shot = os.path.join(OUT_DIR, f"_debug_{kind}.png")
            try:
                pg.screenshot(path=shot)
            except Exception:
                pass
            return {"success": False, "error": f"{kind} indirilemedi (UI ayarı gerekebilir). Debug: {shot}"}
        finally:
            ctx.close()


def create_video(prompt: str, out_path: str = "", headless: bool = True, wait_min: int = 8) -> Dict:
    """Veo ile gerçek AI video (ticari, filigransız). Gemini Pro günlük ~5 kota."""
    out_path = out_path or os.path.join(OUT_DIR, f"veo_{int(time.time())}.mp4")
    return _generate(prompt, "Video oluştur", out_path, "video", wait_min, headless)


def create_image(prompt: str, out_path: str = "", headless: bool = True, wait_min: int = 4) -> Dict:
    """Imagen ile görsel (thumbnail zemini / başlangıç karesi / b-roll still)."""
    out_path = out_path or os.path.join(OUT_DIR, f"imagen_{int(time.time())}.jpg")
    return _generate(prompt, "Görüntü oluştur", out_path, "image", wait_min, headless)
