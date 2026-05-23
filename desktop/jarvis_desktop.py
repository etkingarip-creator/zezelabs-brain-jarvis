"""
╔══════════════════════════════════════════════════════════════════════════╗
║  ZEZELABS JARVIS v6.0 — QUANTUM COMMAND CENTER (SENARYO A)              ║
║  NASA Mission Control + Bloomberg Terminal + SpaceX Dragon Cockpit       ║
║  İzometrik HQ · Her Katın Görsel Dili · CEO Zoom · Sağlık Skoru         ║
╚══════════════════════════════════════════════════════════════════════════╝
"""
import sys, os, math, random, time, json
from pathlib import Path

from PySide6.QtCore import (
    Qt, QTimer, QPointF, QRectF, QSize, QRect,
    Signal, QObject, QPropertyAnimation, QEasingCurve,
    QSequentialAnimationGroup, Property
)
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QFontDatabase,
    QPainterPath, QLinearGradient, QRadialGradient,
    QIcon, QKeySequence, QShortcut, QPalette, QTransform
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFrame, QLabel, QPushButton, QLineEdit, QTextEdit,
    QScrollArea, QSizePolicy, QSystemTrayIcon, QMenu,
    QGraphicsDropShadowEffect, QDialog, QListWidget, QListWidgetItem,
    QProgressBar, QSplitter
)

# ═══════════════════════════════════════════════════════════════════
# DESIGN SYSTEM
# ═══════════════════════════════════════════════════════════════════
C = {
    "bg0": "#040609",  "bg1": "#07090f",  "bg2": "#0b0f1c",
    "bg3": "#0f1526",  "bg4": "#141d33",
    "b0":  "#111827",  "b1":  "#1f2d47",  "b2":  "#2d4163",
    "t1":  "#f0f4ff",  "t2":  "#8fa3c4",  "t3":  "#3d5275",
    "ok":  "#22d3a6",  "warn":"#f59e0b",  "err": "#f43f5e",
    "acc": "#4f8ef7",
}

# Her departman — renk, kat başlığı, ikon, görsel tema kodu
FLOORS = [
    {"id":"ceo",      "name":"CEO",          "icon":"👑", "color":"#f59e0b", "theme":"penthouse",  "health":97, "agents":1,  "floor":6},
    {"id":"strategy", "name":"Strateji",     "icon":"🎯", "color":"#4f8ef7", "theme":"radar",      "health":88, "agents":3,  "floor":5},
    {"id":"eng",      "name":"Mühendislik",  "icon":"⚙️", "color":"#8b5cf6", "theme":"server",     "health":92, "agents":5,  "floor":4},
    {"id":"fin",      "name":"Finans",       "icon":"💰", "color":"#22d3a6", "theme":"matrix",     "health":79, "agents":3,  "floor":3},
    {"id":"marketing","name":"Pazarlama",    "icon":"📡", "color":"#ec4899", "theme":"media",      "health":85, "agents":4,  "floor":2},
    {"id":"sales",    "name":"Satış",        "icon":"🚀", "color":"#f97316", "theme":"pipeline",   "health":91, "agents":3,  "floor":1},
    {"id":"ops",      "name":"Operasyon",    "icon":"🔧", "color":"#06b6d4", "theme":"machine",    "health":83, "agents":2,  "floor":0},
]

AGENT_TASKS = [
    "Q3 raporu analiz ediliyor",  "Pazar araştırması",
    "Kod optimizasyonu",          "Müşteri segmentasyonu",
    "Strateji belgesi hazırlanıyor","Veritabanı sorgusu",
    "API entegrasyon testi",      "Satış pipeline analizi",
    "Sosyal medya içeriği",       "Risk değerlendirmesi",
    "Bütçe optimizasyonu",        "Trend analizi",
]

def health_color(h):
    if h >= 90: return "#22d3a6"
    if h >= 70: return "#f59e0b"
    return "#f43f5e"


# ═══════════════════════════════════════════════════════════════════
# AGENT MODEL
# ═══════════════════════════════════════════════════════════════════
class Agent:
    def __init__(self, floor_data):
        self.floor_id = floor_data["id"]
        self.color    = floor_data["color"]
        self.name     = random.choice(["Argos","Nexus","Cipher","Vector","Pulse",
                                       "Orion","Echo","Titan","Nova","Quill"])
        self.task     = random.choice(AGENT_TASKS)
        self.progress = random.uniform(10, 95)
        self.tokens   = random.randint(300, 3800)
        self.status   = random.choice(["AKTİF","AKTİF","AKTİF","BEKLIYOR"])
        self.uptime   = random.randint(60, 7200)
        # Orbital position on the floor
        self.orbit_r  = random.uniform(28, 48)
        self.orbit_phase = random.uniform(0, math.tau)
        self.orbit_speed = random.uniform(0.015, 0.035)
        self.orb_size = random.uniform(5, 9)
        self.trail    = []          # last N screen positions
        self.pulse    = random.uniform(0, math.tau)
        self.glow_r   = random.uniform(0, math.tau)

    def tick(self):
        self.orbit_phase += self.orbit_speed
        self.pulse       += 0.07
        self.glow_r      += 0.05
        self.uptime      += 1
        if self.status == "AKTİF":
            self.progress = min(100, self.progress + random.uniform(0, 0.4))
            self.tokens   = min(4096, self.tokens + random.randint(0, 8))

    @property
    def status_color(self):
        return C["ok"] if self.status == "AKTİF" else C["warn"]


# ═══════════════════════════════════════════════════════════════════
# ISOMETRIC HQ CANVAS — THE CENTERPIECE
# ═══════════════════════════════════════════════════════════════════
class IsometricHQ(QWidget):
    floor_selected = Signal(dict)

    # Camera zoom target (0.0 = full view, 1.0 = zoomed to selected floor)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(520, 680)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)

        self.floors  = FLOORS
        self.agents  = []
        for fl in self.floors:
            for _ in range(fl["agents"]):
                self.agents.append(Agent(fl))

        self.hovered = None
        self.selected_id = None
        self._zoom   = 1.0          # 1.0 = normal, <1 = zoomed in on floor
        self._zoom_floor_y = 0.5   # normalized vertical center for zoom
        self._anim_tick = 0.0

        # Floor-specific animation states
        self._matrix_chars = [[random.choice("01アイウ") for _ in range(8)] for _ in range(7)]
        self._matrix_y     = [random.uniform(0, 1) for _ in range(7)]
        self._server_blink = [random.random() for _ in range(20)]
        self._ticker_offset = 0.0

        timer = QTimer(self)
        timer.timeout.connect(self._tick)
        timer.start(30)

    # ── Isometric math ─────────────────────────────────────────────
    def _origin(self):
        return QPointF(self.width() / 2, self.height() * 0.12)

    def _iso(self, gx, gy, gz, tw=64, th=34, fh=44):
        ox, oy = self._origin().x(), self._origin().y()
        sx = ox + (gx - gy) * (tw / 2)
        sy = oy + (gx + gy) * (th / 2) - gz * fh
        return QPointF(sx, sy)

    def _floor_polygon(self, floor_z, W=3):
        """Returns the 4 corners of a floor's top face."""
        tl = self._iso(0, 0, floor_z + 1)
        tr = self._iso(W, 0, floor_z + 1)
        br = self._iso(W, W, floor_z + 1)
        bl = self._iso(0, W, floor_z + 1)
        return tl, tr, br, bl

    def _floor_center(self, floor_z):
        tl, tr, br, bl = self._floor_polygon(floor_z)
        return QPointF((tl.x()+tr.x()+br.x()+bl.x())/4,
                       (tl.y()+tr.y()+br.y()+bl.y())/4)

    # ── Animation tick ──────────────────────────────────────────────
    def _tick(self):
        self._anim_tick += 0.035
        self._ticker_offset += 0.8
        for i in range(len(self._server_blink)):
            if random.random() < 0.05:
                self._server_blink[i] = random.random()
        for ag in self.agents:
            ag.tick()
            # Compute screen pos and append to trail
            fl_idx = next((i for i, f in enumerate(self.floors) if f["id"] == ag.floor_id), 0)
            cx, cy = self._floor_center(fl_idx).x(), self._floor_center(fl_idx).y()
            sx = cx + ag.orbit_r * math.cos(ag.orbit_phase)
            sy = cy + ag.orbit_r * math.sin(ag.orbit_phase) * 0.45
            ag.trail.append(QPointF(sx, sy))
            if len(ag.trail) > 14:
                ag.trail.pop(0)
        # Matrix rain
        for i in range(7):
            self._matrix_y[i] += 0.008
            if self._matrix_y[i] > 1.0:
                self._matrix_y[i] = 0.0
                self._matrix_chars[i] = [random.choice("01アイウエオカキクサシスセソタチ") for _ in range(8)]
        self.update()

    # ── Per-floor visual themes ─────────────────────────────────────
    def _draw_floor_detail(self, painter, fl, fl_idx, tl, tr, br, bl):
        theme = fl["theme"]
        cx = (tl.x()+tr.x()+br.x()+bl.x())/4
        cy = (tl.y()+tr.y()+br.y()+bl.y())/4
        w  = abs(tr.x() - tl.x()) * 0.7
        h  = abs(bl.y() - tl.y()) * 0.7

        if theme == "penthouse":
            # Gold shimmer + glass reflection lines
            painter.setPen(QPen(QColor("#f59e0b"), 0.8))
            for i in range(3):
                ox = cx - w*0.3 + i * w*0.3
                painter.drawLine(QPointF(ox, cy - h*0.3), QPointF(ox + w*0.2, cy + h*0.2))
            painter.setPen(QPen(QColor("#ffffff"), 0.5))
            painter.drawLine(QPointF(cx - w*0.3, cy), QPointF(cx + w*0.3, cy))

        elif theme == "radar":
            # Rotating radar sweep
            r = min(w, h) * 0.35
            angle = (self._anim_tick * 2) % math.tau
            painter.setPen(QPen(QColor("#4f8ef740"), 0.5))
            painter.drawEllipse(QPointF(cx, cy), r, r * 0.4)
            painter.setPen(QPen(QColor("#4f8ef7"), 1.2))
            painter.drawLine(QPointF(cx, cy),
                             QPointF(cx + r * math.cos(angle),
                                     cy + r * 0.4 * math.sin(angle)))

        elif theme == "server":
            # Blinking server rack LEDs
            painter.setPen(Qt.PenStyle.NoPen)
            for i, blink in enumerate(self._server_blink[:8]):
                lx = cx - w*0.3 + (i % 4) * w*0.18
                ly = cy - h*0.15 + (i // 4) * h*0.25
                led_col = QColor("#22d3a6") if blink > 0.3 else QColor("#8b5cf6")
                led_col.setAlpha(int(180 + 75 * math.sin(self._anim_tick + i)))
                painter.setBrush(led_col)
                painter.drawEllipse(QPointF(lx, ly), 2, 2)

        elif theme == "matrix":
            # Matrix rain characters
            painter.setFont(QFont("Consolas", 5))
            for i, chars in enumerate(self._matrix_chars[:4]):
                for j, ch in enumerate(chars[:3]):
                    alpha = max(0, int(255 * (1 - abs(self._matrix_y[i] - j/3))))
                    col = QColor("#22d3a6")
                    col.setAlpha(alpha)
                    painter.setPen(col)
                    px = cx - w*0.3 + i * w*0.22
                    py = cy - h*0.3 + j * h*0.25
                    painter.drawText(QPointF(px, py), ch)

        elif theme == "media":
            # Animated signal bars
            painter.setPen(Qt.PenStyle.NoPen)
            for i in range(5):
                bar_h = (0.3 + 0.7 * abs(math.sin(self._anim_tick * 1.5 + i))) * h * 0.5
                bar_x = cx - w*0.3 + i * w*0.15
                col = QColor("#ec4899")
                col.setAlpha(160)
                painter.setBrush(col)
                painter.drawRect(QRectF(bar_x, cy - bar_h/2, w*0.1, bar_h))

        elif theme == "pipeline":
            # Flowing deal orbs along a pipe
            painter.setPen(QPen(QColor("#f9731660"), 0.7))
            painter.drawLine(QPointF(cx - w*0.4, cy), QPointF(cx + w*0.4, cy))
            for i in range(3):
                t = ((self._anim_tick * 0.5 + i * 0.33) % 1.0)
                ox = cx - w*0.4 + t * w*0.8
                col = QColor("#f97316")
                col.setAlpha(int(200 * abs(math.sin(self._anim_tick + i))))
                painter.setBrush(col)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(ox, cy), 4, 4)

        elif theme == "machine":
            # Rotating fan blades
            painter.setPen(QPen(QColor("#06b6d4"), 0.8))
            for blade in range(4):
                angle = self._anim_tick * 3 + blade * math.pi/2
                painter.drawLine(
                    QPointF(cx, cy),
                    QPointF(cx + 14 * math.cos(angle), cy + 8 * math.sin(angle))
                )

    # ── Draw one floor slab ─────────────────────────────────────────
    def _draw_floor(self, painter, fl_idx, fl):
        W = 3
        gz = fl_idx
        tl, tr, br, bl = self._floor_polygon(gz)
        bbl_tl = self._iso(0, 0, gz)
        bbl_tr = self._iso(W, 0, gz)
        bbl_br = self._iso(W, W, gz)
        bbl_bl = self._iso(0, W, gz)

        color   = QColor(fl["color"])
        is_sel  = fl["id"] == self.selected_id
        is_hov  = fl["id"] == self.hovered
        h_score = fl["health"]
        h_col   = QColor(health_color(h_score))
        pulse   = abs(math.sin(self._anim_tick * 1.5 + fl_idx))

        # Intensity
        intensity = 1.4 if is_sel else (1.1 if is_hov else 1.0)

        # ── Left face
        lf = QPainterPath()
        lf.moveTo(tl); lf.lineTo(bl); lf.lineTo(bbl_bl); lf.lineTo(bbl_tl); lf.closeSubpath()
        lc = QColor(fl["color"]); lc.setAlpha(int(80 * intensity + 15 * pulse))
        painter.fillPath(lf, lc)

        # ── Right face
        rf = QPainterPath()
        rf.moveTo(tr); rf.lineTo(br); rf.lineTo(bbl_br); rf.lineTo(bbl_tr); rf.closeSubpath()
        rc = QColor(fl["color"]); rc.setAlpha(int(55 * intensity + 10 * pulse))
        painter.fillPath(rf, rc)

        # ── Top face (with gradient)
        top = QPainterPath()
        top.moveTo(tl); top.lineTo(tr); top.lineTo(br); top.lineTo(bl); top.closeSubpath()
        grad = QLinearGradient(tl, br)
        tc1 = QColor(fl["color"]); tc1.setAlpha(int(170 * intensity + 30 * pulse))
        tc2 = QColor(fl["color"]); tc2.setAlpha(int(90 * intensity))
        grad.setColorAt(0, tc1); grad.setColorAt(1, tc2)
        painter.fillPath(top, grad)

        # ── Health score border on top
        pen_width = 2.0 if is_sel else (1.2 if is_hov else 0.7)
        border_col = h_col if is_sel else QColor(fl["color"])
        border_col.setAlpha(int(200 * intensity))
        painter.setPen(QPen(border_col, pen_width))
        painter.drawPath(top)
        painter.drawPath(lf)
        painter.drawPath(rf)

        # ── Floor-specific visual detail on top face
        painter.save()
        self._draw_floor_detail(painter, fl, fl_idx, tl, tr, br, bl)
        painter.restore()

        # ── Label on top face
        cx = (tl.x()+tr.x()+br.x()+bl.x())/4
        cy = (tl.y()+tr.y()+br.y()+bl.y())/4
        painter.setPen(QColor(C["t1"]) if is_sel else QColor(C["t2"]))
        font = QFont("Segoe UI", 7 if not is_sel else 8,
                     QFont.Weight.Bold if is_sel else QFont.Weight.Normal)
        painter.setFont(font)
        painter.drawText(QPointF(cx - 28, cy + 4), f"{fl['icon']} {fl['name']}")

        # ── Health bar (tiny, on left face)
        bar_x  = bbl_tl.x() + 4
        bar_y  = (bbl_tl.y() + tl.y()) / 2
        bar_w  = 22
        bar_h  = 4
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#ffffff20"))
        painter.drawRoundedRect(QRectF(bar_x, bar_y - 2, bar_w, bar_h), 2, 2)
        painter.setBrush(h_col)
        painter.drawRoundedRect(QRectF(bar_x, bar_y - 2, bar_w * h_score / 100, bar_h), 2, 2)

        return top  # for hit testing

    # ── Draw agent orb with trail ───────────────────────────────────
    def _draw_agent(self, painter, ag):
        fl_idx = next((i for i, f in enumerate(self.floors) if f["id"] == ag.floor_id), 0)
        cx, cy = self._floor_center(fl_idx).x(), self._floor_center(fl_idx).y()
        sx = cx + ag.orbit_r * math.cos(ag.orbit_phase)
        sy = cy + ag.orbit_r * math.sin(ag.orbit_phase) * 0.45

        # Trail
        for i, tp in enumerate(ag.trail):
            alpha = int(120 * (i / len(ag.trail)) ** 1.8)
            r = ag.orb_size * 0.4 * (i / len(ag.trail))
            tc = QColor(ag.color); tc.setAlpha(alpha)
            painter.setBrush(tc); painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(tp, r, r)

        # Glow
        pf = abs(math.sin(ag.pulse))
        glow_r = ag.orb_size + 7 * pf
        glow = QRadialGradient(sx, sy, glow_r * 2.5)
        gc = QColor(ag.color); gc.setAlpha(int(55 * pf))
        glow.setColorAt(0, gc); glow.setColorAt(1, QColor(0,0,0,0))
        painter.setBrush(glow); painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(sx, sy), glow_r * 2.5, glow_r * 2.5)

        # Core
        r = ag.orb_size
        core = QRadialGradient(sx - r*0.35, sy - r*0.35, r)
        core.setColorAt(0, QColor(255,255,255,230))
        core.setColorAt(0.5, QColor(ag.color))
        core.setColorAt(1, QColor(ag.color).darker(200))
        painter.setBrush(core)
        painter.setPen(QPen(QColor(ag.color).lighter(160), 0.5))
        painter.drawEllipse(QPointF(sx, sy), r, r)

    # ── Main paint ─────────────────────────────────────────────────
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        W, H = self.width(), self.height()

        # Deep space background
        bg = QRadialGradient(W/2, H*0.4, max(W,H)*0.7)
        bg.setColorAt(0, QColor("#0d1526"))
        bg.setColorAt(1, QColor(C["bg0"]))
        p.fillRect(self.rect(), bg)

        # Subtle iso grid
        p.setPen(QPen(QColor("#1a2540"), 0.5))
        for gx in range(5):
            for gy in range(5):
                pt = self._iso(gx, gy, 0)
                p.drawPoint(pt)

        # Draw floors bottom to top
        self._top_paths = []
        for i, fl in enumerate(self.floors):
            path = self._draw_floor(p, i, fl)
            self._top_paths.append((i, fl, path))

        # Draw agents on top of floors
        for ag in self.agents:
            self._draw_agent(p, ag)

        # Scanlines overlay
        p.setOpacity(0.025)
        p.setPen(QPen(QColor("#a0d4ff"), 1))
        for y in range(0, H, 4):
            p.drawLine(0, y, W, y)
        p.setOpacity(1.0)

        # Top title
        p.setPen(QColor(C["t2"]))
        f = QFont("Segoe UI", 9)
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        p.setFont(f)
        p.drawText(QRectF(0, 8, W, 18), Qt.AlignmentFlag.AlignHCenter,
                   "🏛  ZEZELABS QUANTUM COMMAND CENTER")

        # Ticker (bottom of canvas)
        self._draw_ticker(p, W, H)
        p.end()

    def _draw_ticker(self, p, W, H):
        msgs = [f"  ⚡ {fl['icon']} {fl['name']}: Sağlık %{fl['health']}  " for fl in self.floors]
        ticker_text = "  •  ".join(msgs)
        p.setFont(QFont("Consolas", 8))

        # Measure text width
        fm = p.fontMetrics()
        text_w = fm.horizontalAdvance(ticker_text)
        offset = int(self._ticker_offset) % (text_w + W)

        p.setPen(QColor(C["t3"]))
        p.fillRect(QRectF(0, H - 20, W, 20), QColor(C["bg0"]))
        p.drawText(QPointF(W - offset, H - 6), ticker_text)
        if W - offset + text_w < W:
            p.drawText(QPointF(W - offset + text_w + W, H - 6), ticker_text)

    def mouseMoveEvent(self, event):
        pos = event.position()
        self.hovered = None
        if hasattr(self, "_top_paths"):
            for (i, fl, path) in reversed(self._top_paths):
                if path.contains(pos):
                    self.hovered = fl["id"]
                    self.setCursor(Qt.CursorShape.PointingHandCursor)
                    return
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, event):
        pos = event.position()
        if hasattr(self, "_top_paths"):
            for (i, fl, path) in reversed(self._top_paths):
                if path.contains(pos):
                    self.selected_id = fl["id"]
                    self.floor_selected.emit(fl)
                    return


# ═══════════════════════════════════════════════════════════════════
# COMMAND PALETTE
# ═══════════════════════════════════════════════════════════════════
class CommandPalette(QDialog):
    command_executed = Signal(str)
    CMDS = [
        ("ajan listele",         "Tüm aktif ajanları listele"),
        ("görev ver: [metin]",   "Tüm sisteme görev gönder"),
        ("CEO raporu",           "CEO özet görünümünü aç"),
        ("strateji: [metin]",    "Strateji departmanına görev"),
        ("mühendislik: [metin]", "Mühendislik departmanına görev"),
        ("finans: [metin]",      "Finans departmanına görev"),
        ("sistem snapshot",      "Anlık durum kaydet"),
        ("log temizle",          "Log ekranını temizle"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(580)

        container = QFrame(self)
        container.setStyleSheet(f"""
            QFrame {{ background:{C['bg3']}; border:1px solid {C['b2']};
                      border-radius:12px; }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(50); shadow.setOffset(0, 10)
        shadow.setColor(QColor(0,0,0,200))
        container.setGraphicsEffect(shadow)

        root = QVBoxLayout(self)
        root.setContentsMargins(0,0,0,0)
        lay  = QVBoxLayout(container)
        lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)

        # Input
        row = QHBoxLayout(); row.setContentsMargins(16,14,16,14); row.setSpacing(10)
        row.addWidget(QLabel("⌘", styleSheet=f"color:{C['t3']};font-size:15px;"))
        self.inp = QLineEdit()
        self.inp.setPlaceholderText("Komut ver veya departman seç...")
        self.inp.setStyleSheet(f"background:transparent;border:none;color:{C['t1']};font-size:14px;")
        self.inp.textChanged.connect(self._filter)
        self.inp.returnPressed.connect(self._exec)
        row.addWidget(self.inp)
        lay.addLayout(row)

        div = QFrame(); div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"color:{C['b1']};")
        lay.addWidget(div)

        self.lst = QListWidget()
        self.lst.setMaximumHeight(320)
        self.lst.setStyleSheet(f"""
            QListWidget {{ background:transparent;border:none;
                           color:{C['t1']};font-size:12px;padding:6px 0; }}
            QListWidget::item {{ padding:8px 16px;border-radius:6px;margin:1px 8px; }}
            QListWidget::item:selected,QListWidget::item:hover {{
                background:{C['bg4']}; }}
        """)
        self.lst.itemActivated.connect(lambda it: (self.command_executed.emit(it.data(Qt.ItemDataRole.UserRole)), self.hide()))
        lay.addWidget(self.lst)

        footer = QLabel("↑↓ Gezin  ↵ Çalıştır  ESC Kapat")
        footer.setStyleSheet(f"color:{C['t3']};font-size:9px;border-top:1px solid {C['b0']};padding:7px 16px;")
        lay.addWidget(footer)
        root.addWidget(container)
        self._fill(self.CMDS)

    def _fill(self, cmds):
        self.lst.clear()
        for cmd, desc in cmds:
            it = QListWidgetItem(f"  {cmd}    —    {desc}")
            it.setData(Qt.ItemDataRole.UserRole, cmd)
            self.lst.addItem(it)
        if self.lst.count(): self.lst.setCurrentRow(0)

    def _filter(self, t):
        self._fill([(c,d) for c,d in self.CMDS if t.lower() in c+d] if t else self.CMDS)

    def _exec(self):
        it = self.lst.currentItem()
        if it: self.command_executed.emit(it.data(Qt.ItemDataRole.UserRole))
        elif self.inp.text(): self.command_executed.emit(self.inp.text())
        self.hide()

    def showEvent(self, e):
        super().showEvent(e)
        self.inp.clear(); self.inp.setFocus(); self._fill(self.CMDS)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape: self.hide()
        elif e.key() == Qt.Key.Key_Down:
            self.lst.setCurrentRow(min(self.lst.currentRow()+1, self.lst.count()-1))
        elif e.key() == Qt.Key.Key_Up:
            self.lst.setCurrentRow(max(self.lst.currentRow()-1, 0))
        else: super().keyPressEvent(e)


# ═══════════════════════════════════════════════════════════════════
# LEFT SIDEBAR — Department Health Dashboard
# ═══════════════════════════════════════════════════════════════════
class HealthCard(QFrame):
    clicked = Signal(dict)

    def __init__(self, fl, parent=None):
        super().__init__(parent)
        self.fl = fl
        self.setFixedHeight(62)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._selected = False
        self._build()
        self._apply_style()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8); lay.setSpacing(8)

        # Color bar
        bar = QFrame(); bar.setFixedWidth(3)
        bar.setStyleSheet(f"background:{self.fl['color']};border-radius:1px;")
        lay.addWidget(bar)

        # Icon
        ic = QLabel(self.fl["icon"])
        ic.setFont(QFont("Segoe UI", 16)); ic.setFixedWidth(26)
        lay.addWidget(ic)

        # Info
        info = QVBoxLayout(); info.setSpacing(2)
        name = QLabel(self.fl["name"])
        name.setStyleSheet(f"color:{C['t1']};font-size:11px;font-weight:bold;")
        info.addWidget(name)

        h = self.fl["health"]
        hc = health_color(h)
        sub = QLabel(f"Sağlık: %{h}  •  {self.fl['agents']} ajan")
        sub.setStyleSheet(f"color:{hc};font-size:9px;")
        info.addWidget(sub)
        lay.addLayout(info)
        lay.addStretch()

        # Mini health bar
        self._mini_bar = QProgressBar()
        self._mini_bar.setRange(0, 100)
        self._mini_bar.setValue(h)
        self._mini_bar.setFixedSize(40, 6)
        self._mini_bar.setTextVisible(False)
        self._mini_bar.setStyleSheet(f"""
            QProgressBar {{ background:{C['b0']};border-radius:3px;border:none; }}
            QProgressBar::chunk {{
                background:{hc}; border-radius:3px;
            }}
        """)
        lay.addWidget(self._mini_bar)

    def _apply_style(self):
        border = self.fl["color"] if self._selected else C["b0"]
        bg = f"{self.fl['color']}18" if self._selected else "transparent"
        self.setStyleSheet(f"""
            HealthCard {{
                background:{bg};
                border-left:3px solid {border};
                border-radius:6px;
            }}
            HealthCard:hover {{
                background:{self.fl['color']}12;
            }}
        """)

    def set_selected(self, v):
        self._selected = v
        self._apply_style()

    def mousePressEvent(self, e):
        self.clicked.emit(self.fl)


class SidebarPanel(QWidget):
    floor_selected = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(210)
        self.setStyleSheet(f"background:{C['bg2']};border-right:1px solid {C['b0']};")
        lay = QVBoxLayout(self); lay.setContentsMargins(8,10,8,10); lay.setSpacing(5)

        # Logo
        logo = QLabel("Z")
        logo.setFixedHeight(44); logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet(f"""
            background:qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 #4f8ef7,stop:1 #8b5cf6);
            color:{C['bg0']};font-size:22px;font-weight:900;
            border-radius:10px;
        """)
        lay.addWidget(logo)

        t = QLabel("ZEZELABS")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t.setStyleSheet(f"color:{C['acc']};font-size:9px;font-weight:bold;letter-spacing:3px;")
        lay.addWidget(t)

        s = QLabel("QUANTUM COMMAND CENTER")
        s.setAlignment(Qt.AlignmentFlag.AlignCenter)
        s.setWordWrap(True)
        s.setStyleSheet(f"color:{C['t3']};font-size:7px;letter-spacing:1px;")
        lay.addWidget(s)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:{C['b0']};margin:4px 0;"); lay.addWidget(sep)

        dl = QLabel("DEPARTMAN SAĞLIĞI")
        dl.setStyleSheet(f"color:{C['t3']};font-size:8px;letter-spacing:1px;padding-left:4px;")
        lay.addWidget(dl)

        self._cards = {}
        for fl in FLOORS:
            card = HealthCard(fl)
            card.clicked.connect(self._on_card)
            lay.addWidget(card)
            self._cards[fl["id"]] = card

        lay.addStretch()

        # System status
        self.sys_lbl = QLabel("● SİSTEM AKTİF")
        self.sys_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sys_lbl.setStyleSheet(f"color:{C['ok']};font-size:9px;font-weight:bold;")
        lay.addWidget(self.sys_lbl)

        ver = QLabel("JARVIS v6.0")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver.setStyleSheet(f"color:{C['t3']};font-size:8px;border:1px solid {C['b1']};border-radius:3px;padding:2px;")
        lay.addWidget(ver)

    def _on_card(self, fl):
        for fid, card in self._cards.items():
            card.set_selected(fid == fl["id"])
        self.floor_selected.emit(fl)


# ═══════════════════════════════════════════════════════════════════
# RIGHT PANEL — Bloomberg-style Telemetry
# ═══════════════════════════════════════════════════════════════════
class TelemetryPanel(QWidget):
    def __init__(self, agents, parent=None):
        super().__init__(parent)
        self.agents = agents
        self.setFixedWidth(250)
        self.setStyleSheet(f"background:{C['bg2']};border-left:1px solid {C['b0']};")

        lay = QVBoxLayout(self); lay.setContentsMargins(12,12,12,12); lay.setSpacing(10)

        # Title
        t = QLabel("📊  CANLI TELEMETRİ")
        t.setStyleSheet(f"color:{C['acc']};font-size:9px;font-weight:bold;letter-spacing:2px;border-bottom:1px solid {C['b0']};padding-bottom:7px;")
        lay.addWidget(t)

        # Metric bars
        self._bars = {}
        for lbl, col in [("CPU", "#4f8ef7"),("RAM","#8b5cf6"),("AĞBANT","#22d3a6"),("AI YÜKÜ","#ec4899")]:
            lay.addWidget(self._make_bar_section(lbl, col))

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:{C['b0']};"); lay.addWidget(sep)

        # Selected dept
        lbl = QLabel("SEÇİLİ DEPARTMAN")
        lbl.setStyleSheet(f"color:{C['t3']};font-size:8px;letter-spacing:1px;")
        lay.addWidget(lbl)

        self.dept_name = QLabel("—")
        self.dept_name.setStyleSheet(f"color:{C['warn']};font-size:14px;font-weight:bold;")
        lay.addWidget(self.dept_name)

        self.dept_sub = QLabel("")
        self.dept_sub.setStyleSheet(f"color:{C['t2']};font-size:9px;")
        lay.addWidget(self.dept_sub)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"color:{C['b0']};"); lay.addWidget(sep2)

        # Live log
        ll = QLabel("⚡  SİSTEM LOGU")
        ll.setStyleSheet(f"color:{C['ok']};font-size:8px;font-weight:bold;letter-spacing:1px;")
        lay.addWidget(ll)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setStyleSheet(f"""
            QTextEdit {{ background:{C['bg0']};color:{C['ok']};
                         font-family:'Consolas';font-size:8px;
                         border:1px solid {C['b0']};border-radius:4px; }}
        """)
        lay.addWidget(self.log)

        # Simulated metrics
        self._log_pool = [
            "Ajan mesh senkronize edildi","CEO kanalı aktif",
            "Strateji raporu güncellendi","Finans verisi çekildi",
            "Güvenlik taraması tamamlandı","AI inference hazır",
            "Yeni görev sıraya alındı","Pipeline analizi yapıldı",
        ]
        self._sim_timer = QTimer(self)
        self._sim_timer.timeout.connect(self._simulate)
        self._sim_timer.start(1800)
        self._add_log("⚡ JARVIS v6.0 — QUANTUM COMMAND CENTER başlatıldı")
        self._simulate()

    def _make_bar_section(self, label, color):
        w = QWidget(); w.setStyleSheet("background:transparent;")
        l = QVBoxLayout(w); l.setContentsMargins(0,0,0,0); l.setSpacing(3)

        row = QHBoxLayout()
        lbl = QLabel(label); lbl.setStyleSheet(f"color:{C['t3']};font-size:8px;letter-spacing:1px;")
        row.addWidget(lbl)
        val = QLabel("—"); val.setStyleSheet(f"color:{color};font-size:8px;font-weight:bold;font-family:'Consolas';")
        row.addStretch(); row.addWidget(val)
        l.addLayout(row)

        bar = QProgressBar(); bar.setRange(0,100); bar.setValue(42)
        bar.setFixedHeight(5); bar.setTextVisible(False)
        bar.setStyleSheet(f"""
            QProgressBar {{ background:{C['b0']};border-radius:2px;border:none; }}
            QProgressBar::chunk {{ background:{color};border-radius:2px; }}
        """)
        l.addWidget(bar)
        self._bars[label] = (bar, val, color)
        return w

    def _simulate(self):
        vals = {
            "CPU": random.randint(18, 78),
            "RAM": random.randint(32, 72),
            "AĞBANT": random.randint(8, 55),
            "AI YÜKÜ": random.randint(25, 90),
        }
        for k, (bar, val, col) in self._bars.items():
            v = vals.get(k, 50)
            bar.setValue(v)
            val.setText(f"%{v}")
        msg = random.choice(self._log_pool)
        self._add_log(f"→ {msg}")

    def _add_log(self, text):
        ts = time.strftime("%H:%M:%S")
        self.log.append(f"[{ts}] {text}")
        self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

    def update_department(self, fl):
        hc = health_color(fl["health"])
        self.dept_name.setText(f"{fl['icon']} {fl['name']}")
        self.dept_name.setStyleSheet(f"color:{fl['color']};font-size:14px;font-weight:bold;")
        self.dept_sub.setText(f"{fl['agents']} Ajan  •  Sağlık %{fl['health']}")
        self.dept_sub.setStyleSheet(f"color:{hc};font-size:9px;")
        self._add_log(f"→ {fl['name']} departmanı seçildi")


# ═══════════════════════════════════════════════════════════════════
# CHAT STRIP (bottom)
# ═══════════════════════════════════════════════════════════════════
class ChatStrip(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(46)
        self.setStyleSheet(f"background:{C['bg0']};border-top:1px solid {C['b0']};")
        lay = QHBoxLayout(self); lay.setContentsMargins(12,6,12,6); lay.setSpacing(8)

        hint = QLabel("⌘K")
        hint.setStyleSheet(f"color:{C['t3']};font-size:10px;background:{C['bg2']};border:1px solid {C['b1']};border-radius:4px;padding:2px 7px;")
        lay.addWidget(hint)

        self.inp = QLineEdit()
        self.inp.setPlaceholderText("Karargaha komut ver...")
        self.inp.setStyleSheet(f"""
            QLineEdit {{ background:{C['bg2']};color:{C['t1']};
                         border:1px solid {C['b1']};border-radius:8px;
                         padding:5px 12px;font-size:12px; }}
            QLineEdit:focus {{ border-color:{C['acc']}; }}
        """)
        self.inp.returnPressed.connect(self._send)
        lay.addWidget(self.inp)

        send = QPushButton("▶")
        send.setFixedSize(32,32)
        send.setStyleSheet(f"background:{C['acc']};color:white;border:none;border-radius:8px;font-size:11px;")
        send.clicked.connect(self._send)
        lay.addWidget(send)

    def _send(self):
        txt = self.inp.text().strip()
        if txt:
            self.inp.clear()

    def handle_command(self, cmd):
        pass


# ═══════════════════════════════════════════════════════════════════
# TITLE BAR
# ═══════════════════════════════════════════════════════════════════
class TitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(38); self._drag = None
        self.setStyleSheet(f"background:{C['bg0']};border-bottom:1px solid {C['b0']};")
        lay = QHBoxLayout(self); lay.setContentsMargins(12,0,8,0); lay.setSpacing(8)

        # macOS traffic lights
        for col, fn in [("#ff5f57","close"),("#febc2e","min"),("#28c840","max")]:
            b = QPushButton(); b.setFixedSize(12,12)
            b.setStyleSheet(f"background:{col};border-radius:6px;border:none;")
            b.clicked.connect(getattr(self, f"_do_{fn}"))
            lay.addWidget(b)

        lay.addSpacing(10)

        lbl = QLabel("ZEZELABS  —  QUANTUM COMMAND CENTER  |  JARVIS v6.0")
        lbl.setStyleSheet(f"color:{C['t2']};font-size:10px;letter-spacing:1px;")
        lay.addWidget(lbl)
        lay.addStretch()

        self.clock = QLabel()
        self.clock.setStyleSheet(f"color:{C['ok']};font-size:10px;font-family:'Consolas';")
        lay.addWidget(self.clock)
        t = QTimer(self); t.timeout.connect(self._update_clock); t.start(1000)
        self._update_clock()

    def _update_clock(self): self.clock.setText(f"⏱  {time.strftime('%H:%M:%S')}")
    def _do_close(self): self.window().close()
    def _do_min(self): self.window().showMinimized()
    def _do_max(self):
        self.window().showNormal() if self.window().isMaximized() else self.window().showMaximized()
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag = e.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
    def mouseMoveEvent(self, e):
        if self._drag and e.buttons() == Qt.MouseButton.LeftButton:
            self.window().move(e.globalPosition().toPoint() - self._drag)
    def mouseReleaseEvent(self, e): self._drag = None


# ═══════════════════════════════════════════════════════════════════
# MAIN WINDOW
# ═══════════════════════════════════════════════════════════════════
class QuantumCommandCenter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ZEZELABS — QUANTUM COMMAND CENTER")
        self.resize(1300, 820); self.setMinimumSize(1000, 660)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)

        ico = os.path.join(os.path.dirname(__file__), "brain.ico")
        if os.path.exists(ico): self.setWindowIcon(QIcon(ico))

        self._palette_dlg = CommandPalette(self)
        self._palette_dlg.command_executed.connect(self._on_cmd)

        self._build()
        QShortcut(QKeySequence("Ctrl+K"), self, self._show_palette)
        QShortcut(QKeySequence("Escape"), self, self.showMinimized)
        self._setup_tray(ico)

    def _build(self):
        c = QWidget(); c.setStyleSheet(f"background:{C['bg1']};")
        self.setCentralWidget(c)
        root = QVBoxLayout(c); root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        root.addWidget(TitleBar(self))

        # Main row
        row = QHBoxLayout(); row.setSpacing(0); row.setContentsMargins(0,0,0,0)

        # Sidebar
        self.sidebar = SidebarPanel()
        self.sidebar.floor_selected.connect(self._on_floor)
        row.addWidget(self.sidebar)

        # Center HQ
        self.hq = IsometricHQ()
        self.hq.floor_selected.connect(self._on_floor)
        row.addWidget(self.hq, 1)

        # Right telemetry
        self.telem = TelemetryPanel(self.hq.agents)
        row.addWidget(self.telem)

        root.addLayout(row, 1)

        # Bottom chat strip + status
        root.addWidget(ChatStrip())
        root.addWidget(self._status_bar())

    def _status_bar(self):
        w = QWidget(); w.setFixedHeight(22)
        w.setStyleSheet(f"background:{C['bg0']};border-top:1px solid {C['b0']};")
        l = QHBoxLayout(w); l.setContentsMargins(12,0,12,0); l.setSpacing(16)

        self._agt_lbl = QLabel()
        self._agt_lbl.setStyleSheet(f"color:{C['t3']};font-size:8px;font-family:'Consolas';")
        l.addWidget(self._agt_lbl)

        l.addStretch()
        ver = QLabel("JARVIS v6.0  ·  Quantum Command Center  ·  Senaryo A")
        ver.setStyleSheet(f"color:{C['t3']};font-size:8px;")
        l.addWidget(ver)

        dot = QLabel("●"); dot.setStyleSheet(f"color:{C['ok']};font-size:8px;")
        l.addWidget(dot)

        t = QTimer(self); t.timeout.connect(lambda: self._agt_lbl.setText(
            f"⚡ {sum(1 for a in self.hq.agents if a.status=='AKTİF')}/{len(self.hq.agents)} Ajan Aktif"
        )); t.start(1000)
        self._agt_lbl.setText(f"⚡ {len(self.hq.agents)} Ajan Aktif")
        return w

    def _on_floor(self, fl):
        self.sidebar._on_card(fl)
        self.telem.update_department(fl)

    def _show_palette(self):
        g = self.geometry()
        self._palette_dlg.move(g.x()+(g.width()-self._palette_dlg.width())//2, g.y()+70)
        self._palette_dlg.show(); self._palette_dlg.raise_()
        self._palette_dlg.activateWindow()

    def _on_cmd(self, cmd):
        self.telem._add_log(f"⌘ {cmd}")

    def _setup_tray(self, ico):
        if not QSystemTrayIcon.isSystemTrayAvailable(): return
        icon = QIcon(ico) if os.path.exists(ico) else self.style().standardIcon(
            self.style().StandardPixmap.SP_ComputerIcon)
        self.tray = QSystemTrayIcon(icon, self)
        m = QMenu()
        m.addAction("Göster", self.showNormal)
        m.addAction("⌘K Komut", self._show_palette)
        m.addSeparator(); m.addAction("Çıkış", QApplication.quit)
        self.tray.setContextMenu(m)
        self.tray.setToolTip("ZEZELABS — QUANTUM COMMAND CENTER")
        self.tray.show()
        self.tray.activated.connect(
            lambda r: self.showNormal() if r == QSystemTrayIcon.ActivationReason.DoubleClick else None)


# ═══════════════════════════════════════════════════════════════════
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ZEZELABS QUANTUM COMMAND CENTER")
    app.setApplicationVersion("6.0.0")

    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window,      QColor(C["bg1"]))
    pal.setColor(QPalette.ColorRole.WindowText,  QColor(C["t1"]))
    pal.setColor(QPalette.ColorRole.Base,        QColor(C["bg2"]))
    pal.setColor(QPalette.ColorRole.Text,        QColor(C["t1"]))
    pal.setColor(QPalette.ColorRole.Button,      QColor(C["bg3"]))
    pal.setColor(QPalette.ColorRole.ButtonText,  QColor(C["t1"]))
    pal.setColor(QPalette.ColorRole.Highlight,   QColor(C["acc"]))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(pal)

    win = QuantumCommandCenter()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
