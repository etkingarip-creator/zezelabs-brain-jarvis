"""
ZEZELABS JARVIS v10.0 — QUANTUM COMMAND CENTER (1-3 HYBRID BLUEPRINT MASTERPIECE)
SpaceX / NASA Mission Control Style · Tactical Blueprint Floorplan · Neural Node Network
Translucent Office Rooms · Scrollable Sidebar · High-Readability Chat Balons · 60 FPS Cyber Particles
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

# ── Design Tokens (Tactical Cockpit Colors) ──────────────────────────
C = {
    "bg_deep":      "#020407",   # Deep obsidian dark space
    "bg_dark":      "#040813",   # Rich translucent slate
    "bg_panel":     "#070d1ed8",  # 85% Translucent Glassmorphic Space
    "bg_input":     "#0a1226ee",  # Input field dark glass
    "border":       "#13223fff",  # Tech boundary
    "border_glow":  "#1f3661ff",  # Highlight neon boundary
    "text_white":   "#f1f5f9",   # High-contrast white
    "text_gray":    "#64748b",   # Space gray telemetry
    "text_dark":    "#24314c",   # Muted blueprint grid lines
    
    "neon_teal":    "#00f2fe",   # Hologram Core Cyan
    "neon_pink":    "#ff007f",   # Alert Pink
    "neon_purple":  "#a855f7",   # Strategy / Matrix Purple
    "neon_gold":    "#ffd700",   # CEO Gold
    "neon_green":   "#10b981",   # System OK Green
    "neon_red":     "#ef4444",   # Critical Red
}

# ── 1-3 Hybrid Blueprint Zone Definitions ───────────────────────────
ZONES = {
    "ceo":       {"name": "CEO Penthouse Suite",   "x": 500, "y": 100, "w": 200, "h": 90,  "color": C["neon_gold"],   "icon": "👑", "desc": "Holding Stratejik Karar Çekirdeği"},
    "strategy":  {"name": "Strateji Savaş Odası",  "x": 500, "y": 290, "w": 230, "h": 115, "color": C["neon_purple"], "icon": "🎯", "desc": "Holografik Pazar & Karar Simülasyonu"},
    "eng":       {"name": "Mühendislik Server",   "x": 190, "y": 190, "w": 200, "h": 95,  "color": C["neon_teal"],   "icon": "⚙️", "desc": "AI Kod Üretim Sunucuları"},
    "fin":       {"name": "Finans Terminal Odası", "x": 810, "y": 190, "w": 200, "h": 95,  "color": C["neon_green"],  "icon": "💰", "desc": "Arbitraj & Portföy Yönetim Masası"},
    "marketing": {"name": "Medya & Pazarlama Hub'ı","x": 190, "y": 390, "w": 200, "h": 95,  "color": C["neon_pink"],   "icon": "📡", "desc": "Sosyal Akış & Kampanya Tasarım Hub'ı"},
    "sales":     {"name": "Satış & İş Geliştirme", "x": 810, "y": 390, "w": 200, "h": 95,  "color": "#f97316",         "icon": "🚀", "desc": "Müşteri Pipeline & Anlaşma Boruları"},
    "ops":       {"name": "Operasyon Altyapı",     "x": 500, "y": 480, "w": 200, "h": 90,  "color": "#06b6d4",         "icon": "🔧", "desc": "Sistem İzleme & Kaynak Yönetim Odası"},
}

# ── Dynamic Neural Network Circuit Links ─────────────────────────────
CIRCUITS = [
    ("ceo", "strategy"),
    ("eng", "strategy"),
    ("fin", "strategy"),
    ("marketing", "strategy"),
    ("sales", "strategy"),
    ("ops", "strategy"),
    ("eng", "ceo"),
    ("fin", "ceo"),
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
            time.sleep(1.2)
            fallback_replies = [
                "📡 YEREL KONTROL MODU: Karargah FastAPI sunucusuyla iletişim kesildi.\nYerel siber eklenti ve ARO Ajan denetimleri stabil durumda.",
                "⚠️ GÜVENLİ ERİŞİM MODU: Çevrimdışı mod aktif. Ajan yörüngeleri ve neural blueprint stabil.\nYerel veri: CPU stabil, log akışı optimize.",
                "🤖 JARVIS YEREL BELLEK: Ağ bağlantısı yok. Talimatınız karargah asenkron sırasına kaydedildi.",
            ]
            self.response_ready.emit(random.choice(fallback_replies), False)


# ── Data Packet Flowing Along Neural Circuits ────────────────────────
class DataPacket:
    def __init__(self, start_zone, end_zone, col):
        self.start = start_zone
        self.end = end_zone
        self.color = col
        self.progress = random.random()
        self.speed = random.uniform(0.008, 0.02)
        self.size = random.uniform(2.5, 4.0)

    def tick(self):
        self.progress += self.speed
        if self.progress >= 1.0:
            self.progress = 0.0


# ── Quantum Neural Agent ─────────────────────────────────────────────
class QuantumAgent:
    def __init__(self, fl):
        self.fl_id = fl["id"]
        self.color = fl["color"]
        self.name = random.choice(["ARGOS", "NEXUS", "CIPHER", "VECTOR", "PULSE", "ORION", "ECHO", "TITAN", "NOVA", "KRONOS"])
        self.task = random.choice(TASKS)
        self.progress = random.uniform(15, 85)
        self.status = random.choice(["AKTİF", "AKTİF", "AKTİF", "KİLİTLİ"])
        
        # 2D Random movement variables bounded inside their office rooms
        self.px = 0.0
        self.py = 0.0
        self.angle = random.uniform(0, math.tau)
        self.speed = random.uniform(0.3, 0.9)
        self.trail = []

    def tick(self, w, h):
        # Bounded random walk inside office blueprint rectangle
        self.angle += random.uniform(-0.3, 0.3)
        self.px += self.speed * math.cos(self.angle)
        self.py += self.speed * math.sin(self.angle)

        # Constrain inside boundaries
        pad_x = w * 0.4
        pad_y = h * 0.4
        if self.px < -pad_x: self.px = -pad_x; self.angle += math.pi
        if self.px > pad_x: self.px = pad_x; self.angle += math.pi
        if self.py < -pad_y: self.py = -pad_y; self.angle += math.pi
        if self.py > pad_y: self.py = pad_y; self.angle += math.pi


# ── TACTICAL BLUEPRINT FLOORPLAN & NEURAL NODE GRID (1-3 Hybrid Canvas) ─
class BlueprintCanvas(QWidget):
    zone_selected = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)

        self.zones = ZONES
        self.agents = [QuantumAgent(fl) for fl in FLOORS for _ in range(fl["agents"])]
        
        # Create animated neural data packets running between department nodes
        self.packets = []
        for src, dst in CIRCUITS:
            z_src = ZONES[src]
            self.packets.append(DataPacket(src, dst, z_src["color"]))
            
        self.hovered_zone = None
        self.selected_zone = None
        self.zoom_t = 0.0
        self.zoom_dir = 0
        self.tick_count = 0.0

        timer = QTimer(self)
        timer.timeout.connect(self._on_tick)
        timer.start(20)

    def _on_tick(self):
        self.tick_count += 0.03
        
        for p in self.packets:
            p.tick()

        for ag in self.agents:
            # Get bound of current room
            z = ZONES[ag.fl_id]
            ag.tick(z["w"], z["h"])

        # Easing zoom transition to focused office room
        if self.zoom_dir != 0:
            self.zoom_t = max(0.0, min(1.0, self.zoom_t + 0.05 * self.zoom_dir))
            if self.zoom_t >= 1.0: self.zoom_dir = 0
            if self.zoom_t <= 0.0:
                self.zoom_dir = 0
                self.selected_zone = None

        self.update()

    def zoom_to(self, zone):
        self.selected_zone = zone
        self.zoom_dir = 1 if self.zoom_t < 0.5 else -1

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()

        # Deep blueprint space background
        bg = QRadialGradient(W / 2, H / 2, max(W, H) * 0.7)
        bg.setColorAt(0, QColor("#040714"))
        bg.setColorAt(1, QColor(C["bg_deep"]))
        p.fillRect(self.rect(), bg)

        # ── Technical Grid Lines ──
        p.setPen(QPen(QColor(C["text_dark"]), 0.7, Qt.PenStyle.SolidLine))
        grid_step = 40
        for x in range(0, W, grid_step):
            p.drawLine(x, 0, x, H)
        for y in range(0, H, grid_step):
            p.drawLine(0, y, W, y)

        # Easing Zoom Transformation Matrix
        zoom_scale = 1.0
        zoom_tx, zoom_ty = 0.0, 0.0
        if self.selected_zone and self.zoom_t > 0:
            ease_t = math.sin(self.zoom_t * math.pi / 2)
            z_info = ZONES[self.selected_zone["id"]]
            zoom_scale = 1.0 + ease_t * 0.85
            zoom_tx = (W / 2 - z_info["x"]) * ease_t * 0.85
            zoom_ty = (H / 2 - z_info["y"]) * ease_t * 0.75
            
        p.save()
        if zoom_scale != 1.0:
            p.translate(W / 2 + zoom_tx - W / 2 * zoom_scale, H / 2 + zoom_ty - H / 2 * zoom_scale)
            p.scale(zoom_scale, zoom_scale)

        # ── 1. Draw Dotted Circuit Lines (Neural Network) ──
        p.save()
        p.setPen(QPen(QColor(C["neon_teal"] + "22"), 1.0, Qt.PenStyle.DashLine))
        for src, dst in CIRCUITS:
            z_src = ZONES[src]
            z_dst = ZONES[dst]
            p.drawLine(QPointF(z_src["x"], z_src["y"]), QPointF(z_dst["x"], z_dst["y"]))
        p.restore()

        # ── 2. Draw Flowing Data Packets (Glowing Particles) ──
        p.save()
        for pkt in self.packets:
            z_src = ZONES[pkt.start]
            z_dst = ZONES[pkt.end]
            dx = z_dst["x"] - z_src["x"]
            dy = z_dst["y"] - z_src["y"]
            px = z_src["x"] + dx * pkt.progress
            py = z_src["y"] + dy * pkt.progress
            
            # Pulse glow
            p.setPen(Qt.PenStyle.NoPen)
            pc = QColor(pkt.color)
            pc.setAlpha(160)
            p.setBrush(pc)
            p.drawEllipse(QPointF(px, py), pkt.size, pkt.size)
        p.restore()

        # ── 3. Draw Translucent Office Blueprint Rooms ──
        for fl_id, z in ZONES.items():
            self._draw_blueprint_room(p, fl_id, z)

        # ── 4. Draw Agents inside Office Rooms ──
        for ag in self.agents:
            self._draw_room_agent(p, ag)

        p.restore()

        # Outer Tactical HUD Compass Ticks
        self._draw_tactical_hud(p, W, H)
        p.end()

    def _draw_blueprint_room(self, p, fl_id, z):
        is_sel = fl_id == (self.selected_zone["id"] if self.selected_zone else None)
        is_hov = fl_id == self.hovered_zone
        intensity = 1.35 if is_sel else (1.15 if is_hov else 1.0)
        col = QColor(z["color"])

        # Glassmorphic Box Fill (No more Solid Blocks!)
        p.save()
        bg_col = QColor(C["bg_panel"])
        bg_col.setAlpha(200 if is_sel else 135)
        p.setBrush(bg_col)
        
        # Tech Blueprint Thin Outline Border
        p.setPen(QPen(col, 1.2 if is_sel else 0.7))
        rx = z["x"] - z["w"] / 2
        ry = z["y"] - z["h"] / 2
        p.drawRoundedRect(QRectF(rx, ry, z["w"], z["h"]), 6, 6)

        # Micro Grid Floor Detail inside this specific office
        p.setPen(QPen(col + "0f", 0.5))
        for step_x in range(int(rx) + 15, int(rx + z["w"]), 20):
            p.drawLine(step_x, ry, step_x, ry + z["h"])
        for step_y in range(int(ry) + 15, int(ry + z["h"]), 20):
            p.drawLine(rx, step_y, rx + z["w"], step_y)

        # Draw Blueprint structural details (Office Furniture/Server Rack schematics)
        self._draw_blueprint_contents(p, fl_id, z, is_sel)

        # Technical room identifier text
        p.setPen(QColor(C["text_white"]) if is_sel else QColor(C["text_gray"]))
        p.setFont(QFont("Consolas", 7, QFont.Weight.Bold if is_sel else QFont.Weight.Normal))
        p.drawText(QRectF(rx + 6, ry + 6, z["w"] - 12, 15), Qt.AlignmentFlag.AlignLeft, f"{z['icon']} {z['name']}")

        # Coords label on bottom right
        p.setPen(QColor(col + "aa" if is_sel else C["text_dark"]))
        p.setFont(QFont("Consolas", 5))
        p.drawText(QRectF(rx + 6, ry + z["h"] - 12, z["w"] - 12, 10), Qt.AlignmentFlag.AlignRight,
                   f"LOC_X: {z['x']} | LOC_Y: {z['y']}")

        p.restore()

    def _draw_blueprint_contents(self, p, fl_id, z, active):
        p.save()
        col = QColor(z["color"])
        col.setAlpha(60 if active else 30)
        p.setPen(QPen(col, 0.8))
        p.setBrush(Qt.BrushStyle.NoBrush)

        cx, cy = z["x"], z["y"]

        if fl_id == "ceo":
            # Prestigious executive desk and circular conference blueprint
            p.drawEllipse(QPointF(cx, cy + 10), 22, 16)
            p.drawRect(QRectF(cx - 35, cy + 8, 70, 4))
        elif fl_id == "strategy":
            # Large circular tactical holo-table blueprint
            p.drawEllipse(QPointF(cx, cy + 12), 32, 22)
            p.drawEllipse(QPointF(cx, cy + 12), 15, 10)
            p.drawLine(cx - 32, cy + 12, cx + 32, cy + 12)
        elif fl_id == "eng":
            # Grid representing rows of server racks
            p.drawRect(QRectF(cx - 40, cy - 10, 20, 40))
            p.drawRect(QRectF(cx + 20, cy - 10, 20, 40))
            for i in range(4):
                p.drawLine(cx - 40, cy - 10 + i*13, cx - 20, cy - 10 + i*13)
                p.drawLine(cx + 20, cy - 10 + i*13, cx + 40, cy - 10 + i*13)
        elif fl_id == "fin":
            # Multiple terminal workstation layouts
            p.drawRect(QRectF(cx - 45, cy + 5, 25, 15))
            p.drawRect(QRectF(cx + 20, cy + 5, 25, 15))
            p.drawLine(cx - 45, cy + 5, cx - 20, cy + 20)
            p.drawLine(cx + 20, cy + 5, cx + 45, cy + 20)
        elif fl_id == "marketing":
            # Circular soundwaves blueprint layout
            p.drawArc(QRectF(cx - 30, cy, 60, 40), 0, 180 * 16)
            p.drawEllipse(QPointF(cx, cy + 20), 10, 8)
        elif fl_id == "sales":
            # Deal pipeline tubes
            p.drawRoundedRect(QRectF(cx - 40, cy + 5, 80, 12), 4, 4)
            p.drawEllipse(QPointF(cx - 20, cy + 11), 3, 3)
            p.drawEllipse(QPointF(cx + 20, cy + 11), 3, 3)
        elif fl_id == "ops":
            # Dual rotating machinery wheels schematic
            p.drawEllipse(QPointF(cx - 25, cy + 12), 14, 14)
            p.drawEllipse(QPointF(cx + 25, cy + 12), 10, 10)

        p.restore()

    def _draw_room_agent(self, p, ag):
        z = ZONES[ag.fl_id]
        # Bounded local room coordinates transformed to global blueprint coords
        sx = z["x"] + ag.px
        sy = z["y"] + ag.py
        orb_r = 4.5

        # Beautiful clean plasma trails
        for i, tp in enumerate(ag.trail):
            alpha = int(120 * (i / max(len(ag.trail), 1)) ** 1.8)
            tc = QColor(ag.color)
            tc.setAlpha(alpha)
            p.setBrush(tc)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(tp, 2.0, 2.0)

        ag.trail.append(QPointF(sx, sy))
        if len(ag.trail) > 10: ag.trail.pop(0)

        # Pulse Glow
        pf = abs(math.sin(ag.pulse))
        p.setPen(Qt.PenStyle.NoPen)
        gc = QColor(ag.color)
        gc.setAlpha(int(65 * pf))
        p.setBrush(gc)
        p.drawEllipse(QPointF(sx, sy), orb_r * 2.2, orb_r * 2.2)

        # Core
        core = QRadialGradient(sx - 1, sy - 1, orb_r)
        core.setColorAt(0, QColor("#ffffff"))
        core.setColorAt(0.5, QColor(ag.color))
        core.setColorAt(1, QColor(ag.color).darker(200))
        p.setBrush(core)
        p.drawEllipse(QPointF(sx, sy), orb_r, orb_r)

    def _draw_tactical_hud(self, p, W, H):
        p.save()
        p.setPen(QPen(QColor(C["neon_teal"] + "55"), 1.0))
        p.setFont(QFont("Consolas", 7))
        
        # Corner tactical brackets on screen borders
        pad = 12
        length = 15
        
        # Top-Left
        p.drawLine(pad, pad, pad + length, pad)
        p.drawLine(pad, pad, pad, pad + length)
        # Top-Right
        p.drawLine(W - pad, pad, W - pad - length, pad)
        p.drawLine(W - pad, pad, W - pad, pad + length)
        # Bottom-Left
        p.drawLine(pad, H - pad, pad + length, H - pad)
        p.drawLine(pad, H - pad, pad, H - pad - length)
        # Bottom-Right
        p.drawLine(W - pad, H - pad, W - pad - length, H - pad)
        p.drawLine(W - pad, H - pad, W - pad, H - pad - length)

        p.drawText(QPointF(20, 22), "SYS_GRID: ON-LINE")
        p.drawText(QPointF(W - 130, 22), f"TACTICAL_BLUEPRINT_v10")
        p.restore()

    def mouseMoveEvent(self, event):
        pos = event.position()
        self.hovered_zone = None
        for fl_id, z in ZONES.items():
            rx = z["x"] - z["w"] / 2
            ry = z["y"] - z["h"] / 2
            if QRectF(rx, ry, z["w"], z["h"]).contains(pos):
                self.hovered_zone = fl_id
                self.setCursor(Qt.CursorShape.PointingHandCursor)
                return
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, event):
        pos = event.position()
        for fl_id, z in ZONES.items():
            rx = z["x"] - z["w"] / 2
            ry = z["y"] - z["h"] / 2
            if QRectF(rx, ry, z["w"], z["h"]).contains(pos):
                fl = next(f for f in FLOORS if f["id"] == fl_id)
                self.zone_selected.emit(fl)
                self.zoom_to(fl)
                return


# ── REAL-TIME OSCILLOSCOPE (NASA Telemetry Waveform) ────────────────
class OscilloscopeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
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
        for y in range(0, H, 15):
            p.drawLine(0, y, W, y)
        for x in range(0, W, 40):
            p.drawLine(x, 0, x, H)

        # Wave paths
        path = QPainterPath()
        path.moveTo(0, H / 2)
        for x in range(0, W, 3):
            y = H / 2 + math.sin(x * 0.04 + self.phase) * (H * 0.28) * (0.8 + 0.2 * math.cos(self.phase * 0.35))
            y += math.sin(x * 0.18 + self.phase * 2) * 2
            path.lineTo(x, y)

        p.setOpacity(0.15)
        p.setPen(QPen(QColor(C["neon_teal"]), 6.0))
        p.drawPath(path)

        p.setOpacity(1.0)
        p.setPen(QPen(QColor(C["neon_teal"]), 1.4))
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
        r = 35

        p.fillRect(self.rect(), QColor("#040813"))

        # Outer ticks
        p.save()
        p.translate(cx, cy)
        p.rotate(self.angle)
        p.setPen(QPen(QColor(C["neon_teal"] + "55"), 1.0))
        for i in range(12):
            p.rotate(30)
            p.drawLine(r - 5, 0, r, 0)
        p.restore()

        # Inner pulse
        p.save()
        pulse = 0.8 + 0.2 * abs(math.sin(self.angle * 0.05))
        p.setPen(QPen(QColor(C["neon_pink"] + "aa"), 1.2))
        p.drawEllipse(QPointF(cx, cy), r * 0.7 * pulse, r * 0.7 * pulse)
        p.restore()

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


# ── COMPACT HIGH-READABILITY CHAT BUBBLES ───────────────────────────
class ChatBubble(QWidget):
    def __init__(self, text, is_jarvis, time_str, parent=None):
        super().__init__(parent)
        self.is_jarvis = is_jarvis
        self.time_str = time_str
        
        main_lay = QHBoxLayout(self)
        main_lay.setContentsMargins(6, 4, 6, 4)
        
        self.box = QFrame()
        
        # CRITICAL AESTHETIC FIX: Beautifully size-restricted bubbles!
        if is_jarvis:
            bg_col = "#060a16e6"
            border_col = C["neon_teal"]
            self.box.setStyleSheet(f"""
                QFrame {{
                    background: {bg_col};
                    border: 1.2px solid {border_col};
                    border-radius: 12px;
                }}
            """)
            main_lay.addWidget(self.box)
            main_lay.addStretch(2)  # Limits width perfectly
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
            main_lay.addStretch(2)
            main_lay.addWidget(self.box)

        box_lay = QVBoxLayout(self.box)
        box_lay.setContentsMargins(12, 10, 12, 10)
        box_lay.setSpacing(4)

        header = QHBoxLayout()
        sender = QLabel("🤖 JARVIS" if is_jarvis else "👤 CEO USER")
        
        # CRITICAL READABILITY FIX: Increased font-size and distinct weight!
        sender.setStyleSheet(f"font-weight: bold; font-size: 11px; color: {C['neon_teal'] if is_jarvis else C['neon_gold']}; font-family: 'Consolas';")
        header.addWidget(sender)
        header.addStretch()
        
        ts = QLabel(time_str)
        ts.setStyleSheet(f"color: {C['text_gray']}; font-size: 9px; font-family: 'Consolas';")
        header.addWidget(ts)
        box_lay.addLayout(header)

        body = QLabel(text)
        body.setWordWrap(True)
        
        # CRITICAL READABILITY FIX: High contrast 12px Segoe UI for perfect reading!
        body.setStyleSheet(f"color: {C['text_white']}; font-size: 12px; font-family: 'Segoe UI', sans-serif; line-height: 145%;")
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

        self.add_message("Zezelabs Holding Siber Karargah Kontrol Arayüzü aktif.\nJARVIS v10.0 Neural Engine çevrimdışı ve bulut hibrit modda hazır. Ne arzu edersiniz?", True)

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


# ── DEPARTMENTS SIDEBAR (SCROLLABLE & NO CLIPPING) ───────────────────
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

        # CRITICAL AESTHETIC FIX: Wrapped in QScrollArea to prevent ANY overlapping / clipping!
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        self.scroll_lay = QVBoxLayout(scroll_content)
        self.scroll_lay.setContentsMargins(0, 0, 0, 0)
        self.scroll_lay.setSpacing(6)

        self.cards = {}
        for fl in FLOORS:
            card = self._make_card(fl)
            self.scroll_lay.addWidget(card)
            self.cards[fl["id"]] = card

        self.scroll_lay.addStretch()
        self.scroll.setWidget(scroll_content)
        lay.addWidget(self.scroll)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"color: {C['border']}; margin: 6px 0px;")
        lay.addWidget(sep2)

        self.sys_led = QLabel("● CORE SYSTEM LOCK")
        self.sys_led.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sys_led.setStyleSheet(f"color: {C['neon_green']}; font-size: 8px; font-weight: bold; font-family: 'Consolas';")
        lay.addWidget(self.sys_led)

        ver = QLabel("JARVIS HUD v10.0")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver.setStyleSheet(f"color: {C['text_dark']}; font-size: 7px; border: 1px solid {C['border']}; border-radius: 4px; padding: 2px;")
        lay.addWidget(ver)

    def _make_card(self, fl):
        card = QFrame()
        card.setFixedHeight(48)  # Slightly reduced card height
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setProperty("fl_id", fl["id"])
        
        # Transparent border look
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
        ico.setFont(QFont("Segoe UI", 12))
        ico.setFixedWidth(18)
        c_lay.addWidget(ico)

        info = QVBoxLayout()
        info.setSpacing(1)
        name = QLabel(fl["name"])
        name.setStyleSheet(f"color: {C['text_white']}; font-size: 9.5px; font-weight: bold; font-family: 'Segoe UI';")
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

        # Oscilloscope and Telemetry spin
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
        self._log("SUCCESS", "ZEZELABS Quantum Command Center v10.0 aktifleşti.")
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
        
        html_msg = f"<span style='color:{C['text_gray']}'>[{ts}]</span> <span style='color:{col};font-weight:bold;'>[{level}]</span> <span style='color:{C['text_white']}'>{text}</span>"
        self.log_txt.append(html_msg)
        self.log_txt.verticalScrollBar().setValue(self.log_txt.verticalScrollBar().maximum())

    def update_dept(self, fl):
        self.dept_name.setText(f"{fl['icon']} {fl['name']}")
        self.dept_name.setStyleSheet(f"color: {fl['color']}; font-size: 13px; font-weight: bold;")
        self.dept_desc.setText(fl.get("desc", ""))
        self._log("INFO", f"Odak departman değişti: {fl['name']}")


# ── MAIN COMMAND WINDOW ──────────────────────────────────────────────
class QuantumHQ(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ZEZELABS — QUANTUM COMMAND CENTER")
        self.resize(1420, 900)
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

        # Title Bar
        root.addWidget(self._create_title_bar())

        # Main splitter layout
        row = QHBoxLayout()
        row.setSpacing(0)
        row.setContentsMargins(0, 0, 0, 0)

        self.sidebar = SidebarPanel()
        self.sidebar.floor_selected.connect(self._on_floor_selected)
        row.addWidget(self.sidebar)

        # Center Column
        center_widget = QWidget()
        center_lay = QVBoxLayout(center_widget)
        center_lay.setContentsMargins(10, 10, 10, 10)
        center_lay.setSpacing(8)

        self.spire = BlueprintCanvas()
        self.spire.zone_selected.connect(self._on_floor_selected)
        center_lay.addWidget(self.spire, 6)

        self.chat = ChatPanel()
        self.chat.message_sent.connect(self._on_chat_sent)
        center_lay.addWidget(self.chat, 4)

        row.addWidget(center_widget, 1)

        # Right Telemetry
        self.telemetry = TelemetryPanel(self.spire.agents)
        row.addWidget(self.telemetry)

        root.addLayout(row, 1)

        # Footer
        root.addWidget(self._create_footer())

    def _create_title_bar(self):
        tb = QFrame()
        tb.setFixedHeight(38)
        tb.setStyleSheet(f"background: {C['bg_deep']}; border-bottom: 1.2px solid {C['border']}; border-top-left-radius: 15px; border-top-right-radius: 15px;")
        tb._drag = None

        lay = QHBoxLayout(tb)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(8)

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
    app.setApplicationVersion("10.0.0")

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
