import sys
import os
import math
import random
import json
import webbrowser
import threading
import asyncio
from datetime import datetime, timezone
import httpx

from PySide6.QtCore import Qt, QPoint, QTimer, QSize, QUrl
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath, QLinearGradient, QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QFrame, QLabel, QPushButton, QLineEdit, QListWidget, QListWidgetItem,
    QScrollArea, QSplitter, QProgressBar, QMessageBox
)

# Core theme variables
THEME = {
    "background": "rgba(7, 13, 25, 0.95)",
    "surface": "rgba(13, 21, 39, 0.85)",
    "border": "#1c2842",
    "primary": "#38bdf8",  # Neon Turquoise/Cyan
    "accent": "#ec4899",   # Neon Pink/Magenta
    "success": "#10b981",  # Emerald Green
    "warning": "#f59e0b",
    "error": "#ef4444",
    "text": "#f8fafc",
    "text_muted": "#64748b"
}

class ToolTip(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet(f"""
            background-color: #0d1527;
            color: #38bdf8;
            border: 1px solid #1c2842;
            border-radius: 4px;
            font-family: 'Segoe UI';
            font-size: 11px;
            font-weight: bold;
            padding: 6px 10px;
        """)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

class PremiumButton(QPushButton):
    def __init__(self, text, parent=None, is_primary=False):
        super().__init__(text, parent)
        self.is_primary = is_primary
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.setFixedHeight(36)
        self.setup_style()
        
    def setup_style(self):
        if self.is_primary:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {THEME["primary"]};
                    color: #070d19;
                    border: 1px solid {THEME["primary"]};
                    border-radius: 8px;
                    padding: 0 16px;
                }}
                QPushButton:hover {{
                    background-color: {THEME["accent"]};
                    color: #ffffff;
                    border-color: {THEME["accent"]};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {THEME["surface"]};
                    color: {THEME["text"]};
                    border: 1px solid {THEME["border"]};
                    border-radius: 8px;
                    padding: 0 16px;
                }}
                QPushButton:hover {{
                    background-color: {THEME["primary"]};
                    color: #070d19;
                    border-color: {THEME["primary"]};
                }}
            """)

class NeuralNetWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.nodes = []
        self.connections = []
        self.particles = []
        self.hovered_node = None
        self.mouse_pos = QPoint(-100, -100)
        self.chart_step = 0
        self.glow_phase = 0.0
        self.setMouseTracking(True)
        
        self.setup_neural_network()
        
        # Anim timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(33)
        
    def setup_neural_network(self):
        layers = [3, 4, 4]
        spacing_x = 110
        start_x = 40
        
        for l_idx, count in enumerate(layers):
            layer_nodes = []
            spacing_y = 190 / (count + 1)
            x = start_x + l_idx * spacing_x
            
            for n_idx in range(count):
                y = spacing_y * (n_idx + 1) + 20
                node_data = {
                    "x": float(x), "y": float(y), "base_x": float(x), "base_y": float(y),
                    "layer": l_idx, "index": n_idx, "base_r": 6.0,
                    "pulse_phase": random.uniform(0, math.pi * 2),
                    "role": f"Agent_{l_idx}_{n_idx}",
                    "status": "AKTİF" if random.choice([True, True, False]) else "BOŞTA",
                    "throughput": f"{random.randint(80, 99)}%"
                }
                self.nodes.append(node_data)
                
        # Synapses (connections)
        for i in range(len(layers) - 1):
            curr_nodes = [n for n in self.nodes if n["layer"] == i]
            next_nodes = [n for n in self.nodes if n["layer"] == i + 1]
            for cn in curr_nodes:
                for nn in next_nodes:
                    self.connections.append({"start": cn, "end": nn})

    def mouseMoveEvent(self, event):
        self.mouse_pos = event.position().toPoint()
        nearest = None
        min_dist = 16.0
        
        for node in self.nodes:
            dist = math.hypot(node["x"] - self.mouse_pos.x(), node["y"] - self.mouse_pos.y())
            if dist < min_dist:
                min_dist = dist
                nearest = node
        self.hovered_node = nearest
        
    def leaveEvent(self, event):
        self.mouse_pos = QPoint(-100, -100)
        self.hovered_node = None

    def update_animation(self):
        self.chart_step += 1
        self.glow_phase += 0.15
        
        # Warp nodes elastically towards mouse
        for node in self.nodes:
            dx = self.mouse_pos.x() - node["base_x"]
            dy = self.mouse_pos.y() - node["base_y"]
            dist = math.hypot(dx, dy)
            if dist < 90:
                factor = (90 - dist) / 90
                tx = node["base_x"] + dx * factor * 0.25
                ty = node["base_y"] + dy * factor * 0.25
            else:
                tx = node["base_x"]
                ty = node["base_y"]
            node["x"] += (tx - node["x"]) * 0.15
            node["y"] += (ty - node["y"]) * 0.15
            node["pulse_phase"] += 0.05
            
        # Particle flows
        if self.chart_step % 8 == 0 and self.connections:
            conn = random.choice(self.connections)
            self.particles.append({
                "start": conn["start"], "end": conn["end"], "progress": 0.0,
                "color": THEME["primary"] if random.choice([True, False]) else THEME["accent"]
            })
            
        active_p = []
        for p in self.particles:
            p["progress"] += 0.045
            if p["progress"] < 1.0:
                active_p.append(p)
        self.particles = active_p
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw Synapses (Perfect antialiased lines)
        pen = QPen(QColor(THEME["border"]))
        pen.setWidth(1)
        painter.setPen(pen)
        for conn in self.connections:
            painter.drawLine(int(conn["start"]["x"]), int(conn["start"]["y"]), int(conn["end"]["x"]), int(conn["end"]["y"]))
            
        # Draw Signal Particles
        for p in self.particles:
            x = p["start"]["x"] + (p["end"]["x"] - p["start"]["x"]) * p["progress"]
            y = p["start"]["y"] + (p["end"]["y"] - p["start"]["y"]) * p["progress"]
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(p["color"])))
            painter.drawEllipse(QPoint(int(x), int(y)), 3, 3)
            
        # Draw Nodes
        for node in self.nodes:
            offset = math.sin(node["pulse_phase"]) * 1.5
            r = node["base_r"] + offset
            
            # Inner circle fill
            painter.setPen(QPen(QColor(THEME["primary"]), 2))
            painter.setBrush(QBrush(QColor("#070d19")))
            painter.drawEllipse(QPoint(int(node["x"]), int(node["y"])), int(r), int(r))
            
        # Draw Hover Glow circles
        if self.hovered_node:
            hx = int(self.hovered_node["x"])
            hy = int(self.hovered_node["y"])
            hr = self.hovered_node["base_r"]
            
            glow1 = hr * 1.5 + math.sin(self.glow_phase) * 3
            glow2 = hr * 3.0 + math.cos(self.glow_phase) * 5
            
            # Outer Ring (Pink glow)
            painter.setPen(QPen(QColor(THEME["accent"]), 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPoint(hx, hy), int(glow2), int(glow2))
            
            # Inner Ring (Turquoise glow)
            painter.setPen(QPen(QColor(THEME["primary"]), 2))
            painter.drawEllipse(QPoint(hx, hy), int(glow1), int(glow1))
            
        # Draw dynamic telemetry text block directly on canvas (HUD style)
        painter.setPen(QColor(THEME["primary"]))
        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        latency = random.randint(24, 38)
        throughput = random.uniform(97.8, 99.4)
        painter.drawText(self.rect().width() - 110, 25, f"AĞ VERİMİ: %{throughput:.1f}\nGECİKME: {latency}ms")

class VoiceWaveWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.wave_phase = 0.0
        self.active = False
        self.last_amplitude = 0.0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_wave)
        self.timer.start(33)
        
    def update_wave(self):
        self.wave_phase += 0.12
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.rect().width()
        height = self.rect().height()
        mid_y = height / 2
        
        max_amp = 32.0 if self.active else 3.0
        
        # Paths setup for 3 overlapping curves
        path_cyan = QPainterPath()
        path_pink = QPainterPath()
        path_gold = QPainterPath()
        
        path_cyan.moveTo(0, mid_y)
        path_pink.moveTo(0, mid_y)
        path_gold.moveTo(0, mid_y)
        
        for x in range(0, width + 4, 4):
            rad = (x / width) * math.pi * 3
            envelope = math.sin((x / width) * math.pi)
            
            y_c = mid_y + max_amp * envelope * (math.sin(rad + self.wave_phase) + 0.35 * math.sin(2.3 * rad - 1.5 * self.wave_phase))
            y_m = mid_y + (max_amp * 0.7) * envelope * (math.sin(rad * 1.5 - self.wave_phase * 1.2) + 0.35 * math.sin(3.1 * rad + self.wave_phase))
            y_g = mid_y + (max_amp * 0.45) * envelope * (math.sin(rad * 0.8 + self.wave_phase * 0.7) + 0.25 * math.sin(1.7 * rad - self.wave_phase))
            
            path_cyan.lineTo(x, y_c)
            path_pink.lineTo(x, y_m)
            path_gold.lineTo(x, y_g)
            
        # Draw Gold Wave
        painter.setPen(QPen(QColor(THEME["warning"]), 1))
        painter.drawPath(path_gold)
        
        # Draw Pink Wave
        painter.setPen(QPen(QColor(THEME["accent"]), 1))
        painter.drawPath(path_pink)
        
        # Draw Cyan Wave (Sharp primary)
        painter.setPen(QPen(QColor(THEME["primary"]), 2))
        painter.drawPath(path_cyan)

class FinancialChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.step = 0
        self.mouse_pos = QPoint(-100, -100)
        self.setMouseTracking(True)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_chart)
        self.timer.start(50)
        
    def update_chart(self):
        self.step += 1
        self.update()
        
    def mouseMoveEvent(self, event):
        self.mouse_pos = event.position().toPoint()
        
    def leaveEvent(self, event):
        self.mouse_pos = QPoint(-100, -100)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.rect().width()
        height = self.rect().height()
        
        pad_x, pad_y = 10, 10
        gw = width - pad_x * 2
        gh = height - pad_y * 2
        
        seed_points = [0.15, 0.35, 0.20, 0.45, 0.30, 0.60, 0.50, 0.75, 0.65, 0.85]
        
        coords = []
        for i, val in enumerate(seed_points):
            x = pad_x + (i / (len(seed_points) - 1)) * gw
            wiggle = math.sin(self.step * 0.15 + i) * 0.03
            y = height - pad_y - (val + wiggle) * gh
            coords.append(QPoint(int(x), int(y)))
            
        # Draw translucent area polygon fill
        area_path = QPainterPath()
        area_path.moveTo(pad_x, height - pad_y)
        for pt in coords:
            area_path.lineTo(pt)
        area_path.lineTo(width - pad_x, height - pad_y)
        area_path.closeSubpath()
        
        gradient = QLinearGradient(0, pad_y, 0, height - pad_y)
        gradient.setColorAt(0.0, QColor(24, 185, 129, 90)) # Translucent Success green
        gradient.setColorAt(1.0, QColor(15, 41, 59, 20))
        painter.fillPath(area_path, QBrush(gradient))
        
        # Draw sharp success line
        path_line = QPainterPath()
        path_line.moveTo(coords[0])
        for pt in coords[1:]:
            path_line.lineTo(pt)
        painter.setPen(QPen(QColor(THEME["success"]), 2))
        painter.drawPath(path_line)
        
        # Draw glowing endpoint
        end_pt = coords[-1]
        pulse_r = 4.0 + 2.0 * math.sin(self.step * 0.2)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(THEME["success"])))
        painter.drawEllipse(end_pt, int(pulse_r), int(pulse_r))
        
        # Coordinates Hover check
        if self.mouse_pos.x() > 0:
            nearest_idx = 0
            min_dist = 99999.0
            for idx, pt in enumerate(coords):
                dist = abs(pt.x() - self.mouse_pos.x())
                if dist < min_dist:
                    min_dist = dist
                    nearest_idx = idx
                    
            if min_dist < 30:
                px = coords[nearest_idx].x()
                py = coords[nearest_idx].y()
                
                # Guidelines
                painter.setPen(QPen(QColor(THEME["border"]), 1, Qt.PenStyle.DashLine))
                painter.drawLine(px, pad_y, px, height - pad_y)
                
                # Glowing node highlighter
                painter.setPen(QPen(QColor(THEME["success"]), 2))
                painter.setBrush(QBrush(QColor("#0d1527")))
                painter.drawEllipse(QPoint(px, py), 5, 5)
                
                # Info overlay
                val = seed_points[nearest_idx]
                info_txt = f"Zaman: T-{9-nearest_idx}\nROI: %{val*100:.1f}"
                bx = px + 10
                by = py - 40
                if bx + 95 > width: bx = px - 105
                if by < 2: by = py + 10
                
                painter.setPen(QPen(QColor(THEME["success"]), 1))
                painter.setBrush(QBrush(QColor("#0d1527")))
                painter.drawRect(bx, by, 95, 36)
                painter.setPen(QColor(THEME["text"]))
                painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
                painter.drawText(bx + 8, by + 16, f"T-{9-nearest_idx}")
                painter.drawText(bx + 8, by + 28, f"ROI: %{val*100:.0f}")

class ChatBubbleItem(QWidget):
    def __init__(self, sender, text, parent=None):
        super().__init__(parent)
        self.sender = sender
        self.text = text
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        
        header_row = QHBoxLayout()
        header_lbl = QLabel(self)
        header_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        
        bubble_row = QHBoxLayout()
        self.bubble_lbl = QLabel(self.text, self)
        self.bubble_lbl.setWordWrap(True)
        self.bubble_lbl.setFont(QFont("Segoe UI", 9))
        self.bubble_lbl.setContentsMargins(15, 12, 15, 12)
        
        if self.sender == "user":
            header_lbl.setText("👤 KULLANICI  ⚡")
            header_lbl.setStyleSheet(f"color: {THEME['text_muted']};")
            header_row.addStretch()
            header_row.addWidget(header_lbl)
            
            # Premium Neon Pink bubble
            self.bubble_lbl.setStyleSheet(f"""
                background-color: {THEME['accent']};
                color: #ffffff;
                border-radius: 12px;
                font-weight: bold;
            """)
            bubble_row.addStretch()
            bubble_row.addWidget(self.bubble_lbl)
            # Give bubble max width constraints
            self.bubble_lbl.setMaximumWidth(450)
        elif self.sender == "jarvis":
            header_lbl.setText("⚡ JARVIS")
            header_lbl.setStyleSheet(f"color: {THEME['primary']};")
            header_row.addWidget(header_lbl)
            header_row.addStretch()
            
            # Premium Glassmorphic slate bubble
            self.bubble_lbl.setStyleSheet(f"""
                background-color: {THEME['surface']};
                color: {THEME['text']};
                border: 1px solid {THEME['border']};
                border-radius: 12px;
            """)
            bubble_row.addWidget(self.bubble_lbl)
            bubble_row.addStretch()
            self.bubble_lbl.setMaximumWidth(450)
        else: # system
            header_lbl.setText("⚠️ SİSTEM UYARISI")
            header_lbl.setStyleSheet(f"color: {THEME['warning']};")
            header_row.addStretch()
            header_row.addWidget(header_lbl)
            header_row.addStretch()
            
            self.bubble_lbl.setStyleSheet(f"""
                background-color: #070d19;
                color: {THEME['warning']};
                border: 1px solid {THEME['border']};
                border-radius: 8px;
            """)
            bubble_row.addStretch()
            bubble_row.addWidget(self.bubble_lbl)
            bubble_row.addStretch()
            
        layout.addLayout(header_row)
        layout.addLayout(bubble_row)

class PremiumCard(QFrame):
    def __init__(self, title, desc, parent=None, command=None):
        super().__init__(parent)
        self.title = title
        self.desc = desc
        self.command = command
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setup_ui()
        
    def setup_ui(self):
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Plain)
        self.setLineWidth(1)
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME["surface"]};
                border: 1px solid {THEME["border"]};
                border-radius: 10px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        
        self.title_lbl = QLabel(self.title, self)
        self.title_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.title_lbl.setStyleSheet(f"color: {THEME['text']}; border: none; background: transparent;")
        layout.addWidget(self.title_lbl)
        
        self.desc_lbl = QLabel(self.desc, self)
        self.desc_lbl.setWordWrap(True)
        self.desc_lbl.setFont(QFont("Segoe UI", 8))
        self.desc_lbl.setStyleSheet(f"color: {THEME['text_muted']}; border: none; background: transparent;")
        layout.addWidget(self.desc_lbl)
        
    def enterEvent(self, event):
        # Premium Neon accent color transition on hover
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #1c0d24;
                border: 1px solid {THEME["accent"]};
                border-radius: 10px;
            }}
        """)
        self.title_lbl.setStyleSheet(f"color: {THEME['accent']}; border: none; background: transparent;")
        
    def leaveEvent(self, event):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME["surface"]};
                border: 1px solid {THEME["border"]};
                border-radius: 10px;
            }}
        """)
        self.title_lbl.setStyleSheet(f"color: {THEME['text']}; border: none; background: transparent;")
        
    def mousePressEvent(self, event):
        if self.command:
            self.command()

class JarvisPySideMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.theme = THEME
        self.drag_start = QPoint()
        
        self.setWindowTitle("⚡ ZEZELABS HOLDING | JARVIS | v3.0-QtPrototype")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.resize(1150, 760)
        self.setStyleSheet(f"background-color: {self.theme['background']};")
        
        self.setup_ui()
        
    def setup_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- TITLE BAR ---
        title_bar = QFrame(self)
        title_bar.setFixedHeight(48)
        title_bar.setStyleSheet(f"background-color: {self.theme['surface']}; border-bottom: 1px solid {self.theme['border']};")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(20, 0, 20, 0)
        
        title_lbl = QLabel("⚡ ZEZELABS HOLDING  |  JARVIS  |  v3.0-QtPrototype (PySide6)", title_bar)
        title_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {self.theme['primary']}; border: none;")
        title_layout.addWidget(title_lbl)
        title_layout.addStretch()
        
        close_btn = QPushButton("✕", title_bar)
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.theme['text_muted']};
                border: none;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.theme['error']};
                color: #ffffff;
                border-radius: 4px;
            }}
        """)
        close_btn.clicked.connect(self.close)
        title_layout.addWidget(close_btn)
        main_layout.addWidget(title_bar)
        
        # Connect dragging slots
        title_bar.mousePressEvent = self.title_press_event
        title_bar.mouseMoveEvent = self.title_move_event
        
        # --- SHELL LAYOUT ---
        shell_splitter = QSplitter(Qt.Orientation.Horizontal, self)
        shell_splitter.setHandleWidth(1)
        shell_splitter.setStyleSheet(f"QSplitter::handle {{ background-color: {self.theme['border']}; }}")
        
        # Left strip menu
        left_strip = QFrame(shell_splitter)
        left_strip.setFixedWidth(60)
        left_strip.setStyleSheet(f"background-color: {self.theme['surface']};")
        left_layout = QVBoxLayout(left_strip)
        left_layout.setContentsMargins(0, 15, 0, 15)
        left_layout.setSpacing(15)
        
        icons = ["🏠", "💬", "📈", "📁", "⚙️"]
        for ico in icons:
            btn = QPushButton(ico, left_strip)
            btn.setFixedSize(60, 50)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self.theme['text_muted']};
                    border: none;
                    font-size: 18px;
                }}
                QPushButton:hover {{
                    background-color: {self.theme['border']};
                    color: {self.theme['primary']};
                }}
            """)
            left_layout.addWidget(btn)
        left_layout.addStretch()
        shell_splitter.addWidget(left_strip)
        
        # Main Dashboard Panel
        dashboard_panel = QFrame(shell_splitter)
        dashboard_layout = QHBoxLayout(dashboard_panel)
        dashboard_layout.setContentsMargins(20, 20, 20, 20)
        dashboard_layout.setSpacing(15)
        
        # 1. Left Section (Sinir Ağı & Audio Spectrum)
        left_view = QFrame(dashboard_panel)
        left_view.setStyleSheet("border: none; background: transparent;")
        left_view_layout = QVBoxLayout(left_view)
        left_view_layout.setContentsMargins(0, 0, 0, 0)
        left_view_layout.setSpacing(15)
        
        # Sinir Ağı Frame
        net_frame = QFrame(left_view)
        net_frame.setStyleSheet(f"background-color: {self.theme['surface']}; border: 1px solid {self.theme['border']}; border-radius: 12px;")
        net_layout = QVBoxLayout(net_frame)
        net_layout.setContentsMargins(15, 12, 15, 12)
        
        net_hdr = QLabel("⚛️ SINIR AĞI (ANTIALIASED CANVAS)", net_frame)
        net_hdr.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        net_hdr.setStyleSheet(f"color: {self.theme['primary']}; border: none; background: transparent;")
        net_layout.addWidget(net_hdr)
        
        self.net_canvas = NeuralNetWidget(net_frame)
        net_layout.addWidget(self.net_canvas)
        left_view_layout.addWidget(net_frame, 3)
        
        # Audio Wave Frame
        wave_frame = QFrame(left_view)
        wave_frame.setFixedHeight(160)
        wave_frame.setStyleSheet(f"background-color: {self.theme['surface']}; border: 1px solid {self.theme['border']}; border-radius: 12px;")
        wave_layout = QVBoxLayout(wave_frame)
        wave_layout.setContentsMargins(15, 12, 15, 12)
        
        wave_hdr = QLabel("🎤 SES SPEKTRUMU (TRIPLE WAVEFORM)", wave_frame)
        wave_hdr.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        wave_hdr.setStyleSheet(f"color: {self.theme['primary']}; border: none; background: transparent;")
        wave_layout.addWidget(wave_hdr)
        
        self.wave_canvas = VoiceWaveWidget(wave_frame)
        wave_layout.addWidget(self.wave_canvas)
        left_view_layout.addWidget(wave_frame, 1)
        
        dashboard_layout.addWidget(left_view, 5)
        
        # 2. Right Section (Sohbet Konsolu & ROI Grafiği)
        right_view = QFrame(dashboard_panel)
        right_view_layout = QVBoxLayout(right_view)
        right_view_layout.setContentsMargins(0, 0, 0, 0)
        right_view_layout.setSpacing(15)
        
        # Chat Console Box
        chat_frame = QFrame(right_view)
        chat_frame.setStyleSheet(f"background-color: {self.theme['surface']}; border: 1px solid {self.theme['border']}; border-radius: 12px;")
        chat_layout = QVBoxLayout(chat_frame)
        chat_layout.setContentsMargins(15, 12, 15, 12)
        
        chat_hdr_layout = QHBoxLayout()
        chat_hdr = QLabel("💬 JARVIS SOHBET VE GÖREV MERKEZİ", chat_frame)
        chat_hdr.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        chat_hdr.setStyleSheet(f"color: {self.theme['primary']}; border: none; background: transparent;")
        chat_hdr_layout.addWidget(chat_hdr)
        chat_hdr_layout.addStretch()
        
        status_badge = QLabel("BAĞLANTI: AKTİF", chat_frame)
        status_badge.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        status_badge.setStyleSheet(f"color: {self.theme['success']}; border: none; background: transparent;")
        chat_hdr_layout.addWidget(status_badge)
        chat_layout.addLayout(chat_hdr_layout)
        
        # Scrollable Chat Area
        self.chat_scroll = QScrollArea(chat_frame)
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setStyleSheet("border: none; background: transparent;")
        
        self.chat_container = QWidget()
        self.chat_container.setStyleSheet("background: transparent;")
        self.chat_list_layout = QVBoxLayout(self.chat_container)
        self.chat_list_layout.setContentsMargins(0, 0, 0, 0)
        self.chat_list_layout.setSpacing(10)
        self.chat_list_layout.addStretch()
        
        self.chat_scroll.setWidget(self.chat_container)
        chat_layout.addWidget(self.chat_scroll)
        
        # Input row
        input_row = QHBoxLayout()
        self.input_entry = QLineEdit(chat_frame)
        self.input_entry.setPlaceholderText("Jarvis'e sesli veya yazılı talimat ver...")
        self.input_entry.setFont(QFont("Segoe UI", 10))
        self.input_entry.setStyleSheet(f"""
            QLineEdit {{
                background-color: #070d19;
                color: #ffffff;
                border: 1px solid {self.theme['border']};
                border-radius: 8px;
                padding: 8px 12px;
            }}
            QLineEdit:focus {{
                border-color: {self.theme['primary']};
            }}
        """)
        self.input_entry.returnPressed.connect(self.send_message)
        input_row.addWidget(self.input_entry)
        
        send_btn = PremiumButton("GÖNDER ➔", chat_frame, is_primary=True)
        send_btn.clicked.connect(self.send_message)
        input_row.addWidget(send_btn)
        chat_layout.addLayout(input_row)
        
        right_view_layout.addWidget(chat_frame, 3)
        
        # ROI Chart Frame
        roi_frame = QFrame(right_view)
        roi_frame.setFixedHeight(180)
        roi_frame.setStyleSheet(f"background-color: {self.theme['surface']}; border: 1px solid {self.theme['border']}; border-radius: 12px;")
        roi_layout = QVBoxLayout(roi_frame)
        roi_layout.setContentsMargins(15, 12, 15, 12)
        
        roi_hdr = QLabel("📈 YATIRIM GETİRİSİ VE TELEMETRİ (ROI CHART)", roi_frame)
        roi_hdr.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        roi_hdr.setStyleSheet(f"color: {self.theme['primary']}; border: none; background: transparent;")
        roi_layout.addWidget(roi_hdr)
        
        self.roi_chart = FinancialChartWidget(roi_frame)
        roi_layout.addWidget(self.roi_chart)
        right_view_layout.addWidget(roi_frame, 2)
        
        dashboard_layout.addWidget(right_view, 5)
        
        shell_splitter.addWidget(dashboard_panel)
        main_layout.addWidget(shell_splitter)
        
        # Default greetings
        self.add_message("jarvis", "Merhaba komutanım! PySide6 tabanlı yeni fütüristik Jarvis v3.0 arayüzüne hoş geldiniz. Antialiasing (kenar yumuşatma) ve pürüzsüz animasyonlar başarıyla devrededir.")

    def title_press_event(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def title_move_event(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_start)
            event.accept()

    def add_message(self, sender, text):
        bubble = ChatBubbleItem(sender, text, self)
        # Add to layout before stretch
        count = self.chat_list_layout.count()
        self.chat_list_layout.insertWidget(count - 1, bubble)
        
        # Scroll to bottom
        QTimer.singleShot(50, lambda: self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        ))

    def send_message(self):
        text = self.input_entry.text().strip()
        if not text:
            return
            
        self.add_message("user", text)
        self.input_entry.clear()
        
        # Start thinking animation
        self.wave_canvas.active = True
        
        # Background worker for simulated query
        def run_query():
            try:
                resp = httpx.post("http://localhost:5000/api/jarvis/chat", json={"message": text}, timeout=10)
                reply = resp.json().get("response", "Başarılı bağlantı kuruldu.")
            except Exception as e:
                reply = f"Masaüstü ağ geçidi bağlantı hatası: {e}. Yerel motor simüle ediliyor."
                
            QTimer.singleShot(800, lambda: [
                self.add_message("jarvis", reply),
                setattr(self.wave_canvas, "active", False)
            ])
            
        threading.Thread(target=run_query, daemon=True).start()

def main():
    app = QApplication(sys.argv)
    window = JarvisPySideMainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
