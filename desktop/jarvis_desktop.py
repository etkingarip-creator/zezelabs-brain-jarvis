"""
╔══════════════════════════════════════════════════════════════════╗
║          ZEZELABS SİBER KARARGAH — JARVIS v4.0 HQ               ║
║          Isometric HQ + Neon Agent Orbs + Live Telemetry         ║
╚══════════════════════════════════════════════════════════════════╝
"""
import sys
import os
import math
import random
import time
import threading
import json
import httpx

from PySide6.QtCore import (
    Qt, QTimer, QPoint, QPointF, QRectF, QSizeF, Signal, QObject,
    QPropertyAnimation, QEasingCurve, QThread
)
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QPainterPath,
    QLinearGradient, QRadialGradient, QIcon, QPixmap,
    QFontDatabase, QPalette
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFrame, QLabel, QPushButton, QLineEdit, QScrollArea,
    QSplitter, QProgressBar, QSystemTrayIcon, QMenu, QSizePolicy,
    QGraphicsDropShadowEffect, QTextEdit
)

# ═══════════════════════════════════════════════════════════════
# THEME — ZEZELABS SIBER KARARGAH PALETTE
# ═══════════════════════════════════════════════════════════════
COLORS = {
    "bg_deep":      "#03050f",
    "bg_dark":      "#070d1a",
    "bg_card":      "#0a1628",
    "border":       "#0f2044",
    "border_glow":  "#00f2fe",
    "neon_cyan":    "#00f2fe",
    "neon_pink":    "#ff007f",
    "neon_purple":  "#7928ca",
    "neon_green":   "#00ff9f",
    "neon_gold":    "#ffd700",
    "neon_orange":  "#ff6600",
    "text":         "#e2e8f0",
    "text_dim":     "#4a6080",
    "text_bright":  "#ffffff",
}

DEPARTMENTS = [
    {"id": "ceo",       "name": "CEO",         "floor": 7, "color": "#ffd700", "icon": "👑", "agents": 1},
    {"id": "strategy",  "name": "STRATEJİ",    "floor": 6, "color": "#00f2fe", "icon": "🎯", "agents": 3},
    {"id": "eng",       "name": "MÜHENDİSLİK", "floor": 5, "color": "#7928ca", "icon": "⚙️", "agents": 5},
    {"id": "fin",       "name": "FİNANS",       "floor": 4, "color": "#00ff9f", "icon": "💰", "agents": 3},
    {"id": "marketing", "name": "PAZARLAMA",    "floor": 3, "color": "#ff007f", "icon": "📡", "agents": 4},
    {"id": "sales",     "name": "SATIŞ",        "floor": 2, "color": "#ff6600", "icon": "🚀", "agents": 3},
    {"id": "ops",       "name": "OPERASYON",    "floor": 1, "color": "#00f2fe", "icon": "🔧", "agents": 2},
]

# ═══════════════════════════════════════════════════════════════
# ISOMETRIC HQ CANVAS
# ═══════════════════════════════════════════════════════════════
class IsometricHQWidget(QWidget):
    department_clicked = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(480, 600)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)

        self.hovered_floor = -1
        self.selected_floor = -1
        self.tick = 0.0
        self.agents = []           # list of AnimAgent
        self.floor_pulses = {}     # floor_index → pulse_phase

        self._init_agents()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(30)  # ~33 fps

    def _init_agents(self):
        self.agents = []
        for dept in DEPARTMENTS:
            for i in range(dept["agents"]):
                self.agents.append({
                    "dept": dept,
                    "phase": random.uniform(0, math.tau),
                    "speed": random.uniform(0.02, 0.05),
                    "size": random.uniform(5, 9),
                    "pulse": random.uniform(0, math.tau),
                })
        for i, dept in enumerate(DEPARTMENTS):
            self.floor_pulses[i] = random.uniform(0, math.tau)

    def _tick(self):
        self.tick += 0.04
        for ag in self.agents:
            ag["phase"] += ag["speed"]
            ag["pulse"] += 0.08
        for k in self.floor_pulses:
            self.floor_pulses[k] += 0.03
        self.update()

    # ── Isometric helpers ────────────────────────────────────────
    def _iso_origin(self):
        w, h = self.width(), self.height()
        return QPointF(w / 2, h * 0.18)

    def _to_screen(self, gx, gy, gz, tile_w=54, tile_h=28, floor_h=36):
        ox, oy = self._iso_origin().x(), self._iso_origin().y()
        sx = ox + (gx - gy) * (tile_w / 2)
        sy = oy + (gx + gy) * (tile_h / 2) - gz * floor_h
        return QPointF(sx, sy)

    # ── Draw one isometric floor slab ───────────────────────────
    def _draw_floor(self, painter, floor_idx, dept):
        gz = floor_idx  # z = floor number
        tw, th = 54, 28
        fh = 36
        n_floors = len(DEPARTMENTS)

        color = QColor(dept["color"])
        is_hov = (self.hovered_floor == floor_idx)
        is_sel = (self.selected_floor == floor_idx)
        pulse = abs(math.sin(self.floor_pulses[floor_idx]))

        alpha_top = int(200 + 40 * pulse) if (is_hov or is_sel) else int(140 + 30 * pulse)
        alpha_side = int(120 + 20 * pulse) if (is_hov or is_sel) else int(80 + 15 * pulse)

        # Building block is 3×3 iso tiles wide
        W = 3

        # Top face corners
        top_tl = self._to_screen(0,   0,   gz + 1)
        top_tr = self._to_screen(W,   0,   gz + 1)
        top_br = self._to_screen(W,   W,   gz + 1)
        top_bl = self._to_screen(0,   W,   gz + 1)

        # Bottom face at gz
        bot_tl = self._to_screen(0,   0,   gz)
        bot_tr = self._to_screen(W,   0,   gz)
        bot_br = self._to_screen(W,   W,   gz)
        bot_bl = self._to_screen(0,   W,   gz)

        # ── Left face ──
        left_face = QPainterPath()
        left_face.moveTo(top_tl)
        left_face.lineTo(top_bl)
        left_face.lineTo(bot_bl)
        left_face.lineTo(bot_tl)
        left_face.closeSubpath()
        lc = QColor(dept["color"])
        lc.setAlpha(alpha_side)
        painter.fillPath(left_face, lc)

        # ── Right face ──
        right_face = QPainterPath()
        right_face.moveTo(top_tr)
        right_face.lineTo(top_br)
        right_face.lineTo(bot_br)
        right_face.lineTo(bot_tr)
        right_face.closeSubpath()
        rc = QColor(dept["color"])
        rc.setAlpha(int(alpha_side * 0.6))
        painter.fillPath(right_face, rc)

        # ── Top face ──
        top_face = QPainterPath()
        top_face.moveTo(top_tl)
        top_face.lineTo(top_tr)
        top_face.lineTo(top_br)
        top_face.lineTo(top_bl)
        top_face.closeSubpath()

        grad = QLinearGradient(top_tl, top_br)
        tc = QColor(dept["color"])
        tc.setAlpha(alpha_top)
        tc2 = QColor(dept["color"])
        tc2.setAlpha(int(alpha_top * 0.5))
        grad.setColorAt(0, tc)
        grad.setColorAt(1, tc2)
        painter.fillPath(top_face, grad)

        # ── Glow border ──
        glow_color = QColor(dept["color"])
        glow_color.setAlpha(200 if (is_hov or is_sel) else 100)
        pen = QPen(glow_color, 1.5 if (is_hov or is_sel) else 0.8)
        painter.setPen(pen)
        painter.drawPath(top_face)
        painter.drawPath(left_face)
        painter.drawPath(right_face)

        # ── Department label on top face ──
        center_x = (top_tl.x() + top_tr.x() + top_br.x() + top_bl.x()) / 4
        center_y = (top_tl.y() + top_tr.y() + top_br.y() + top_bl.y()) / 4

        painter.setPen(QColor(COLORS["text_bright"]))
        font = QFont("Segoe UI", 7, QFont.Weight.Bold)
        painter.setFont(font)
        label = f"{dept['icon']} {dept['name']}"
        painter.drawText(QPointF(center_x - 30, center_y + 4), label)

        return top_face  # for hit testing

    # ── Draw neon agent orb on a floor ──────────────────────────
    def _draw_agent(self, painter, ag, floor_idx):
        dept = ag["dept"]
        dept_floor = dept["floor"] - 1  # 0-indexed

        # Orbit center: top face center
        gz = dept_floor + 1
        W = 3
        top_tl = self._to_screen(0, 0, gz)
        top_tr = self._to_screen(W, 0, gz)
        top_br = self._to_screen(W, W, gz)
        top_bl = self._to_screen(0, W, gz)
        cx = (top_tl.x() + top_tr.x() + top_br.x() + top_bl.x()) / 4
        cy = (top_tl.y() + top_tr.y() + top_br.y() + top_bl.y()) / 4

        # Orbit the top of the floor slightly
        r = 22 + ag["size"]
        ox = cx + r * math.cos(ag["phase"])
        oy = cy + r * math.sin(ag["phase"]) * 0.45  # iso squash

        # Pulse glow
        glow_r = ag["size"] + 4 * abs(math.sin(ag["pulse"]))

        color = QColor(dept["color"])

        # Outer glow
        glow = QRadialGradient(ox, oy, glow_r * 2.5)
        gc = QColor(dept["color"])
        gc.setAlpha(60)
        glow.setColorAt(0, gc)
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(glow)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(ox, oy), glow_r * 2.5, glow_r * 2.5)

        # Core orb
        core = QRadialGradient(ox - ag["size"] * 0.3, oy - ag["size"] * 0.3, ag["size"])
        core.setColorAt(0, QColor(255, 255, 255, 220))
        core.setColorAt(0.5, color)
        core.setColorAt(1, QColor(dept["color"]).darker(180))
        painter.setBrush(core)
        painter.drawEllipse(QPointF(ox, oy), ag["size"], ag["size"])

    # ── Main paint ───────────────────────────────────────────────
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        painter.fillRect(self.rect(), QColor(COLORS["bg_deep"]))

        # Grid dots (subtle iso grid)
        painter.setPen(QPen(QColor(COLORS["border"]), 1))
        for gx in range(5):
            for gy in range(5):
                p = self._to_screen(gx, gy, 0)
                painter.drawPoint(p)

        # Draw floors bottom to top
        self._floor_paths = []
        for i, dept in enumerate(DEPARTMENTS):
            path = self._draw_floor(painter, i, dept)
            self._floor_paths.append((i, dept, path))

        # Draw agents on top
        for ag in self.agents:
            dept = ag["dept"]
            floor_idx = dept["floor"] - 1
            self._draw_agent(painter, ag, floor_idx)

        # Scan line overlay
        painter.setOpacity(0.03)
        for y in range(0, self.height(), 3):
            painter.setPen(QPen(QColor(0, 242, 254), 1))
            painter.drawLine(0, y, self.width(), y)
        painter.setOpacity(1.0)

        # HQ title at top
        painter.setPen(QColor(COLORS["neon_cyan"]))
        font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(QRectF(0, 6, self.width(), 20),
                         Qt.AlignmentFlag.AlignHCenter, "🏛️  ZEZELABS SİBER KARARGAH")

        painter.end()

    def mouseMoveEvent(self, event):
        pos = QPointF(event.pos())
        self.hovered_floor = -1
        if hasattr(self, "_floor_paths"):
            for (i, dept, path) in reversed(self._floor_paths):
                if path.contains(pos):
                    self.hovered_floor = i
                    self.setCursor(Qt.CursorShape.PointingHandCursor)
                    break
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
        self.update()

    def mousePressEvent(self, event):
        if hasattr(self, "_floor_paths"):
            pos = QPointF(event.pos())
            for (i, dept, path) in reversed(self._floor_paths):
                if path.contains(pos):
                    self.selected_floor = i
                    self.department_clicked.emit(dept)
                    break
        self.update()


# ═══════════════════════════════════════════════════════════════
# TELEMETRY PANEL (Right side)
# ═══════════════════════════════════════════════════════════════
class TelemetryBar(QWidget):
    def __init__(self, label, color, parent=None):
        super().__init__(parent)
        self.label = label
        self.color = color
        self.value = 0
        self.setFixedHeight(34)
        self._anim_value = 0.0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._anim_tick)
        self.timer.start(30)

    def set_value(self, v):
        self.value = max(0, min(100, v))

    def _anim_tick(self):
        diff = self.value - self._anim_value
        self._anim_value += diff * 0.1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        # Background track
        track = QRectF(0, h // 2 - 4, w, 8)
        painter.setBrush(QColor(COLORS["bg_card"]))
        painter.setPen(QPen(QColor(COLORS["border"]), 1))
        painter.drawRoundedRect(track, 4, 4)

        # Fill
        fill_w = (self._anim_value / 100.0) * w
        if fill_w > 0:
            fill = QRectF(0, h // 2 - 4, fill_w, 8)
            grad = QLinearGradient(0, 0, w, 0)
            c = QColor(self.color)
            c2 = QColor(self.color)
            c2.setAlpha(120)
            grad.setColorAt(0, c2)
            grad.setColorAt(1, c)
            painter.setBrush(grad)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(fill, 4, 4)

        # Label + value
        painter.setPen(QColor(COLORS["text"]))
        painter.setFont(QFont("Segoe UI", 8))
        painter.drawText(QRectF(0, 0, w * 0.7, h // 2 - 4), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.label)
        painter.setPen(QColor(self.color))
        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        painter.drawText(QRectF(0, 0, w, h // 2 - 4), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                         f"{self._anim_value:.0f}%")
        painter.end()


class TelemetryPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(260)
        self.setMaximumWidth(320)
        self.setStyleSheet(f"""
            QWidget {{
                background: {COLORS['bg_dark']};
                color: {COLORS['text']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Title
        title = QLabel("📊  CANLI TELEMETRİ")
        title.setStyleSheet(f"""
            color: {COLORS['neon_cyan']};
            font-family: 'Segoe UI';
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 2px;
            border-bottom: 1px solid {COLORS['border']};
            padding-bottom: 8px;
        """)
        layout.addWidget(title)

        # System bars
        self.bar_cpu    = TelemetryBar("CPU", COLORS["neon_cyan"])
        self.bar_ram    = TelemetryBar("RAM", COLORS["neon_purple"])
        self.bar_net    = TelemetryBar("AĞBANT", COLORS["neon_green"])
        self.bar_ai     = TelemetryBar("AI YÜKÜ", COLORS["neon_pink"])

        for bar in [self.bar_cpu, self.bar_ram, self.bar_net, self.bar_ai]:
            layout.addWidget(bar)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {COLORS['border']};")
        layout.addWidget(sep)

        # Active dept info
        self.dept_title = QLabel("SEÇILI DEPARTMAN")
        self.dept_title.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 9px; letter-spacing: 2px;")
        layout.addWidget(self.dept_title)

        self.dept_name = QLabel("—")
        self.dept_name.setStyleSheet(f"color: {COLORS['neon_gold']}; font-size: 15px; font-weight: bold;")
        layout.addWidget(self.dept_name)

        self.dept_agents = QLabel("")
        self.dept_agents.setStyleSheet(f"color: {COLORS['text']}; font-size: 10px;")
        layout.addWidget(self.dept_agents)

        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"color: {COLORS['border']};")
        layout.addWidget(sep2)

        # Live log
        log_label = QLabel("⚡  SİSTEM LOGU")
        log_label.setStyleSheet(f"color: {COLORS['neon_green']}; font-size: 9px; font-weight: bold; letter-spacing: 2px;")
        layout.addWidget(log_label)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(160)
        self.log_area.setStyleSheet(f"""
            QTextEdit {{
                background: {COLORS['bg_deep']};
                color: {COLORS['neon_green']};
                font-family: 'Consolas', monospace;
                font-size: 9px;
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
            }}
        """)
        layout.addWidget(self.log_area)

        layout.addStretch()

        # Status indicator
        self.status_dot = QLabel("● SİSTEM AKTİF")
        self.status_dot.setStyleSheet(f"color: {COLORS['neon_green']}; font-size: 9px; font-weight: bold;")
        layout.addWidget(self.status_dot)

        # Simulate telemetry
        self._sim_timer = QTimer(self)
        self._sim_timer.timeout.connect(self._simulate)
        self._sim_timer.start(1500)
        self._simulate()

        self._log_msgs = [
            "JARVIS çekirdek başlatıldı",
            "Departman bağlantıları aktif",
            "Ajan mesh ağı senkronize",
            "CEO kanalı dinleniyor",
            "Strateji modülü hazır",
            "Finans verisi güncellendi",
            "Pazarlama ajanı rapor gönderdi",
            "Satış pipeline analizi tamamlandı",
            "Güvenlik taraması geçildi",
            "AI inference motoru hazır",
            "WebSocket bağlantısı stabil",
            "Bellek optimizasyonu yapıldı",
        ]
        self._add_log("⚡ ZEZELABS JARVIS v4.0 başlatıldı")

    def _simulate(self):
        self.bar_cpu.set_value(random.uniform(15, 85))
        self.bar_ram.set_value(random.uniform(30, 75))
        self.bar_net.set_value(random.uniform(5, 60))
        self.bar_ai.set_value(random.uniform(20, 95))
        msg = random.choice(self._log_msgs)
        self._add_log(f"→ {msg}")

    def _add_log(self, text):
        ts = time.strftime("%H:%M:%S")
        self.log_area.append(f"[{ts}] {text}")
        sb = self.log_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    def update_department(self, dept):
        self.dept_name.setText(f"{dept['icon']} {dept['name']}")
        color = dept["color"]
        self.dept_name.setStyleSheet(f"color: {color}; font-size: 15px; font-weight: bold;")
        agents = dept["agents"]
        self.dept_agents.setText(f"{agents} Aktif Ajan  |  Kat {dept['floor']}")
        self._add_log(f"→ {dept['name']} departmanı seçildi")


# ═══════════════════════════════════════════════════════════════
# CHAT PANEL (Bottom)
# ═══════════════════════════════════════════════════════════════
class ChatBubble(QFrame):
    def __init__(self, text, is_user=False, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.setFrameShape(QFrame.Shape.NoFrame)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)

        label = QLabel(text)
        label.setWordWrap(True)
        label.setMaximumWidth(400)
        if is_user:
            label.setStyleSheet(f"""
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {COLORS['neon_purple']}, stop:1 {COLORS['neon_pink']});
                color: white;
                border-radius: 12px;
                padding: 8px 14px;
                font-family: 'Segoe UI';
                font-size: 10px;
            """)
            layout.addStretch()
            layout.addWidget(label)
        else:
            label.setStyleSheet(f"""
                background: {COLORS['bg_card']};
                color: {COLORS['neon_cyan']};
                border: 1px solid {COLORS['border_glow']};
                border-radius: 12px;
                padding: 8px 14px;
                font-family: 'Consolas', monospace;
                font-size: 10px;
            """)
            layout.addWidget(label)
            layout.addStretch()


class ChatPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximumHeight(220)
        self.setStyleSheet(f"""
            background: {COLORS['bg_dark']};
            border-top: 1px solid {COLORS['border']};
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 8)
        layout.setSpacing(4)

        # Chat title
        title = QLabel("💬  JARVIS İLE KONUŞ")
        title.setStyleSheet(f"""
            color: {COLORS['neon_pink']};
            font-family: 'Segoe UI';
            font-size: 10px;
            font-weight: bold;
            letter-spacing: 2px;
        """)
        layout.addWidget(title)

        # Scroll area for bubbles
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                background: {COLORS['bg_deep']};
                width: 4px;
                border-radius: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {COLORS['border']};
                border-radius: 2px;
            }}
        """)

        self.bubble_container = QWidget()
        self.bubble_container.setStyleSheet("background: transparent;")
        self.bubble_layout = QVBoxLayout(self.bubble_container)
        self.bubble_layout.setSpacing(4)
        self.bubble_layout.addStretch()
        self.scroll.setWidget(self.bubble_container)
        layout.addWidget(self.scroll)

        # Input bar
        input_row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Karargaha komut ver...")
        self.input.setStyleSheet(f"""
            QLineEdit {{
                background: {COLORS['bg_deep']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 6px 12px;
                font-family: 'Segoe UI';
                font-size: 10px;
            }}
            QLineEdit:focus {{
                border-color: {COLORS['neon_cyan']};
            }}
        """)
        self.input.returnPressed.connect(self._send)
        input_row.addWidget(self.input)

        send_btn = QPushButton("▶")
        send_btn.setFixedSize(36, 36)
        send_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 {COLORS['neon_cyan']}, stop:1 {COLORS['neon_purple']});
                color: {COLORS['bg_deep']};
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {COLORS['neon_pink']};
            }}
        """)
        send_btn.clicked.connect(self._send)
        input_row.addWidget(send_btn)
        layout.addLayout(input_row)

        # Welcome message
        self._add_bubble("🏛️ ZEZELABS SİBER KARARGAH aktif. Departman seçin veya komut verin.", is_user=False)

    def _add_bubble(self, text, is_user):
        bubble = ChatBubble(text, is_user)
        self.bubble_layout.insertWidget(self.bubble_layout.count() - 1, bubble)
        QTimer.singleShot(50, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()))

    def _send(self):
        text = self.input.text().strip()
        if not text:
            return
        self._add_bubble(text, is_user=True)
        self.input.clear()
        # Simulate JARVIS reply
        QTimer.singleShot(600, lambda: self._jarvis_reply(text))

    def _jarvis_reply(self, user_text):
        replies = [
            f"Anlıyorum: '{user_text}' — İşleniyor...",
            "Tüm departmanlar hazır efendim.",
            "Operasyon başlatıldı. Sonuç 3 dakika içinde.",
            "Strateji modülü analiz ediyor...",
            "CEO kanalına iletildi. Onay bekleniyor.",
            "Veri akışı optimize edildi.",
            "Ajan mesh ağı senkronize. Görev dağıtıldı.",
        ]
        reply = random.choice(replies)
        self._add_bubble(f"⚡ {reply}", is_user=False)


# ═══════════════════════════════════════════════════════════════
# SIDEBAR — Department List
# ═══════════════════════════════════════════════════════════════
class DeptButton(QPushButton):
    def __init__(self, dept, parent=None):
        super().__init__(parent)
        self.dept = dept
        self.setText(f"  {dept['icon']}  {dept['name']}")
        self.setFixedHeight(38)
        self.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_card']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-left: 3px solid {dept['color']};
                border-radius: 6px;
                text-align: left;
                padding-left: 8px;
                font-family: 'Segoe UI';
                font-size: 10px;
            }}
            QPushButton:hover {{
                background: {COLORS['bg_dark']};
                border-left-color: {dept['color']};
                color: {dept['color']};
            }}
        """)


class SidebarPanel(QWidget):
    department_selected = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(180)
        self.setStyleSheet(f"""
            background: {COLORS['bg_dark']};
            border-right: 1px solid {COLORS['border']};
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(5)

        # Logo area
        logo = QLabel("Z")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setFixedHeight(48)
        logo.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 {COLORS['neon_cyan']}, stop:1 {COLORS['neon_purple']});
            color: {COLORS['bg_deep']};
            font-family: 'Segoe UI Black';
            font-size: 24px;
            font-weight: 900;
            border-radius: 12px;
        """)
        layout.addWidget(logo)

        title = QLabel("ZEZELABS")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"""
            color: {COLORS['neon_cyan']};
            font-size: 9px;
            font-weight: bold;
            letter-spacing: 3px;
        """)
        layout.addWidget(title)

        sub = QLabel("SİBER KARARGAH")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 8px; letter-spacing: 2px;")
        layout.addWidget(sub)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {COLORS['border']}; margin: 4px 0;")
        layout.addWidget(sep)

        dept_label = QLabel("DEPARTMANLAR")
        dept_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 8px; letter-spacing: 2px; padding-left: 4px;")
        layout.addWidget(dept_label)

        for dept in DEPARTMENTS:
            btn = DeptButton(dept)
            btn.clicked.connect(lambda checked=False, d=dept: self.department_selected.emit(d))
            layout.addWidget(btn)

        layout.addStretch()

        # Version badge
        ver = QLabel("JARVIS v4.0")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver.setStyleSheet(f"""
            color: {COLORS['neon_purple']};
            font-size: 8px;
            font-weight: bold;
            letter-spacing: 1px;
            border: 1px solid {COLORS['neon_purple']};
            border-radius: 4px;
            padding: 3px 8px;
        """)
        layout.addWidget(ver)


# ═══════════════════════════════════════════════════════════════
# TITLE BAR (custom frameless)
# ═══════════════════════════════════════════════════════════════
class TitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(42)
        self._drag_pos = None
        self.setStyleSheet(f"""
            background: {COLORS['bg_deep']};
            border-bottom: 1px solid {COLORS['border']};
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 8, 0)

        # Icon + title
        icon_lbl = QLabel("🏛️")
        icon_lbl.setStyleSheet("font-size: 14px;")
        layout.addWidget(icon_lbl)

        title = QLabel("ZEZELABS SİBER KARARGAH")
        title.setStyleSheet(f"""
            color: {COLORS['neon_cyan']};
            font-family: 'Segoe UI';
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 2px;
        """)
        layout.addWidget(title)
        layout.addStretch()

        # Clock
        self.clock = QLabel()
        self.clock.setStyleSheet(f"color: {COLORS['neon_green']}; font-size: 10px; font-family: 'Consolas';")
        layout.addWidget(self.clock)
        self._update_clock()
        clk_timer = QTimer(self)
        clk_timer.timeout.connect(self._update_clock)
        clk_timer.start(1000)

        layout.addSpacing(10)

        # Window buttons
        for sym, cb, col in [("—", self._minimize, COLORS["neon_green"]),
                              ("⬜", self._maximize, COLORS["neon_gold"]),
                              ("✕", self._close,    COLORS["neon_pink"])]:
            btn = QPushButton(sym)
            btn.setFixedSize(28, 28)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {COLORS['text_dim']};
                    border: none;
                    font-size: 12px;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    background: {col};
                    color: {COLORS['bg_deep']};
                }}
            """)
            btn.clicked.connect(cb)
            layout.addWidget(btn)

    def _update_clock(self):
        self.clock.setText(time.strftime("⏱  %H:%M:%S"))

    def _minimize(self):
        self.window().showMinimized()

    def _maximize(self):
        if self.window().isMaximized():
            self.window().showNormal()
        else:
            self.window().showMaximized()

    def _close(self):
        self.window().close()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


# ═══════════════════════════════════════════════════════════════
# MAIN WINDOW
# ═══════════════════════════════════════════════════════════════
class ZezeHQWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ZEZELABS SİBER KARARGAH — JARVIS v4.0")
        self.setMinimumSize(1050, 720)
        self.resize(1200, 780)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        # Icon
        ico_path = os.path.join(os.path.dirname(__file__), "brain.ico")
        if os.path.exists(ico_path):
            self.setWindowIcon(QIcon(ico_path))

        # System tray
        self._setup_tray(ico_path)

        # Central widget
        central = QWidget()
        central.setStyleSheet(f"background: {COLORS['bg_deep']};")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Title bar
        self.title_bar = TitleBar()
        root.addWidget(self.title_bar)

        # Main content row
        content_row = QHBoxLayout()
        content_row.setSpacing(0)
        content_row.setContentsMargins(0, 0, 0, 0)

        # Sidebar
        self.sidebar = SidebarPanel()
        self.sidebar.department_selected.connect(self._on_department)
        content_row.addWidget(self.sidebar)

        # Center: HQ + Chat stacked
        center_col = QVBoxLayout()
        center_col.setSpacing(0)
        center_col.setContentsMargins(0, 0, 0, 0)

        self.hq = IsometricHQWidget()
        self.hq.department_clicked.connect(self._on_department)
        center_col.addWidget(self.hq, stretch=1)

        self.chat = ChatPanel()
        center_col.addWidget(self.chat)

        content_row.addLayout(center_col, stretch=1)

        # Telemetry
        self.telemetry = TelemetryPanel()
        content_row.addWidget(self.telemetry)

        root.addLayout(content_row)

    def _setup_tray(self, ico_path):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        icon = QIcon(ico_path) if os.path.exists(ico_path) else QIcon()
        self.tray = QSystemTrayIcon(icon, self)
        menu = QMenu()
        menu.addAction("Göster", self.showNormal)
        menu.addAction("Çıkış", QApplication.quit)
        self.tray.setContextMenu(menu)
        self.tray.setToolTip("ZEZELABS SİBER KARARGAH")
        self.tray.show()
        self.tray.activated.connect(self._tray_activated)

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.showNormal()
            self.activateWindow()

    def _on_department(self, dept):
        self.telemetry.update_department(dept)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.showMinimized()


# ═══════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ZEZELABS SİBER KARARGAH")
    app.setApplicationVersion("4.0.0")

    # Dark palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,          QColor(COLORS["bg_deep"]))
    palette.setColor(QPalette.ColorRole.WindowText,      QColor(COLORS["text"]))
    palette.setColor(QPalette.ColorRole.Base,            QColor(COLORS["bg_dark"]))
    palette.setColor(QPalette.ColorRole.AlternateBase,   QColor(COLORS["bg_card"]))
    palette.setColor(QPalette.ColorRole.Text,            QColor(COLORS["text"]))
    palette.setColor(QPalette.ColorRole.Button,          QColor(COLORS["bg_card"]))
    palette.setColor(QPalette.ColorRole.ButtonText,      QColor(COLORS["text"]))
    palette.setColor(QPalette.ColorRole.Highlight,       QColor(COLORS["neon_cyan"]))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(COLORS["bg_deep"]))
    app.setPalette(palette)

    window = ZezeHQWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
