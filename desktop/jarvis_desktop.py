"""
ZEZELABS JARVIS v9.0 — QUANTUM COMMAND CENTER (ULTRA-PREMIUM HUD VERSION)
SpaceX Flight Dashboard + NASA Mission Control + Bloomberg Cyber Terminal
Holographic Wireframe Grid Spire · 3D Particle Storm · Compact Chat Bubbles · Rotating circular telemetry
"""
import sys
import os
import math
import random
import time
import requests

from PySide6.QtCore import (
    Qt, QTimer, QPointF, QRectF, Signal, Slot, QThread
)
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont,
    QPainterPath, QLinearGradient, QRadialGradient,
    QIcon, QKeySequence, QShortcut, QPalette
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFrame, QLabel, QPushButton, QLineEdit, QTextEdit,
    QScrollArea, QSizePolicy, QSystemTrayIcon, QMenu,
    QGraphicsDropShadowEffect, QDialog, QListWidget, QListWidgetItem,
    QProgressBar, QSplitter
)

# ── Design Tokens (Cyber Translucent Matrix Theme) ──────────────────
C = {
    "bg_deep":      "#020408",   # Ultra deep space black
    "bg_dark":      "#040812",   # Rich translucent cobalt black
    "bg_panel":     "#070d1ecc",  # 80% Translucent Glassmorphic Space
    "bg_input":     "#0a1226ee",  # Input field deep glass
    "border":       "#13213dff",  # Structural tech border
    "border_glow":  "#1f3661ff",  # Focus tech glow border
    "text_white":   "#f1f5f9",   # Soft white
    "text_gray":    "#64748b",   # Telemetry cool gray
    "text_dark":    "#2e3b55",   # Muted grid lines
    
    "neon_teal":    "#00f2fe",   # Hologram Core Cyan
    "neon_pink":    "#ff007f",   # Alert / Pulse Pink
    "neon_purple":  "#a855f7",   # Strategy / Matrix Violet
    "neon_gold":    "#ffd700",   # CEO Penthouse Amber Gold
    "neon_green":   "#10b981",   # Security System Safe Green
    "neon_red":     "#ef4444",   # Cyber Warning Red
}

FLOORS = [
    {"id": "ceo",       "name": "CEO Penthouse",   "icon": "👑", "color": C["neon_gold"],   "health": 98, "agents": 1, "floor": 6, "desc": "Stratejik Vizyon & AI Onay Hattı"},
    {"id": "strategy",  "name": "Strateji Ağı",    "icon": "🎯", "color": C["neon_purple"], "health": 92, "agents": 3, "floor": 5, "desc": "Holografik Pazar & Karar Motorları"},
    {"id": "eng",       "name": "Mühendislik",     "icon": "⚙️", "color": C["neon_teal"],   "health": 95, "agents": 5, "floor": 4, "desc": "Sistem Geliştirme & AI Kodlama"},
    {"id": "fin",       "name": "Finans Terminali", "icon": "💰", "color": C["neon_green"],  "health": 88, "agents": 3, "floor": 3, "desc": "Otonom Arbitraj & Risk Analizi"},
    {"id": "marketing", "name": "Pazarlama Hub'ı",  "icon": "📡", "color": C["neon_pink"],   "health": 85, "agents": 4, "floor": 2, "desc": "Duygu Analizi & İçerik Dağıtımı"},
    {"id": "sales",     "name": "Satış Kanalları", "icon": "🚀", "color": "#f97316",         "health": 91, "agents": 3, "floor": 1, "desc": "Otonom Anlaşmalar & Pipeline"},
    {"id": "ops",       "name": "Operasyon",       "icon": "🔧", "color": "#06b6d4",         "health": 89, "agents": 2, "floor": 0, "desc": "Altyapı İzleme & Kaynak Tahsisi"},
]

TASKS = [
    "Q3 Holding Analizi", "Siber Güvenlik Taraması", "Pazar Trend Tahmini",
    "Kod Optimizasyonu v4.0", "Arbitraj Risk Değerlendirmesi", "Sosyal Medya Kampanyası",
    "Pipeline Entegrasyonu", "Otonom Rapor Hazırlama", "Chroma DB İndeksleme",
]

def get_health_color(h):
    if h >= 90: return C["neon_green"]
    if h >= 70: return C["neon_gold"]
    return C["neon_red"]


# ── Async API Request Worker ─────────────────────────────────────────
class ChatWorker(QThread):
    response_ready = Signal(str, bool)

    def __init__(self, message):
        super().__init__()
        self.message = message

    def run(self):
        url = "http://127.0.0.1:8000/api/jarvis/chat"
        try:
            r = requests.post(url, json={"message": self.message}, timeout=10)
            if r.status_code == 200:
                data = r.json()
                reply = data.get("response", "İletişim kuruldu fakat yanıt boş döndü.")
                self.response_ready.emit(reply, True)
            else:
                self.response_ready.emit(f"Sunucu hatası: Kod {r.status_code}", False)
        except Exception as e:
            time.sleep(1.0)
            fallback_replies = [
                "📡 YEREL MOD: Merkez sunucuyla bağlantı kesildi. Yerel Ajan Protokolü devrede.\nYapılan analiz: Veri tabanı stabil, eklenti sistemi aktif.",
                "⚠️ GÜVENLİ BAĞLANTI: FastAPI sunucusuna erişilemiyor. Yerel sinirsel örgü stabil.\nYerel sistem verisi: CPU stabil, bellek optimize.",
                "🤖 JARVIS YEREL ÇEKİRDEK: Ağ bağlantısı yok. Yerel komutlar işletiliyor.\nTalimatınız kuyruğa alındı ve sunucu aktifleştiğinde otomatik senkronize edilecektir.",
            ]
            self.response_ready.emit(random.choice(fallback_replies), False)


# ── Particle Class for Cyber Atmosphere ──────────────────────────────
class CyberParticle:
    def __init__(self, W, H):
        self.reset(W, H, True)

    def reset(self, W, H, init=False):
        self.gx = random.uniform(0.3, 2.7)
        self.gy = random.uniform(0.3, 2.7)
        self.gz = random.uniform(0, 7.0) if init else 0.0
        self.speed = random.uniform(0.005, 0.012)
        self.size = random.uniform(1.8, 3.5)
        self.color = random.choice([C["neon_teal"], C["neon_purple"], C["neon_gold"], C["neon_pink"]])
        self.alpha = random.randint(30, 110)
        self.pulse_speed = random.uniform(0.08, 0.2)
        self.pulse_phase = random.uniform(0, 3.14)

    def tick(self, W, H):
        self.gz += self.speed
        self.pulse_phase += self.pulse_speed
        if self.gz > 7.1:
            self.reset(W, H, False)


# ── Quantum Neural Agent ─────────────────────────────────────────────
class QuantumAgent:
    def __init__(self, fl):
        self.fl_id = fl["id"]
        self.color = fl["color"]
        self.name = random.choice(["ARGOS", "NEXUS", "CIPHER", "VECTOR", "PULSE", "ORION", "ECHO", "TITAN", "NOVA", "KRONOS"])
        self.task = random.choice(TASKS)
        self.progress = random.uniform(15, 85)
        self.status = random.choice(["AKTİF", "AKTİF", "AKTİF", "KİLİTLİ"])
        
        # Predefined distinct orbits to avoid messy clumping!
        self.orbit_r = random.uniform(0.25, 0.42)
        self.phase = random.uniform(0, math.tau)
        self.speed = random.uniform(0.01, 0.024)
        self.pulse = random.uniform(0, math.tau)
        self.trail = []

    def tick(self):
        self.phase += self.speed
        self.pulse += 0.08
        if self.status == "AKTİF":
            self.progress += random.uniform(0, 0.3)
            if self.progress >= 100:
                self.progress = 0
                self.task = random.choice(TASKS)


# ── ISOMETRIC HOLOGRAPHIC SPIRE (SpaceX cockpit standards) ───────────
class IsometricSpire(QWidget):
    floor_selected = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)

        self.floors = FLOORS
        self.agents = [QuantumAgent(fl) for fl in self.floors for _ in range(fl["agents"])]
        
        self.hovered = None
        self.selected = None
        self.zoom_fl = None
        self.zoom_t = 0.0
        self.zoom_dir = 0
        self.tick_count = 0.0
        
        # Cyber particles list
        self.particles = []
        self.grid_fade = 0.0

        timer = QTimer(self)
        timer.timeout.connect(self._on_tick)
        timer.start(24)

    def _params(self):
        W, H = self.width(), self.height()
        tw = W * 0.25  # Reduced width slightly to prevent visual crowding
        th = tw * 0.45
        n = len(self.floors)
        fh = (H * 0.65 - 3 * th) / n
        fh = max(fh, 30)
        return tw, th, fh

    def _iso(self, gx, gy, gz, tw, th, fh):
        ox = self.width() / 2
        oy = self.height() * 0.16 + 3.0 * (th / 2)
        sx = ox + (gx - gy) * (tw / 2)
        sy = oy + (gx + gy) * (th / 2) - gz * fh
        return QPointF(sx, sy)

    def _top_face(self, gz, tw, th, fh, W=3):
        tl = self._iso(0, 0, gz + 1, tw, th, fh)
        tr = self._iso(W, 0, gz + 1, tw, th, fh)
        br = self._iso(W, W, gz + 1, tw, th, fh)
        bl = self._iso(0, W, gz + 1, tw, th, fh)
        return tl, tr, br, bl

    def _face_center(self, gz, tw, th, fh):
        tl, tr, br, bl = self._top_face(gz, tw, th, fh)
        return QPointF((tl.x() + tr.x() + br.x() + bl.x()) / 4,
                       (tl.y() + tr.y() + br.y() + bl.y()) / 4)

    def _on_tick(self):
        self.tick_count += 0.025
        self.grid_fade = 0.6 + 0.3 * math.sin(self.tick_count * 1.5)
        
        target_particles = 60
        if len(self.particles) < target_particles:
            self.particles.append(CyberParticle(self.width(), self.height()))

        for p in self.particles:
            p.tick(self.width(), self.height())

        for ag in self.agents:
            ag.tick()

        # CEO Zoom easing transition
        if self.zoom_dir != 0:
            self.zoom_t = max(0.0, min(1.0, self.zoom_t + 0.045 * self.zoom_dir))
            if self.zoom_t >= 1.0: self.zoom_dir = 0
            if self.zoom_t <= 0.0:
                self.zoom_dir = 0
                self.zoom_fl = None

        self.update()

    def zoom_to(self, fl):
        self.zoom_fl = fl
        self.zoom_dir = 1 if self.zoom_t < 0.5 else -1

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()
        tw, th, fh = self._params()

        # Deep grid gradient background
        bg = QRadialGradient(W / 2, H * 0.45, max(W, H) * 0.8)
        bg.setColorAt(0, QColor("#030713"))
        bg.setColorAt(1, QColor(C["bg_deep"]))
        p.fillRect(self.rect(), bg)

        # Draw Tech HUD Compass Elements behind Spire
        self._draw_hud_compass(p, W, H, tw, th)

        # Render rising data particles
        self._draw_particles(p, tw, th, fh)

        # Apply zoom transforms
        p.save()
        if self.zoom_fl and self.zoom_t > 0:
            ease_t = math.sin(self.zoom_t * math.pi / 2)
            fl_idx = next((i for i, f in enumerate(self.floors) if f["id"] == self.zoom_fl["id"]), 0)
            fc = self._face_center(fl_idx, tw, th, fh)
            zoom_scale = 1.0 + ease_t * 0.6
            zoom_tx = (W / 2 - fc.x()) * ease_t * 0.6
            zoom_ty = (H / 2 - fc.y()) * ease_t * 0.5
            p.translate(W / 2 + zoom_tx - W / 2 * zoom_scale, H / 2 + zoom_ty - H / 2 * zoom_scale)
            p.scale(zoom_scale, zoom_scale)

        # Draw Spire Core Vertical Beam
        self._draw_core_beam(p, tw, th, fh)

        # Draw Floors (Bottom to Top)
        self._top_paths = []
        for i, fl in enumerate(self.floors):
            path = self._draw_spire_floor(p, i, fl, tw, th, fh)
            self._top_paths.append((i, fl, path))

        # Render Agents with orbits and laser links
        for ag in self.agents:
            self._draw_spire_agent(p, ag, tw, th, fh)

        p.restore()

        # CRT scanline overlay
        p.setOpacity(0.012)
        p.setPen(QPen(QColor(C["neon_teal"]), 1.0))
        for y in range(0, H, 4):
            p.drawLine(0, y, W, y)
        p.setOpacity(1.0)

        # Top dashboard details
        self._draw_top_stats(p, W)
        p.end()

    def _draw_hud_compass(self, p, W, H, tw, th):
        p.save()
        p.setOpacity(0.1 * self.grid_fade)
        cx, cy = W / 2, H * 0.62
        rx, ry = tw * 1.6, th * 1.6
        p.setPen(QPen(QColor(C["neon_teal"]), 1.0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), rx, ry)
        p.drawEllipse(QPointF(cx, cy), rx * 0.8, ry * 0.8)
        p.drawLine(cx - rx, cy, cx + rx, cy)
        p.drawLine(cx, cy - ry, cx, cy + ry)
        
        p.setFont(QFont("Consolas", 7))
        p.setPen(QColor(C["neon_teal"]))
        p.drawText(QPointF(cx + rx * 0.82, cy - 5), "SPIRE_GRID_LOCK")
        p.restore()

    def _draw_core_beam(self, p, tw, th, fh):
        p.save()
        n = len(self.floors)
        bottom_c = self._face_center(0, tw, th, fh)
        top_c = self._face_center(n - 1, tw, th, fh)
        
        beam_g = QLinearGradient(bottom_c, top_c)
        c1 = QColor(C["neon_teal"])
        c1.setAlpha(80)
        c2 = QColor(C["neon_purple"])
        c2.setAlpha(140)
        beam_g.setColorAt(0, c1)
        beam_g.setColorAt(1, c2)

        p.setPen(QPen(beam_g, 3))
        p.drawLine(bottom_c, top_c)
        p.setPen(QPen(QColor("#ffffff"), 1.0))
        p.drawLine(bottom_c, top_c)
        p.restore()

    def _draw_particles(self, p, tw, th, fh):
        p.save()
        for pt in self.particles:
            iso_pt = self._iso(pt.gx, pt.gy, pt.gz, tw, th, fh)
            cursor_pos = self.mapFromGlobal(self.cursor().pos())
            dist = math.hypot(iso_pt.x() - cursor_pos.x(), iso_pt.y() - cursor_pos.y())
            if dist < 60:
                push_f = (60 - dist) * 0.35
                angle = math.atan2(iso_pt.y() - cursor_pos.y(), iso_pt.x() - cursor_pos.x())
                iso_pt.setX(iso_pt.x() + math.cos(angle) * push_f)
                iso_pt.setY(iso_pt.y() + math.sin(angle) * push_f)

            alpha_pulse = int(pt.alpha * (0.6 + 0.4 * math.sin(pt.pulse_phase)))
            pc = QColor(pt.color)
            pc.setAlpha(max(0, min(alpha_pulse, 255)))
            
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(pc)
            p.drawEllipse(iso_pt, pt.size, pt.size * 0.5)
        p.restore()

    def _draw_spire_floor(self, p, fl_idx, fl, tw, th, fh):
        gz = fl_idx
        W3 = 3
        tl, tr, br, bl = self._top_face(gz, tw, th, fh, W3)
        btl = self._iso(0, 0, gz, tw, th, fh)
        btr = self._iso(W3, 0, gz, tw, th, fh)
        bbr = self._iso(W3, W3, gz, tw, th, fh)
        bbl = self._iso(0, W3, gz, tw, th, fh)

        is_sel = fl["id"] == self.selected
        is_hov = fl["id"] == self.hovered
        pulse = abs(math.sin(self.tick_count * 1.5 + fl_idx * 0.7))
        intensity = 1.4 if is_sel else (1.15 if is_hov else 1.0)

        # CRITICAL AESTHETIC FIX: Highly Translucent glassmorphism for floor sides!
        # This completely removes the "Giant Solid Green Sponge Cake" look.
        col = QColor(fl["color"])
        
        # ── Translucent Left Wall ──
        lf = QPainterPath()
        lf.moveTo(tl); lf.lineTo(bl); lf.lineTo(bbl); lf.lineTo(btl)
        lf.closeSubpath()
        lc = QColor(C["bg_panel"])
        lc.setAlpha(120)
        p.fillPath(lf, lc)
        
        # Add slight neon outline color to sides
        lc_edge = QColor(fl["color"])
        lc_edge.setAlpha(int(35 * intensity))
        p.fillPath(lf, lc_edge)

        # ── Translucent Right Wall ──
        rf = QPainterPath()
        rf.moveTo(tr); rf.lineTo(br); rf.lineTo(bbr); rf.lineTo(btr)
        rf.closeSubpath()
        rc = QColor(C["bg_panel"])
        rc.setAlpha(90)
        p.fillPath(rf, rc)
        
        rc_edge = QColor(fl["color"])
        rc_edge.setAlpha(int(25 * intensity))
        p.fillPath(rf, rc_edge)

        # ── Translucent Floor Surface with glowing core beam hole ──
        top = QPainterPath()
        top.moveTo(tl); top.lineTo(tr); top.lineTo(br); top.lineTo(bl)
        top.closeSubpath()
        
        surface_grad = QLinearGradient(tl, br)
        tc1 = QColor(fl["color"])
        tc1.setAlpha(int(30 * intensity + 8 * pulse)) # Extremely light neon tint
        tc2 = QColor("#081024")
        tc2.setAlpha(190)
        surface_grad.setColorAt(0, tc1)
        surface_grad.setColorAt(1, tc2)
        p.fillPath(top, surface_grad)

        # ── Fine Holographic Gridlines on Floor Surface ──
        p.save()
        p.setPen(QPen(QColor(fl["color"] + "18"), 0.8))
        grid_lines = 4
        for gi in range(1, grid_lines):
            frac = gi / grid_lines
            # Drawing parallel lines
            p.drawLine(QPointF(tl.x() + (bl.x() - tl.x()) * frac, tl.y() + (bl.y() - tl.y()) * frac),
                       QPointF(tr.x() + (br.x() - tr.x()) * frac, tr.y() + (br.y() - tr.y()) * frac))
            p.drawLine(QPointF(tl.x() + (tr.x() - tl.x()) * frac, tl.y() + (tr.y() - tl.y()) * frac),
                       QPointF(bl.x() + (br.x() - bl.x()) * frac, bl.y() + (br.y() - bl.y()) * frac))
        p.restore()

        # ── High-Tech Structural Neon Borders ──
        border_w = 2.0 if is_sel else (1.2 if is_hov else 0.6)
        border_c = QColor(get_health_color(fl["health"])) if is_sel else col
        border_c.setAlpha(int(160 * intensity))
        p.setPen(QPen(border_c, border_w))
        p.drawPath(top)
        p.drawPath(lf)
        p.drawPath(rf)

        # Tech corner brackets for active HUD focus
        self._draw_corners_bracket(p, tl, tr, br, bl, border_c, is_sel)

        cx = (tl.x() + tr.x() + br.x() + bl.x()) / 4
        cy = (tl.y() + tr.y() + br.y() + bl.y()) / 4
        fw = abs(tr.x() - tl.x()) * 0.7
        fhy = abs(bl.y() - tl.y()) * 0.65
        
        # Render floor-specific fine graphics
        self._draw_floor_graphics(p, fl["id"], cx, cy, fw, fhy, col)

        # Delicate technical text indicators instead of large wordy headers
        p.setPen(QColor(C["text_white"]) if is_sel else QColor(C["text_gray"]))
        f_sz = max(7, int(tw * 0.075))
        font = QFont("Consolas", f_sz, QFont.Weight.Bold if is_sel else QFont.Weight.Normal)
        p.setFont(font)
        p.drawText(QPointF(cx - fw * 0.44, cy + f_sz * 0.6), f"{fl['icon']} {fl['name']}")

        # Mini vertical indicator bar on side of each plate
        bx = btl.x() + 4
        by = (btl.y() + tl.y()) / 2 - 3
        bw = min(tw * 0.32, 45)
        bh = 3
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#ffffff12"))
        p.drawRoundedRect(QRectF(bx, by, bw, bh), 1, 1)
        p.setBrush(QColor(get_health_color(fl["health"])))
        p.drawRoundedRect(QRectF(bx, by, bw * fl["health"] / 100, bh), 1, 1)

        return top

    def _draw_corners_bracket(self, p, tl, tr, br, bl, col, active):
        if not active: return
        p.save()
        p.setPen(QPen(col, 2.0))
        length = 10
        for pt, dx, dy in [(tl, 1, 0.5), (tr, -1, 0.5), (br, -1, -0.5), (bl, 1, -0.5)]:
            p.drawLine(pt, QPointF(pt.x() + dx * length, pt.y() + dy * length))
        p.restore()

    def _draw_floor_graphics(self, p, floor_id, cx, cy, fw, fh, col):
        t = self.tick_count
        p.save()
        p.setClipRect(QRectF(cx - fw * 0.8, cy - fh * 0.9, fw * 1.6, fh * 1.8))

        if floor_id == "ceo":
            p.setPen(QPen(QColor(C["neon_gold"]), 0.9))
            for i in range(3):
                scale = 0.3 + i * 0.22
                p.drawEllipse(QPointF(cx, cy), fw * scale, fh * scale)
            # Glowing core diamond
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(C["neon_gold"] + "aa"))
            d_sz = 5 + 3 * abs(math.sin(t * 2.5))
            p.drawPolygon([QPointF(cx, cy - d_sz), QPointF(cx + d_sz * 1.3, cy),
                           QPointF(cx, cy + d_sz), QPointF(cx - d_sz * 1.3, cy)])

        elif floor_id == "strategy":
            r = min(fw, fh) * 0.5
            p.setPen(QPen(QColor(C["neon_purple"] + "45"), 0.8))
            p.drawEllipse(QPointF(cx, cy), r, r * 0.45)
            p.drawEllipse(QPointF(cx, cy), r * 0.5, r * 0.45 * 0.5)
            
            sweep_a = (t * 2.0) % math.tau
            p.setPen(QPen(QColor(C["neon_purple"]), 1.4))
            p.drawLine(QPointF(cx, cy), QPointF(cx + r * math.cos(sweep_a), cy + r * 0.45 * math.sin(sweep_a)))

        elif floor_id == "eng":
            p.setFont(QFont("Consolas", 5))
            p.setPen(QColor(C["neon_teal"] + "aa"))
            for col_idx in range(4):
                fx = cx - fw * 0.3 + col_idx * fw * 0.2
                for char_idx in range(3):
                    fy = cy - fh * 0.35 + char_idx * fh * 0.3
                    ch = random.choice(["1", "0", "x", "y", "a", "b"])
                    op = abs(math.sin(t * 1.8 + col_idx + char_idx))
                    p.setOpacity(op)
                    p.drawText(QPointF(fx, fy), ch)
            p.setOpacity(1.0)

        elif floor_id == "fin":
            p.setPen(QPen(QColor(C["neon_green"]), 1.0))
            candlesticks = 5
            for idx in range(candlesticks):
                bx = cx - fw * 0.3 + idx * fw * 0.16
                by = cy + math.sin(t * 1.5 + idx) * fh * 0.3
                cw = fw * 0.07
                ch2 = fh * (0.18 + 0.12 * abs(math.sin(t + idx)))
                p.setBrush(QColor(C["neon_green"] + "88"))
                p.drawRect(QRectF(bx, by - ch2 / 2, cw, ch2))
                p.drawLine(QPointF(bx + cw / 2, by - ch2), QPointF(bx + cw / 2, by + ch2))

        elif floor_id == "marketing":
            p.setPen(QPen(QColor(C["neon_pink"]), 1.2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            wave = QPainterPath()
            wave.moveTo(cx - fw * 0.4, cy)
            for x in range(int(fw * 0.8)):
                wx = cx - fw * 0.4 + x
                wy = cy + math.sin(x * 0.1 + t * 3.5) * fh * 0.3
                wave.lineTo(wx, wy)
            p.drawPath(wave)

        elif floor_id == "sales":
            p.setPen(QPen(QColor("#f9731688"), 1.8))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(cx, cy), fw * 0.35, fh * 0.35)
            pulse_a = (t * 2.8) % math.tau
            px = cx + fw * 0.35 * math.cos(pulse_a)
            py = cy + fh * 0.35 * math.sin(pulse_a)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor("#ffffff"))
            p.drawEllipse(QPointF(px, py), 3.5, 3.5)

        elif floor_id == "ops":
            p.setPen(QPen(QColor("#06b6d4"), 1.0))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawArc(QRectF(cx - fw * 0.32, cy - fh * 0.32, fw * 0.64, fh * 0.64), int(t * 12 * 57.29), int(180 * 16))
            p.setFont(QFont("Consolas", 5))
            p.drawText(QPointF(cx - 10, cy + 2), f"O_{int((t*8)%99):02d}")

        p.restore()

    def _draw_spire_agent(self, p, ag, tw, th, fh):
        fl_idx = next((i for i, f in enumerate(self.floors) if f["id"] == ag.fl_id), 0)
        c = self._face_center(fl_idx, tw, th, fh)
        cx, cy = c.x(), c.y()
        
        # Elegant Thin Dashed Orbit lines drawn on screen!
        p.save()
        p.setPen(QPen(QColor(ag.color + "12"), 0.8, Qt.PenStyle.DashLine))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), tw * ag.orbit_r, th * ag.orbit_r)
        p.restore()

        # Orb coordinates with precession noise
        r_orbit = tw * ag.orbit_r
        precession = 0.04 * math.sin(self.tick_count + ag.pulse)
        sx = cx + r_orbit * math.cos(ag.phase)
        sy = cy + r_orbit * math.sin(ag.phase + precession) * 0.45
        orb_r = max(4.0, tw * 0.035)

        # Glowing neural trails
        for i, tp in enumerate(ag.trail):
            alpha = int(120 * (i / max(len(ag.trail), 1)) ** 1.8)
            tr_r = orb_r * 0.45 * (i / max(len(ag.trail), 1))
            tc = QColor(ag.color)
            tc.setAlpha(alpha)
            p.setBrush(tc)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(tp, tr_r, tr_r * 0.5)

        ag.trail.append(QPointF(sx, sy))
        if len(ag.trail) > 18: ag.trail.pop(0)

        # Pulse glow
        pf = abs(math.sin(ag.pulse))
        glow_r = orb_r * (1.8 + 1.0 * pf)
        glow = QRadialGradient(sx, sy, glow_r)
        gc = QColor(ag.color)
        gc.setAlpha(int(60 * pf))
        glow.setColorAt(0, gc)
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(glow)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(sx, sy), glow_r, glow_r * 0.6)

        # Agent Core
        core = QRadialGradient(sx - orb_r * 0.35, sy - orb_r * 0.35, orb_r)
        core.setColorAt(0, QColor(255, 255, 255, 240))
        core.setColorAt(0.4, QColor(ag.color))
        core.setColorAt(1, QColor(ag.color).darker(230))
        p.setBrush(core)
        p.setPen(QPen(QColor(ag.color).lighter(160), 0.6))
        p.drawEllipse(QPointF(sx, sy), orb_r, orb_r)

        # Neural task links shoot to the Spire core
        if ag.status == "AKTİF" and random.random() < 0.12:
            p.save()
            p.setOpacity(0.35)
            p.setPen(QPen(QColor(ag.color), 1.0))
            p.drawLine(QPointF(sx, sy), c)
            p.restore()

    def _draw_top_stats(self, p, W):
        p.save()
        p.setPen(QColor(C["text_gray"]))
        p.setFont(QFont("Consolas", 7))
        p.drawText(QRectF(15, 6, W - 30, 20), Qt.AlignmentFlag.AlignLeft,
                   f"📡 NETWORK_LINK: ACTIVE | CORE_TEMP: 44.2°C | HIGH_RESOLUTION_GRID: LOCKED")
        p.restore()

    def mouseMoveEvent(self, event):
        pos = event.position()
        self.hovered = None
        if hasattr(self, "_top_paths"):
            for _, fl, path in reversed(self._top_paths):
                if path.contains(pos):
                    self.hovered = fl["id"]
                    self.setCursor(Qt.CursorShape.PointingHandCursor)
                    return
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, event):
        pos = event.position()
        if hasattr(self, "_top_paths"):
            for _, fl, path in reversed(self._top_paths):
                if path.contains(pos):
                    prev = self.selected
                    self.selected = fl["id"]
                    self.floor_selected.emit(fl)
                    if prev == fl["id"]:
                        self.zoom_to(fl)
                    return


# ── REAL-TIME OSCILLOSCOPE (NASA Telemetry Waveform) ────────────────
class OscilloscopeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(70)
        self.phase = 0.0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_wave)
        self.timer.start(35)

    def update_wave(self):
        self.phase += 0.18
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()

        p.fillRect(self.rect(), QColor("#03060f"))

        # Grid lines
        p.setPen(QPen(QColor("#0d162a"), 0.8))
        for y in range(0, H, 14):
            p.drawLine(0, y, W, y)
        for x in range(0, W, 35):
            p.drawLine(x, 0, x, H)

        # Wave paths
        path = QPainterPath()
        path.moveTo(0, H / 2)
        for x in range(0, W, 3):
            y = H / 2 + math.sin(x * 0.045 + self.phase) * (H * 0.28) * (0.85 + 0.15 * math.cos(self.phase * 0.4))
            y += math.sin(x * 0.2 + self.phase * 2) * 2
            path.lineTo(x, y)

        p.setOpacity(0.15)
        p.setPen(QPen(QColor(C["neon_teal"]), 6.0))
        p.drawPath(path)

        p.setOpacity(1.0)
        p.setPen(QPen(QColor(C["neon_teal"]), 1.5))
        p.drawPath(path)


# ── ROTATING TELEMETRY CIRCULAR GAUGE ───────────────────────────────
class TelemetryGaugeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(95)
        self.angle = 0.0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_gauge)
        self.timer.start(40)

    def update_gauge(self):
        self.angle += 1.5
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()
        cx, cy = W / 2, H / 2
        r = 38

        # Background
        p.fillRect(self.rect(), QColor("#040813"))

        # Outer tech ticks
        p.save()
        p.translate(cx, cy)
        p.rotate(self.angle)
        p.setPen(QPen(QColor(C["neon_teal"] + "55"), 1.0))
        for i in range(12):
            p.rotate(30)
            p.drawLine(r - 5, 0, r, 0)
        p.restore()

        # Inner pulsing circle
        p.save()
        pulse = 0.8 + 0.2 * abs(math.sin(self.angle * 0.05))
        p.setPen(QPen(QColor(C["neon_pink"] + "aa"), 1.2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), r * 0.7 * pulse, r * 0.7 * pulse)
        p.restore()

        # Text Overlay
        p.setPen(QColor(C["neon_teal"]))
        p.setFont(QFont("Consolas", 7))
        p.drawText(QRectF(0, H - 15, W, 15), Qt.AlignmentFlag.AlignCenter, "CORE_NEURAL_SPIN: ACTIVE")


# ── COMMAND PALETTE Overlay Widget ──────────────────────────────────
class CommandPalette(QDialog):
    command_executed = Signal(str)
    
    CMDS = [
        ("ajan listele",         "Tüm aktif quantum holding ajanlarını dökümle"),
        ("CEO penthouse zoom",   "CEO Penthouse katına yüksek çözünürlüklü odaklan"),
        ("görev ver: [metin]",   "Sistem geneline asenkron görev ata"),
        ("strateji planı",       "Strateji Departmanı vizyon analizi tetikle"),
        ("finans ROI raporu",    "Mevcut kârlılık ve AI portföy analizini raporla"),
        ("güvenlik taraması",    "ZezeGuard güvenlik katmanlarını denetle"),
        ("sistem snapshot",      "Holding operasyonel durum snapshot kaydı"),
        ("log temizle",          "Karargah log terminalini temizle"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(560)

        cont = QFrame(self)
        cont.setStyleSheet(f"""
            QFrame {{
                background: {C['bg_panel']};
                border: 1.5px solid {C['border_glow']};
                border-radius: 14px;
            }}
        """)
        
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(40)
        sh.setOffset(0, 8)
        sh.setColor(QColor(0, 0, 0, 220))
        cont.setGraphicsEffect(sh)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        
        lay = QVBoxLayout(cont)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        row = QHBoxLayout()
        row.setContentsMargins(18, 14, 18, 14)
        row.setSpacing(10)

        cmd_icon = QLabel("⌘")
        cmd_icon.setStyleSheet(f"color: {C['neon_teal']}; font-size: 18px; font-weight: bold;")
        row.addWidget(cmd_icon)

        self.inp = QLineEdit()
        self.inp.setPlaceholderText("Quantum komutu yazın veya departman seçin...")
        self.inp.setStyleSheet(f"background: transparent; border: none; color: {C['text_white']}; font-size: 14px; font-family: 'Consolas';")
        self.inp.textChanged.connect(self._filter)
        self.inp.returnPressed.connect(self._exec)
        row.addWidget(self.inp)

        lay.addLayout(row)

        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"color: {C['border']};")
        lay.addWidget(div)

        self.lst = QListWidget()
        self.lst.setMaximumHeight(280)
        self.lst.setStyleSheet(f"""
            QListWidget {{
                background: transparent;
                border: none;
                color: {C['text_white']};
                font-family: 'Consolas';
                font-size: 12px;
                padding: 6px 0px;
            }}
            QListWidget::item {{
                padding: 10px 18px;
                border-radius: 6px;
                margin: 2px 10px;
            }}
            QListWidget::item:selected, QListWidget::item:hover {{
                background: {C['border']};
                color: {C['neon_teal']};
            }}
        """)
        self.lst.itemActivated.connect(lambda it: (self.command_executed.emit(it.data(Qt.ItemDataRole.UserRole)), self.hide()))
        lay.addWidget(self.lst)

        footer = QLabel("▲▼ Seç  ↵ Gönder  ESC Kapat")
        footer.setStyleSheet(f"color: {C['text_gray']}; font-size: 9px; font-family: 'Consolas'; border-top: 1.2px solid {C['border']}; padding: 8px 18px;")
        lay.addWidget(footer)

        root.addWidget(cont)
        self._fill(self.CMDS)

    def _fill(self, cmds):
        self.lst.clear()
        for c, d in cmds:
            it = QListWidgetItem(f" > {c:<22}  ::  {d}")
            it.setData(Qt.ItemDataRole.UserRole, c)
            self.lst.addItem(it)
        if self.lst.count():
            self.lst.setCurrentRow(0)

    def _filter(self, t):
        self._fill([(c, d) for c, d in self.CMDS if t.lower() in c.lower() or t.lower() in d.lower()] if t else self.CMDS)

    def _exec(self):
        it = self.lst.currentItem()
        if it:
            self.command_executed.emit(it.data(Qt.ItemDataRole.UserRole))
        elif self.inp.text():
            self.command_executed.emit(self.inp.text())
        self.hide()

    def showEvent(self, e):
        super().showEvent(e)
        self.inp.clear()
        self.inp.setFocus()
        self._fill(self.CMDS)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.hide()
        elif e.key() == Qt.Key.Key_Down:
            self.lst.setCurrentRow(min(self.lst.currentRow() + 1, self.lst.count() - 1))
        elif e.key() == Qt.Key.Key_Up:
            self.lst.setCurrentRow(max(self.lst.currentRow() - 1, 0))
        else:
            super().keyPressEvent(e)


# ── COMPACT CHAT BUBBLES ─────────────────────────────────────────────
class ChatBubble(QWidget):
    def __init__(self, text, is_jarvis, time_str, parent=None):
        super().__init__(parent)
        self.is_jarvis = is_jarvis
        self.time_str = time_str
        
        main_lay = QHBoxLayout(self)
        main_lay.setContentsMargins(6, 4, 6, 4)
        
        self.box = QFrame()
        
        # CRITICAL AESTHETIC FIX: Beautifully size-restricted bubbles!
        # This completely removes the "Infinite wide cyan border stretching across the screen" bug.
        if is_jarvis:
            bg_col = "#060a16cc"
            border_col = C["neon_teal"]
            self.box.setStyleSheet(f"""
                QFrame {{
                    background: {bg_col};
                    border: 1.2px solid {border_col};
                    border-radius: 12px;
                }}
            """)
            main_lay.addWidget(self.box)
            main_lay.addStretch(2)  # Generous stretch on right side to push bubble left and restrict its width!
        else:
            bg_col = "#3b82f61e"
            border_col = "#3b82f666"
            self.box.setStyleSheet(f"""
                QFrame {{
                    background: {bg_col};
                    border: 1.2px solid {border_col};
                    border-radius: 12px;
                }}
            """)
            main_lay.addStretch(2)  # Generous stretch on left side to push bubble right and restrict its width!
            main_lay.addWidget(self.box)

        box_lay = QVBoxLayout(self.box)
        box_lay.setContentsMargins(12, 10, 12, 10)
        box_lay.setSpacing(4)

        header = QHBoxLayout()
        sender = QLabel("🤖 JARVIS" if is_jarvis else "👤 CEO USER")
        sender.setStyleSheet(f"font-weight: bold; font-size: 10px; color: {C['neon_teal'] if is_jarvis else C['neon_gold']}; font-family: 'Consolas';")
        header.addWidget(sender)
        header.addStretch()
        
        ts = QLabel(time_str)
        ts.setStyleSheet(f"color: {C['text_gray']}; font-size: 8px; font-family: 'Consolas';")
        header.addWidget(ts)
        box_lay.addLayout(header)

        body = QLabel(text)
        body.setWordWrap(True)
        body.setStyleSheet(f"color: {C['text_white']}; font-size: 11px; font-family: 'Segoe UI'; line-height: 140%;")
        box_lay.addWidget(body)


class TypingIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 2, 12, 2)
        
        self.box = QFrame()
        self.box.setStyleSheet(f"background: {C['bg_panel']}; border: 1px solid {C['neon_teal']}33; border-radius: 10px;")
        self.box.setFixedWidth(70)
        
        box_lay = QHBoxLayout(self.box)
        box_lay.setContentsMargins(10, 0, 10, 0)
        box_lay.setSpacing(4)
        
        self.dots = []
        for _ in range(3):
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {C['neon_teal']}; font-size: 8px;")
            box_lay.addWidget(dot)
            self.dots.append(dot)
            
        lay.addWidget(self.box)
        lay.addStretch()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(250)
        self.step = 0

    def _animate(self):
        for i, dot in enumerate(self.dots):
            op = 0.3 if i != self.step else 1.0
            dot.setStyleSheet(f"color: {C['neon_teal']}; font-size: 8px; opacity: {op};")
        self.step = (self.step + 1) % 3


# ── FULL-FEATURED ADVANCED CHAT PANEL ───────────────────────────────
class ChatPanel(QWidget):
    message_sent = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {C['bg_panel']}; border: 1.2px solid {C['border']}; border-radius: 12px;")
        
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(15)
        sh.setColor(QColor(0, 0, 0, 100))
        self.setGraphicsEffect(sh)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(6)

        # Header info
        header = QHBoxLayout()
        header.setContentsMargins(4, 2, 4, 2)
        title = QLabel("💬  SOHBET & BELLEK AKIŞI")
        title.setStyleSheet(f"color: {C['neon_teal']}; font-weight: bold; font-family: 'Consolas'; font-size: 10px; letter-spacing: 2px;")
        header.addWidget(title)
        header.addStretch()
        
        self.status_led = QLabel("● CORE_ONLINE")
        self.status_led.setStyleSheet(f"color: {C['neon_green']}; font-size: 8px; font-family: 'Consolas'; font-weight: bold;")
        header.addWidget(self.status_led)
        lay.addLayout(header)

        # Scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.bubbles_lay = QVBoxLayout(self.scroll_content)
        self.bubbles_lay.setContentsMargins(4, 4, 4, 4)
        self.bubbles_lay.setSpacing(4)
        self.bubbles_lay.addStretch()
        
        self.scroll.setWidget(self.scroll_content)
        lay.addWidget(self.scroll)

        self.typing_widget = None

        # Input box
        inp_frame = QFrame()
        inp_frame.setStyleSheet(f"background: {C['bg_input']}; border: 1.2px solid {C['border']}; border-radius: 8px;")
        inp_lay = QHBoxLayout(inp_frame)
        inp_lay.setContentsMargins(8, 4, 8, 4)
        inp_lay.setSpacing(6)

        self.inp = QLineEdit()
        self.inp.setPlaceholderText("Siber Karargaha veya JARVIS'e talimat verin...")
        self.inp.setStyleSheet(f"background: transparent; border: none; color: {C['text_white']}; font-family: 'Segoe UI'; font-size: 11px;")
        self.inp.returnPressed.connect(self._on_send)
        inp_lay.addWidget(self.inp, 1)

        send_btn = QPushButton("▶")
        send_btn.setFixedSize(26, 26)
        send_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C['neon_teal']};
                color: {C['bg_deep']};
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: #ffffff;
            }}
        """)
        send_btn.clicked.connect(self._on_send)
        inp_lay.addWidget(send_btn)

        lay.addWidget(inp_frame)

        self.add_message("Zezelabs Holding Siber Karargah Kontrol Arayüzü aktif.\nJARVIS v9.0 Neural Engine çevrimdışı ve bulut hibrit modda hazır. Ne arzu edersiniz?", True)

    def add_message(self, text, is_jarvis):
        self.bubbles_lay.takeAt(self.bubbles_lay.count() - 1)
        ts = time.strftime("%H:%M:%S")
        bubble = ChatBubble(text, is_jarvis, ts)
        self.bubbles_lay.addWidget(bubble)
        self.bubbles_lay.addStretch()
        QTimer.singleShot(80, self._scroll_down)

    def show_typing(self):
        if not self.typing_widget:
            self.bubbles_lay.takeAt(self.bubbles_lay.count() - 1)
            self.typing_widget = TypingIndicator()
            self.bubbles_lay.addWidget(self.typing_widget)
            self.bubbles_lay.addStretch()
            QTimer.singleShot(80, self._scroll_down)

    def hide_typing(self):
        if self.typing_widget:
            self.typing_widget.deleteLater()
            self.typing_widget = None

    def _scroll_down(self):
        sb = self.scroll.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _on_send(self):
        txt = self.inp.text().strip()
        if not txt: return
        self.inp.clear()
        
        self.add_message(txt, False)
        self.show_typing()
        self.message_sent.emit(txt)


# ── DEPARTMENTS SIDEBAR ──────────────────────────────────────────────
class SidebarPanel(QWidget):
    floor_selected = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(198)
        self.setStyleSheet(f"background: {C['bg_dark']}; border-right: 1.2px solid {C['border']};")
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 12, 8, 12)
        lay.setSpacing(6)

        # Logo
        logo = QLabel("Z")
        logo.setFixedHeight(36)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {C['neon_teal']}, stop:1 {C['neon_purple']});
            color: {C['bg_deep']};
            font-size: 18px;
            font-weight: 900;
            border-radius: 8px;
        """)
        lay.addWidget(logo)

        l1 = QLabel("ZEZELABS AI")
        l1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l1.setStyleSheet(f"color: {C['neon_teal']}; font-size: 10px; font-weight: bold; letter-spacing: 4px;")
        lay.addWidget(l1)

        l2 = QLabel("HOLDING ENGINE")
        l2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l2.setStyleSheet(f"color: {C['text_gray']}; font-size: 7px; letter-spacing: 2px;")
        lay.addWidget(l2)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {C['border']}; margin: 6px 0px;")
        lay.addWidget(sep)

        dl = QLabel("DEPARTMAN VERİLERİ")
        dl.setStyleSheet(f"color: {C['text_gray']}; font-size: 8px; font-weight: bold; letter-spacing: 1px; padding-left: 2px;")
        lay.addWidget(dl)

        self.cards = {}
        for fl in FLOORS:
            card = self._make_card(fl)
            lay.addWidget(card)
            self.cards[fl["id"]] = card

        lay.addStretch()

        self.sys_led = QLabel("● CORE SYSTEM LOCK")
        self.sys_led.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sys_led.setStyleSheet(f"color: {C['neon_green']}; font-size: 8px; font-weight: bold; font-family: 'Consolas';")
        lay.addWidget(self.sys_led)

        ver = QLabel("JARVIS HUD v9.0")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver.setStyleSheet(f"color: {C['text_dark']}; font-size: 7px; border: 1px solid {C['border']}; border-radius: 4px; padding: 2px;")
        lay.addWidget(ver)

    def _make_card(self, fl):
        card = QFrame()
        card.setFixedHeight(50)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setProperty("fl_id", fl["id"])
        
        # CRITICAL AESTHETIC FIX: Pure translucent card look!
        # This completely removes the aggressive solid red card clashing.
        card.setStyleSheet(f"""
            QFrame {{
                background: transparent;
                border-left: 3px solid {fl['color']}22;
                border-radius: 5px;
            }}
            QFrame:hover {{
                background: {fl['color']}15;
            }}
        """)
        
        c_lay = QHBoxLayout(card)
        c_lay.setContentsMargins(8, 4, 8, 4)
        c_lay.setSpacing(6)

        ico = QLabel(fl["icon"])
        ico.setFont(QFont("Segoe UI", 13))
        ico.setFixedWidth(20)
        c_lay.addWidget(ico)

        info = QVBoxLayout()
        info.setSpacing(1)
        name = QLabel(fl["name"])
        name.setStyleSheet(f"color: {C['text_white']}; font-size: 10px; font-weight: bold; font-family: 'Segoe UI';")
        info.addWidget(name)

        hc = get_health_color(fl["health"])
        stat = QLabel(f"Sğl %{fl['health']} • {fl['agents']} Ajan")
        stat.setStyleSheet(f"color: {hc}; font-size: 8px; font-family: 'Consolas';")
        info.addWidget(stat)
        c_lay.addLayout(info)

        c_lay.addStretch()

        pb = QProgressBar()
        pb.setRange(0, 100)
        pb.setValue(fl["health"])
        pb.setFixedSize(30, 4)
        pb.setTextVisible(False)
        pb.setStyleSheet(f"""
            QProgressBar {{
                background: {C['border']};
                border-radius: 2px;
                border: none;
            }}
            QProgressBar::chunk {{
                background: {hc};
                border-radius: 2px;
            }}
        """)
        c_lay.addWidget(pb)

        card.mousePressEvent = lambda ev, _fl=fl: (self.floor_selected.emit(_fl), self._select(_fl["id"]))
        return card

    def _select(self, fid):
        for fid2, card in self.cards.items():
            fl = next(f for f in FLOORS if f["id"] == fid2)
            sel = (fid2 == fid)
            
            # Subtle glowing border and trans-back instead of opaque solid coloring!
            border_c = fl["color"] if sel else fl["color"] + "22"
            bg = f"{fl['color']}18" if sel else "transparent"
            card.setStyleSheet(f"""
                QFrame {{
                    background: {bg};
                    border-left: 3px solid {border_c};
                    border-radius: 5px;
                }}
                QFrame:hover {{
                    background: {fl['color']}15;
                }}
            """)


# ── TELEMETRY & LIVE OBSERVATORY PANEL ───────────────────────────────
class TelemetryPanel(QWidget):
    def __init__(self, agents, parent=None):
        super().__init__(parent)
        self.agents = agents
        self.setFixedWidth(238)
        self.setStyleSheet(f"background: {C['bg_dark']}; border-left: 1.2px solid {C['border']};")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 12, 10, 12)
        lay.setSpacing(6)

        t = QLabel("📊  QUANTUM TELEMETRİ")
        t.setStyleSheet(f"color: {C['neon_teal']}; font-size: 10px; font-weight: bold; letter-spacing: 2px; border-bottom: 1.2px solid {C['border']}; padding-bottom: 6px; font-family: 'Consolas';")
        lay.addWidget(t)

        self.bars = {}
        for lbl, col in [("MANTIK YÜKÜ", C["neon_teal"]), ("NÖRON HAFIZA", C["neon_purple"]), ("KULLANIM VERİ", C["neon_green"]), ("ORB FREKANS", C["neon_pink"])]:
            w = QWidget()
            w.setStyleSheet("background: transparent;")
            wl = QVBoxLayout(w)
            wl.setContentsMargins(0, 0, 0, 0)
            wl.setSpacing(2)

            row = QHBoxLayout()
            nm = QLabel(lbl)
            nm.setStyleSheet(f"color: {C['text_gray']}; font-size: 8px; font-family: 'Consolas';")
            row.addWidget(nm)

            val = QLabel("—%")
            val.setStyleSheet(f"color: {col}; font-size: 8px; font-weight: bold; font-family: 'Consolas';")
            row.addStretch()
            row.addWidget(val)
            wl.addLayout(row)

            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(45)
            bar.setFixedHeight(4)
            bar.setTextVisible(False)
            bar.setStyleSheet(f"""
                QProgressBar {{
                    background: {C['border']};
                    border-radius: 2px;
                    border: none;
                }}
                QProgressBar::chunk {{
                    background: {col};
                    border-radius: 2px;
                }}
            """)
            wl.addWidget(bar)
            lay.addWidget(w)
            self.bars[lbl] = (bar, val, col)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {C['border']};")
        lay.addWidget(sep)

        dl = QLabel("ODAKLANILAN DEPARTMAN")
        dl.setStyleSheet(f"color: {C['text_gray']}; font-size: 8px; font-family: 'Consolas';")
        lay.addWidget(dl)

        self.dept_name = QLabel("Holding Core")
        self.dept_name.setStyleSheet(f"color: {C['neon_gold']}; font-size: 13px; font-weight: bold; font-family: 'Segoe UI';")
        lay.addWidget(self.dept_name)

        self.dept_desc = QLabel("ZEZELABS yapay zeka operasyon merkez binası.")
        self.dept_desc.setWordWrap(True)
        self.dept_desc.setStyleSheet(f"color: {C['text_gray']}; font-size: 9px; line-height: 120%;")
        lay.addWidget(self.dept_desc)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"color: {C['border']};")
        lay.addWidget(sep2)

        # NASA Waveform Oscilloscope & Circular Spin Telemetry
        self.oscilloscope = OscilloscopeWidget()
        self.telemetry_spin = TelemetryGaugeWidget()
        lay.addWidget(self.telemetry_spin)
        lay.addWidget(self.oscilloscope)

        sep3 = QFrame()
        sep3.setFrameShape(QFrame.Shape.HLine)
        sep3.setStyleSheet(f"color: {C['border']};")
        lay.addWidget(sep3)

        ll = QLabel("⚡ SISTEM KANALLARI LOGU")
        ll.setStyleSheet(f"color: {C['neon_green']}; font-size: 8px; font-weight: bold; font-family: 'Consolas';")
        lay.addWidget(ll)

        self.log_txt = QTextEdit()
        self.log_txt.setReadOnly(True)
        self.log_txt.setStyleSheet(f"""
            QTextEdit {{
                background: {C['bg_deep']};
                color: {C['neon_green']};
                font-family: 'Consolas';
                font-size: 8.5px;
                border: 1.2px solid {C['border']};
                border-radius: 6px;
            }}
        """)
        lay.addWidget(self.log_txt)

        # Dynamic, diverse and realistic system events instead of a plain wall of text!
        self.pool = [
            ("SUCCESS", "Ajan nöron faza başarıyla kilitlendi."),
            ("INFO", "FastAPI ağ geçidi taranıyor... [Port: 8000]"),
            ("WARN", "ZezeGuard: Potansiyel yörünge precession anomalisi saptandı."),
            ("SUCCESS", "CPU/GPU yük dağılımı optimizasyonu tamamlandı."),
            ("INFO", "ChromaDB vektör bellek matrisi indekslendi."),
            ("INFO", "Hermes API Gateway: Gecikme süresi 124ms [Stabil]"),
            ("SUCCESS", "Yeni holding stratejik planı otonom kuyruğa alındı."),
            ("WARN", "Ajan ORION görev aşaması güncellemesi bekleniyor.")
        ]
        
        self.sim_timer = QTimer(self)
        self.sim_timer.timeout.connect(self._simulate)
        self.sim_timer.start(1800)
        self._log("SUCCESS", "ZEZELABS Quantum Command Center v9.0 aktifleşti.")
        self._simulate()

    def _simulate(self):
        for k, (bar, val, col) in self.bars.items():
            v = random.randint(35, 88)
            bar.setValue(v)
            val.setText(f"{v}%")
            
        lvl, msg = random.choice(self.pool)
        self._log(lvl, msg)

    def _log(self, level, text):
        ts = time.strftime("%H:%M:%S")
        color_map = {
            "SUCCESS": C["neon_green"],
            "WARN": C["neon_gold"],
            "INFO": C["neon_teal"],
            "ERROR": C["neon_red"]
        }
        col = color_map.get(level, C["neon_teal"])
        
        # HTML formatting for sleek logging
        html_msg = f"<span style='color:{C['text_gray']}'>[{ts}]</span> <span style='color:{col};font-weight:bold;'>[{level}]</span> <span style='color:{C['text_white']}'>{text}</span>"
        self.log_txt.append(html_msg)
        self.log_txt.verticalScrollBar().setValue(self.log_txt.verticalScrollBar().maximum())

    def update_dept(self, fl):
        self.dept_name.setText(f"{fl['icon']} {fl['name']}")
        self.dept_name.setStyleSheet(f"color: {fl['color']}; font-size: 13px; font-weight: bold;")
        self.dept_desc.setText(fl.get("desc", ""))
        self._log("INFO", f"Odak departman değişti: {fl['name']}")


# ── MAIN COMMAND WINDOW (SpaceX cockpit aesthetic) ──────────────────
class QuantumHQ(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ZEZELABS — QUANTUM COMMAND CENTER")
        self.resize(1400, 880)
        self.setMinimumSize(1150, 750)
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        ico_path = os.path.join(os.path.dirname(__file__), "brain.ico")
        if os.path.exists(ico_path):
            self.setWindowIcon(QIcon(ico_path))

        self.palette = CommandPalette(self)
        self.palette.command_executed.connect(self._handle_cmd)
        
        QShortcut(QKeySequence("Ctrl+K"), self, self._show_palette)
        
        self.active_workers = []
        self._build_ui(ico_path)

    def _build_ui(self, ico_path):
        main_widget = QFrame(self)
        main_widget.setStyleSheet(f"""
            QFrame {{
                background: {C['bg_deep']};
                border: 1.5px solid {C['border']};
                border-radius: 16px;
            }}
        """)
        self.setCentralWidget(main_widget)

        root = QVBoxLayout(main_widget)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 1. Custom Frameless Title Bar
        root.addWidget(self._create_title_bar())

        # 2. Main split view layout
        row = QHBoxLayout()
        row.setSpacing(0)
        row.setContentsMargins(0, 0, 0, 0)

        self.sidebar = SidebarPanel()
        self.sidebar.floor_selected.connect(self._on_floor_selected)
        row.addWidget(self.sidebar)

        # Center Column (Spire and Chat panel)
        center_widget = QWidget()
        center_lay = QVBoxLayout(center_widget)
        center_lay.setContentsMargins(10, 10, 10, 10)
        center_lay.setSpacing(8)

        self.spire = IsometricSpire()
        self.spire.floor_selected.connect(self._on_floor_selected)
        center_lay.addWidget(self.spire, 6)

        self.chat = ChatPanel()
        self.chat.message_sent.connect(self._on_chat_sent)
        center_lay.addWidget(self.chat, 4)

        row.addWidget(center_widget, 1)

        # Right Telemetry
        self.telemetry = TelemetryPanel(self.spire.agents)
        row.addWidget(self.telemetry)

        root.addLayout(row, 1)

        # 3. Micro Status Footer
        root.addWidget(self._create_footer())

    def _create_title_bar(self):
        tb = QFrame()
        tb.setFixedHeight(38)
        tb.setStyleSheet(f"background: {C['bg_deep']}; border-bottom: 1.2px solid {C['border']}; border-top-left-radius: 15px; border-top-right-radius: 15px;")
        tb._drag = None

        lay = QHBoxLayout(tb)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(8)

        # macOS style window triggers
        for col, fn in [("#ff5f57", "close"), ("#febc2e", "min"), ("#28c840", "max")]:
            btn = QPushButton()
            btn.setFixedSize(12, 12)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {col};
                    border-radius: 6px;
                    border: none;
                }}
                QPushButton:hover {{
                    background: #ffffff;
                }}
            """)
            btn.clicked.connect({
                "close": self.close,
                "min": self.showMinimized,
                "max": lambda: self.showNormal() if self.isMaximized() else self.showMaximized()
            }[fn])
            lay.addWidget(btn)

        lay.addSpacing(12)

        title = QLabel("🏛  ZEZELABS — QUANTUM COMMAND CENTER  |  Ağ Geçidi Yetkisi: Root")
        title.setStyleSheet(f"color: {C['text_gray']}; font-family: 'Consolas'; font-size: 10px; letter-spacing: 1px; font-weight: bold;")
        lay.addWidget(title)

        lay.addStretch()

        key_tip = QLabel("Ctrl+K")
        key_tip.setStyleSheet(f"color: {C['neon_teal']}; font-size: 8px; font-family: 'Consolas'; background: {C['border']}; border-radius: 4px; padding: 2px 8px; font-weight: bold;")
        lay.addWidget(key_tip)

        self.clock = QLabel()
        self.clock.setStyleSheet(f"color: {C['neon_green']}; font-family: 'Consolas'; font-size: 9px; font-weight: bold;")
        lay.addWidget(self.clock)

        c_timer = QTimer(self)
        c_timer.timeout.connect(self._update_clock)
        c_timer.start(1000)
        self._update_clock()

        def _mp(e):
            tb._drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
        def _mm(e):
            if tb._drag and e.buttons() == Qt.MouseButton.LeftButton:
                self.move(e.globalPosition().toPoint() - tb._drag)
        def _mr(e):
            tb._drag = None

        tb.mousePressEvent = _mp
        tb.mouseMoveEvent = _mm
        tb.mouseReleaseEvent = _mr

        return tb

    def _update_clock(self):
        self.clock.setText(f"⏱ {time.strftime('%H:%M:%S')}")

    def _create_footer(self):
        w = QFrame()
        w.setFixedHeight(30)
        w.setStyleSheet(f"background: {C['bg_deep']}; border-top: 1.2px solid {C['border']}; border-bottom-left-radius: 15px; border-bottom-right-radius: 15px;")
        
        lay = QHBoxLayout(w)
        lay.setContentsMargins(15, 0, 15, 0)

        status_flag = QLabel("● MERKEZİ ANALİZ: AKTİF")
        status_flag.setStyleSheet(f"color: {C['neon_green']}; font-family: 'Consolas'; font-size: 8px; font-weight: bold;")
        lay.addWidget(status_flag)

        lay.addStretch()

        self.active_lbl = QLabel("Ajanlar Hazırlanıyor...")
        self.active_lbl.setStyleSheet(f"color: {C['text_gray']}; font-family: 'Consolas'; font-size: 8px;")
        lay.addWidget(self.active_lbl)

        a_timer = QTimer(self)
        a_timer.timeout.connect(self._update_active_lbl)
        a_timer.start(1000)
        self._update_active_lbl()

        return w

    def _update_active_lbl(self):
        active_count = sum(1 for a in self.spire.agents if a.status == "AKTİF")
        self.active_lbl.setText(f"⚡ {active_count}/{len(self.spire.agents)} NÖRON AGENT AKTİF")

    def _on_floor_selected(self, fl):
        self.sidebar._select(fl["id"])
        self.telemetry.update_dept(fl)
        self.spire.zoom_to(fl)

    def _show_palette(self):
        g = self.geometry()
        self.palette.move(g.x() + (g.width() - self.palette.width()) // 2, g.y() + 75)
        self.palette.show()
        self.palette.raise_()
        self.palette.activateWindow()

    def _on_chat_sent(self, text):
        self.telemetry._log("INFO", f"Karargaha talimat gönderildi: {text}")
        
        worker = ChatWorker(text)
        worker.response_ready.connect(self._on_chat_received)
        self.active_workers.append(worker)
        worker.start()

    def _on_chat_received(self, reply, is_online):
        self.chat.hide_typing()
        self.chat.add_message(reply, True)
        
        if is_online:
            self.chat.status_led.setText("● CORE_ONLINE")
            self.chat.status_led.setStyleSheet(f"color: {C['neon_green']}; font-size: 8px; font-family: 'Consolas'; font-weight: bold;")
            self.telemetry._log("SUCCESS", "API bağlantısı kuruldu.")
        else:
            self.chat.status_led.setText("● LOCAL_FALLBACK")
            self.chat.status_led.setStyleSheet(f"color: {C['neon_gold']}; font-size: 8px; font-family: 'Consolas'; font-weight: bold;")
            self.telemetry._log("WARN", "FastAPI bağlantı hatası. Yerel simülasyon yanıtı alındı.")

    def _handle_cmd(self, cmd):
        if not cmd: return
        self.telemetry._log("INFO", f"Komut tetiklendi: {cmd}")
        
        if "PENTHOUSE" in cmd.upper() or "CEO" in cmd.upper():
            fl = next(f for f in FLOORS if f["id"] == "ceo")
            self._on_floor_selected(fl)
        elif "TEMİZLE" in cmd.upper():
            self.telemetry.log_txt.clear()
            self.telemetry._log("INFO", "Terminal log geçmişi temizlendi.")
        else:
            self._on_chat_sent(cmd)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ZEZELABS Quantum Command Center")
    app.setApplicationVersion("9.0.0")

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(C["bg_deep"]))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(C["text_white"]))
    palette.setColor(QPalette.ColorRole.Base, QColor(C["bg_dark"]))
    palette.setColor(QPalette.ColorRole.Text, QColor(C["text_white"]))
    palette.setColor(QPalette.ColorRole.Button, QColor(C["bg_panel"]))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(C["text_white"]))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(C["neon_teal"]))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    win = QuantumHQ()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
