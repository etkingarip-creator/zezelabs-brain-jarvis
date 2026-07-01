"""
Thumbnail (Kapak/Hook) Motoru — CTR'ın #1 belirleyicisi.

YouTube 1280x720 kapak: çarpıcı arka plan + metin HİYERARŞİSİ:
  - KICKER (üstte küçük, renkli bar) — bağlam
  - ANA HOOK (dev Impact/Arial Black, beyaz + kalın siyah stroke) — bir VURGU kelimesi renkli
  - karartma gradyanı (metin okunurluğu) + kontrast

Küçük boyutta bile okunur olmalı (mobil feed). PIL ile çizilir.
"""
from __future__ import annotations
import os
from typing import Optional, List

FONT_IMPACT = "C:/Windows/Fonts/impact.ttf"
FONT_BLACK = "C:/Windows/Fonts/ariblk.ttf"
FONT_BOLD = "C:/Windows/Fonts/arialbd.ttf"


def _font(size: int, path: str = FONT_IMPACT):
    from PIL import ImageFont
    for p in (path, FONT_BLACK, FONT_BOLD):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _wrap(draw, words: List[str], font, max_w: int) -> List[List[str]]:
    lines, cur = [], []
    for wd in words:
        test = " ".join(cur + [wd])
        if draw.textlength(test, font=font) <= max_w or not cur:
            cur.append(wd)
        else:
            lines.append(cur); cur = [wd]
    if cur:
        lines.append(cur)
    return lines


def make_thumbnail(bg_image: str, hook: str, out_path: str,
                   kicker: str = "", accent_word: str = "",
                   accent_color=(255, 215, 0), vertical: bool = False) -> Optional[str]:
    """Hook thumbnail üret. accent_word (varsa) vurgu renginde çizilir."""
    from PIL import Image, ImageDraw, ImageFilter
    from PIL import ImageEnhance
    W, H = (1080, 1920) if vertical else (1280, 720)
    try:
        bg = Image.open(bg_image).convert("RGB")
    except Exception:
        bg = Image.new("RGB", (W, H), (15, 18, 40))
    # kapla + ortala kırp
    scale = max(W / bg.width, H / bg.height)
    bg = bg.resize((int(bg.width * scale) + 1, int(bg.height * scale) + 1))
    bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2,
                  (bg.width - W) // 2 + W, (bg.height - H) // 2 + H))
    # 1) Görsel zenginleştirme — MrBeast seviyesi: yüksek kontrast + canlı doygunluk + keskinlik
    bg = ImageEnhance.Contrast(bg).enhance(1.28)
    bg = ImageEnhance.Color(bg).enhance(1.5)
    bg = ImageEnhance.Brightness(bg).enhance(1.05)
    bg = ImageEnhance.Sharpness(bg).enhance(1.6)
    # 2) Spotlight vignette: kenarlar belirgin koyu, merkez/özne parlak (güçlü odak)
    vig = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vig)
    vd.ellipse([-W * 0.20, -H * 0.20, W * 1.20, H * 1.20], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(W * 0.16))
    black = Image.new("RGB", (W, H), (0, 0, 0))
    bg = Image.composite(bg, Image.blend(bg, black, 0.68), vig)
    # 3) Alt gradyan (metin okunurluğu)
    grad = Image.new("L", (1, H), 0)
    for y in range(H):
        grad.putpixel((0, y), int(240 * ((y / H) ** 1.5)))
    bg = Image.composite(black, bg, grad.resize((W, H)))

    margin = int(W * 0.055)

    # --- KICKER (renkli bar) ---
    if kicker:
        kf = _font(int(H * 0.052), FONT_BOLD)
        d0 = ImageDraw.Draw(bg)
        kw = d0.textlength(kicker.upper(), font=kf)
        kh = int(H * 0.072); pad = int(H * 0.018)
        d0.rectangle([margin, margin, margin + kw + pad * 2, margin + kh], fill=accent_color)
        d0.text((margin + pad, margin + pad // 2), kicker.upper(), font=kf, fill=(8, 8, 8))

    # --- ANA HOOK: glow + 3D gölge + stroke, vurgu kelime renkli + alt çizgi ---
    size = int(H * 0.185) if not vertical else int(H * 0.115)
    max_w = W - margin * 2
    _d = ImageDraw.Draw(bg)
    words = hook.upper().split()

    def _fit(sz):
        f = _font(sz)
        ls = _wrap(_d, words, f, max_w)
        widest = max((_d.textlength(" ".join(l), font=f) for l in ls), default=0)
        return f, ls, widest
    font, lines, widest = _fit(size)
    # Satır sayısı VEYA genişlik taşarsa küçült (tek kelime bile sığsın → kesik yok)
    while (len(lines) > (3 if not vertical else 5) or widest > max_w) and size > 26:
        size -= 6; font, lines, widest = _fit(size)
    line_h = int(size * 1.05)
    total_h = line_h * len(lines)
    y0 = H - margin - total_h - int(H * 0.02)
    stroke = max(5, size // 11)
    acc = (accent_word or "").upper().strip(".,!?")

    # Glow katmanı (vurgu rengiyle, bulanık) → metnin arkasında parlama
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    y = y0
    for line in lines:
        x = margin
        for wd in line:
            gd.text((x, y), wd, font=font, fill=accent_color + (220,) if any(acc and acc in wd for _ in [0]) else (255, 255, 255, 120))
            x += gd.textlength(wd + " ", font=font)
        y += line_h
    glow = glow.filter(ImageFilter.GaussianBlur(size * 0.12))
    bg = Image.alpha_composite(bg.convert("RGBA"), glow).convert("RGB")

    draw = ImageDraw.Draw(bg)
    y = y0
    for line in lines:
        x = margin
        for i, wd in enumerate(line):
            is_acc = bool(acc and acc in wd)
            wlen = draw.textlength(wd, font=font)
            off = max(3, size // 20)
            if is_acc:
                # MrBeast-stili HIGHLIGHTER kutusu: dolu renk zemin + koyu metin (yüksek kontrast pop)
                pad = int(size * 0.10)
                draw.rectangle([x - pad, y - int(pad * 0.3), x + wlen + pad, y + int(size * 1.12)],
                               fill=accent_color)
                draw.text((x, y), wd, font=font, fill=(12, 12, 12))
            else:
                draw.text((x + off, y + off), wd, font=font, fill=(0, 0, 0))  # 3D gölge
                draw.text((x, y), wd, font=font, fill=(255, 255, 255),
                          stroke_width=stroke, stroke_fill=(0, 0, 0))
            x += wlen + draw.textlength(" ", font=font)
        y += line_h

    # Kalın renkli çerçeve (MrBeast kadrajı) — opsiyonel ince
    bw = max(6, int(H * 0.012))
    ImageDraw.Draw(bg).rectangle([bw // 2, bw // 2, W - bw // 2, H - bw // 2], outline=accent_color, width=bw)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bg.save(out_path, "JPEG", quality=92)
    return out_path if os.path.exists(out_path) else None


def make_thumbnail_split(photo: str, hook: str, out_path: str, kicker: str = "",
                         accent_word: str = "", accent_color=(255, 215, 0),
                         subject_side: str = "right", vertical: bool = False) -> Optional[str]:
    """SPLIT layout: bir taraf özne fotoğrafı, diğer taraf metin paneli. Denge garantili (ölü boşluk yok)."""
    from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
    W, H = (1080, 1920) if vertical else (1280, 720)
    try:
        ph = Image.open(photo).convert("RGB")
    except Exception:
        ph = Image.new("RGB", (W, H), (20, 24, 48))
    ph = ImageEnhance.Contrast(ph).enhance(1.25)
    ph = ImageEnhance.Color(ph).enhance(1.5)
    ph = ImageEnhance.Sharpness(ph).enhance(1.5)

    def cover(img, w, h):
        s = max(w / img.width, h / img.height)
        im = img.resize((int(img.width * s) + 1, int(img.height * s) + 1))
        return im.crop(((im.width - w) // 2, (im.height - h) // 2,
                        (im.width - w) // 2 + w, (im.height - h) // 2 + h))

    # Taban: tüm kareyi kaplayan koyu+bulanık foto (renk uyumu) + karartma
    base = cover(ph, W, H)
    canvas = Image.blend(base.filter(ImageFilter.GaussianBlur(28)), Image.new("RGB", (W, H), (0, 0, 0)), 0.72)

    # Özne paneli: keskin foto, bir tarafta (right/left). Genişlik ~%46.
    pw = int(W * 0.46)
    panel = cover(ph, pw, H)
    px = W - pw if subject_side == "right" else 0
    # yumuşak kenar maskesi (metin tarafına doğru erisin)
    mask = Image.new("L", (pw, H), 255)
    md = ImageDraw.Draw(mask)
    feather = int(pw * 0.28)
    for i in range(feather):
        a = int(255 * (i / feather))
        xcol = i if subject_side == "right" else pw - 1 - i
        md.line([(xcol, 0), (xcol, H)], fill=a)
    canvas.paste(panel, (px, 0), mask)

    # Metin tarafını biraz daha karart (okunurluk)
    tx0 = 0 if subject_side == "right" else int(W * 0.46)
    txw = int(W * 0.58)
    shade = Image.new("RGBA", (txw, H), (0, 0, 0, 120))
    canvas = canvas.convert("RGBA"); canvas.alpha_composite(shade, (tx0, 0)); canvas = canvas.convert("RGB")

    draw = ImageDraw.Draw(canvas)
    margin = int(W * 0.045)
    text_x = margin if subject_side == "right" else int(W * 0.46) + margin
    text_w = int(W * 0.50)

    if kicker:
        kf = _font(int(H * 0.05), FONT_BOLD)
        kw = draw.textlength(kicker.upper(), font=kf); pad = int(H * 0.016)
        draw.rectangle([text_x, margin, text_x + kw + pad * 2, margin + int(H * 0.07)], fill=accent_color)
        draw.text((text_x + pad, margin + pad // 2), kicker.upper(), font=kf, fill=(8, 8, 8))

    size = int(H * 0.16) if not vertical else int(H * 0.105)
    words = hook.upper().split()

    def _fit2(sz):
        f = _font(sz)
        ls = _wrap(draw, words, f, text_w)
        widest = max((draw.textlength(" ".join(l), font=f) for l in ls), default=0)
        return f, ls, widest
    font, lines, widest = _fit2(size)
    while (len(lines) > 4 or widest > text_w) and size > 26:
        size -= 6; font, lines, widest = _fit2(size)
    line_h = int(size * 1.06)
    y = H - margin - line_h * len(lines) - int(H * 0.03)
    stroke = max(5, size // 11)
    acc = (accent_word or "").upper().strip(".,!?")
    for line in lines:
        x = text_x
        for wd in line:
            is_acc = bool(acc and acc in wd)
            wlen = draw.textlength(wd, font=font)
            if is_acc:
                pad = int(size * 0.10)
                draw.rectangle([x - pad, y - int(pad * 0.3), x + wlen + pad, y + int(size * 1.12)], fill=accent_color)
                draw.text((x, y), wd, font=font, fill=(12, 12, 12))
            else:
                off = max(3, size // 20)
                draw.text((x + off, y + off), wd, font=font, fill=(0, 0, 0))
                draw.text((x, y), wd, font=font, fill=(255, 255, 255), stroke_width=stroke, stroke_fill=(0, 0, 0))
            x += wlen + draw.textlength(" ", font=font)
        y += line_h

    bw = max(6, int(H * 0.012))
    draw.rectangle([bw // 2, bw // 2, W - bw // 2, H - bw // 2], outline=accent_color, width=bw)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    canvas.save(out_path, "JPEG", quality=92)
    return out_path if os.path.exists(out_path) else None


# MrBeast-stili yüksek-CTR renk şemaları (A/B testi için)
ACCENT_SCHEMES = {
    "yellow": (255, 215, 0),
    "red": (255, 45, 45),
    "green": (40, 230, 120),
    "cyan": (0, 215, 255),
}


def make_variants(bg_image: str, hook: str, out_dir: str, kicker: str = "",
                  accent_word: str = "", schemes: Optional[List[str]] = None,
                  vertical: bool = False) -> List[str]:
    """Aynı kapağı farklı vurgu renkleriyle üret (A/B testi → hangisi tıklanıyor)."""
    os.makedirs(out_dir, exist_ok=True)
    schemes = schemes or ["yellow", "red", "cyan"]
    outs = []
    for s in schemes:
        col = ACCENT_SCHEMES.get(s, (255, 215, 0))
        p = os.path.join(out_dir, f"thumb_{s}.jpg")
        r = make_thumbnail(bg_image, hook, p, kicker=kicker, accent_word=accent_word,
                           accent_color=col, vertical=vertical)
        if r:
            outs.append(r)
    return outs
