import math
import time
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPolygon

CYAN  = "#00d4ff"
DIM   = "#0a8fa8"
BG    = "#050d12"
AMBER = "#e8b84b"
WHITE = "#cceeff"
GREEN = "#00ff9f"

# ══════════════════════════════════════════════════════════════
# ARC REACTOR  (center animation)
# ══════════════════════════════════════════════════════════════
class ArcReactorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_speaking = False
        self.angle       = 0
        self.pulse       = 0.0
        self.pulse_dir   = 1
        self.scan_angle  = 0
        self.setMinimumSize(260, 260)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(30)

    def start_speaking_animation(self):
        self.is_speaking = True

    def stop_speaking_animation(self):
        self.is_speaking = False
        self.update()

    def _tick(self):
        self.angle      = (self.angle + 1.5) % 360
        self.scan_angle = (self.scan_angle + 0.8) % 360
        if self.is_speaking:
            self.pulse += 0.07 * self.pulse_dir
            if self.pulse >= 1.0 or self.pulse <= 0.0:
                self.pulse_dir *= -1
        else:
            self.pulse = max(0.0, self.pulse - 0.04)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(BG))

        cx = self.width()  // 2
        cy = self.height() // 2
        R  = min(cx, cy) - 16

        # --- glow when speaking ---
        if self.is_speaking:
            for g in range(4):
                gr    = R + 12 + g * 10 + int(self.pulse * 12)
                alpha = max(0, 50 - g * 12)
                p.setPen(QPen(QColor(0, 212, 255, alpha), 2))
                p.setBrush(Qt.NoBrush)
                p.drawEllipse(cx - gr, cy - gr, gr * 2, gr * 2)

        # --- dashed outer ring ---
        pen = QPen(QColor(DIM), 1, Qt.DashLine)
        pen.setDashPattern([4, 6])
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(cx - R, cy - R, R * 2, R * 2)

        # --- rotating arc ---
        pen2 = QPen(QColor(CYAN), 2)
        pen2.setCapStyle(Qt.RoundCap)
        p.setPen(pen2)
        p.drawArc(cx - R + 4, cy - R + 4,
                  (R - 4) * 2, (R - 4) * 2,
                  int(self.angle * 16), 100 * 16)
        p.drawArc(cx - R + 4, cy - R + 4,
                  (R - 4) * 2, (R - 4) * 2,
                  int((self.angle + 180) * 16), 60 * 16)

        # --- counter arc ---
        pen3 = QPen(QColor(0, 100, 140, 180), 1)
        pen3.setCapStyle(Qt.RoundCap)
        p.setPen(pen3)
        r2 = R - 14
        p.drawArc(cx - r2, cy - r2, r2 * 2, r2 * 2,
                  int(-self.angle * 2 * 16), 80 * 16)

        # --- tick marks around outer ring ---
        p.setPen(QPen(QColor(CYAN), 1))
        for i in range(36):
            a   = math.radians(i * 10)
            x1  = cx + int((R - 1) * math.cos(a))
            y1  = cy + int((R - 1) * math.sin(a))
            length = 8 if i % 9 == 0 else 4
            x2  = cx + int((R - 1 - length) * math.cos(a))
            y2  = cy + int((R - 1 - length) * math.sin(a))
            p.drawLine(x1, y1, x2, y2)

        # --- concentric rings ---
        for scale, alpha in [(0.72, 140), (0.52, 100), (0.34, 70)]:
            r = int(R * scale)
            pulse_boost = int(self.pulse * 40) if self.is_speaking else 0
            color = QColor(0, 212, 255, min(255, alpha + pulse_boost))
            p.setPen(QPen(color, 1))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(cx - r, cy - r, r * 2, r * 2)

        # --- radar sweep ---
        sweep_r = int(R * 0.52)
        sweep_color = QColor(0, 212, 255, 30)
        p.setBrush(QBrush(sweep_color))
        p.setPen(Qt.NoPen)
        p.drawPie(
            cx - sweep_r, cy - sweep_r,
            sweep_r * 2, sweep_r * 2,
            int(self.scan_angle * 16), 40 * 16
        )

        # --- hexagon core ---
        hex_r   = int(R * 0.22)
        core_alpha = int(160 + self.pulse * 95) if self.is_speaking else 130
        points  = []
        for i in range(6):
            a = math.radians(60 * i + 30)
            points.append(QPoint(
                cx + int(hex_r * math.cos(a)),
                cy + int(hex_r * math.sin(a))
            ))
        p.setPen(QPen(QColor(0, 212, 255, core_alpha), 2))
        fill_a = 80 if self.is_speaking else 50
        p.setBrush(QBrush(QColor(0, 212, 255, fill_a)))
        p.drawPolygon(QPolygon(points))

        # --- center dot ---
        dot_r = 6
        dot_color = QColor(180, 240, 255, 255) if self.is_speaking else QColor(0, 212, 255, 200)
        p.setBrush(QBrush(dot_color))
        p.setPen(Qt.NoPen)
        p.drawEllipse(cx - dot_r, cy - dot_r, dot_r * 2, dot_r * 2)

        # --- status text ---
        status = "CORE ACTIVE" if not self.is_speaking else "PROCESSING"
        p.setPen(QColor(CYAN))
        f = QFont("Menlo", 8, QFont.Bold)
        p.setFont(f)
        fm   = p.fontMetrics()
        tw   = fm.horizontalAdvance(status)
        p.drawText(cx - tw // 2, cy + int(R * 0.38), status)

        # --- JARVIS label below ---
        p.setPen(QColor(DIM))
        f2 = QFont("Helvetica Neue", 8)
        p.setFont(f2)
        label = "J.A.R.V.I.S."
        tw2   = p.fontMetrics().horizontalAdvance(label)
        p.drawText(cx - tw2 // 2, cy + R + 14, label)


# ══════════════════════════════════════════════════════════════
# TOP BAR WIDGET
# ══════════════════════════════════════════════════════════════
class TopBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(52)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {BG};
                border-bottom: 1px solid {DIM};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(0)

        # left — title
        left = QVBoxLayout()
        left.setSpacing(0)
        title = QLabel("JARVIS")
        title.setStyleSheet(
            f"color: {CYAN}; font-family: 'Helvetica Neue'; "
            f"font-size: 16pt; font-weight: bold; "
            f"letter-spacing: 4px; background: transparent; border: none;"
        )
        sub = QLabel("JUST A RATHER VERY INTELLIGENT SYSTEM")
        sub.setStyleSheet(
            f"color: {DIM}; font-family: 'Menlo'; "
            f"font-size: 7pt; letter-spacing: 2px; "
            f"background: transparent; border: none;"
        )
        left.addWidget(title)
        left.addWidget(sub)
        layout.addLayout(left)
        layout.addStretch()

        # center — status + clock
        center = QVBoxLayout()
        center.setSpacing(2)
        center.setAlignment(Qt.AlignCenter)

        status_row = QHBoxLayout()
        status_row.setSpacing(6)
        dot = QLabel("●")
        dot.setStyleSheet(
            f"color: {GREEN}; font-size: 10pt; "
            f"background: transparent; border: none;"
        )
        status_lbl = QLabel("SYSTEM STATUS")
        status_lbl.setStyleSheet(
            f"color: {DIM}; font-family: 'Menlo'; font-size: 7pt; "
            f"letter-spacing: 1px; background: transparent; border: none;"
        )
        self.status_val = QLabel("OPTIMAL")
        self.status_val.setStyleSheet(
            f"color: {GREEN}; font-family: 'Menlo'; font-size: 9pt; "
            f"font-weight: bold; letter-spacing: 2px; "
            f"background: transparent; border: none;"
        )
        status_row.addWidget(status_lbl)
        status_row.addWidget(dot)
        status_row.addWidget(self.status_val)
        center.addLayout(status_row)

        self.clock_lbl = QLabel("00:00:00")
        self.clock_lbl.setAlignment(Qt.AlignCenter)
        self.clock_lbl.setStyleSheet(
            f"color: {CYAN}; font-family: 'Menlo'; font-size: 13pt; "
            f"font-weight: bold; background: transparent; border: none;"
        )
        center.addWidget(self.clock_lbl)
        layout.addLayout(center)
        layout.addStretch()

        # right — user
        right = QVBoxLayout()
        right.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        user = QLabel("T. STARK")
        user.setAlignment(Qt.AlignRight)
        user.setStyleSheet(
            f"color: {WHITE}; font-family: 'Helvetica Neue'; "
            f"font-size: 11pt; font-weight: bold; "
            f"background: transparent; border: none;"
        )
        role = QLabel("OPERATOR")
        role.setAlignment(Qt.AlignRight)
        role.setStyleSheet(
            f"color: {DIM}; font-family: 'Menlo'; font-size: 7pt; "
            f"letter-spacing: 2px; background: transparent; border: none;"
        )
        right.addWidget(user)
        right.addWidget(role)
        layout.addLayout(right)

        # clock timer
        self._clock = QTimer(self)
        self._clock.timeout.connect(self._tick_clock)
        self._clock.start(1000)
        self._tick_clock()

    def _tick_clock(self):
        self.clock_lbl.setText(time.strftime("%H:%M:%S"))