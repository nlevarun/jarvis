import math
from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPolygon, QRadialGradient

from ui.theme import CYAN, CYAN_DIM, CYAN_DARK, BG, WHITE, GREEN

class ReactorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_speaking  = False
        self.is_thinking  = False
        self.angle        = 0.0
        self.angle2       = 0.0
        self.scan_angle   = 0.0
        self.pulse        = 0.0
        self.pulse_dir    = 1
        self.tick_count   = 0
        self.setMinimumSize(320, 320)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)  # ~60fps

    def start_speaking(self):
        self.is_speaking = True
        self.is_thinking = False

    def stop_speaking(self):
        self.is_speaking = False

    def start_thinking(self):
        self.is_thinking = True
        self.is_speaking = False

    def stop_thinking(self):
        self.is_thinking = False

    def _tick(self):
        self.tick_count += 1
        self.angle      = (self.angle + 1.2) % 360
        self.angle2     = (self.angle2 - 0.7) % 360
        self.scan_angle = (self.scan_angle + 0.9) % 360

        if self.is_speaking or self.is_thinking:
            self.pulse += 0.06 * self.pulse_dir
            if self.pulse >= 1.0 or self.pulse <= 0.0:
                self.pulse_dir *= -1
        else:
            self.pulse = max(0.0, self.pulse - 0.03)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(BG))

        cx = self.width()  // 2
        cy = self.height() // 2
        R  = min(cx, cy) - 10

        self._draw_glow(painter, cx, cy, R)
        self._draw_outer_rings(painter, cx, cy, R)
        self._draw_tick_marks(painter, cx, cy, R)
        self._draw_rotating_arcs(painter, cx, cy, R)
        self._draw_inner_rings(painter, cx, cy, R)
        self._draw_radar_sweep(painter, cx, cy, R)
        self._draw_triangle(painter, cx, cy, R)
        self._draw_center_glow(painter, cx, cy, R)
        self._draw_labels(painter, cx, cy, R)

    def _draw_glow(self, p, cx, cy, R):
        if self.is_speaking or self.is_thinking or self.pulse > 0.05:
            for g in range(5):
                gr    = R + 8 + g * 12 + int(self.pulse * 15)
                alpha = max(0, 45 - g * 9)
                color = QColor(0, 180, 255, alpha) if not self.is_thinking else QColor(255, 180, 0, alpha)
                p.setPen(QPen(color, 2))
                p.setBrush(Qt.NoBrush)
                p.drawEllipse(cx - gr, cy - gr, gr * 2, gr * 2)

    def _draw_outer_rings(self, p, cx, cy, R):
        # outermost dashed ring
        pen = QPen(QColor(CYAN_DIM), 1, Qt.DashLine)
        pen.setDashPattern([3, 5])
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(cx - R, cy - R, R * 2, R * 2)

        # solid ring just inside
        r1 = int(R * 0.93)
        p.setPen(QPen(QColor(CYAN_DARK), 1))
        p.drawEllipse(cx - r1, cy - r1, r1 * 2, r1 * 2)

        # tick ring
        r2 = int(R * 0.86)
        p.setPen(QPen(QColor(CYAN), 1))
        p.drawEllipse(cx - r2, cy - r2, r2 * 2, r2 * 2)

    def _draw_tick_marks(self, p, cx, cy, R):
        p.setPen(QPen(QColor(CYAN), 1))
        r_outer = int(R * 0.93)
        r_inner = int(R * 0.86)
        for i in range(72):
            a     = math.radians(i * 5)
            is_major = i % 9 == 0
            ri    = int(R * 0.82) if is_major else r_inner
            x1    = cx + int(r_outer * math.cos(a))
            y1    = cy + int(r_outer * math.sin(a))
            x2    = cx + int(ri * math.cos(a))
            y2    = cy + int(ri * math.sin(a))
            alpha = 255 if is_major else 120
            p.setPen(QPen(QColor(0, 212, 255, alpha), 2 if is_major else 1))
            p.drawLine(x1, y1, x2, y2)

    def _draw_rotating_arcs(self, p, cx, cy, R):
        r = int(R * 0.78)

        # arc 1 — clockwise
        pen1 = QPen(QColor(CYAN), 3)
        pen1.setCapStyle(Qt.RoundCap)
        p.setPen(pen1)
        p.setBrush(Qt.NoBrush)
        p.drawArc(cx - r, cy - r, r * 2, r * 2,
                  int(self.angle * 16), 110 * 16)
        p.drawArc(cx - r, cy - r, r * 2, r * 2,
                  int((self.angle + 180) * 16), 70 * 16)

        # arc 2 — counter clockwise
        r2  = int(R * 0.68)
        pen2 = QPen(QColor(0, 140, 200, 180), 2)
        pen2.setCapStyle(Qt.RoundCap)
        p.setPen(pen2)
        p.drawArc(cx - r2, cy - r2, r2 * 2, r2 * 2,
                  int(self.angle2 * 16), 90 * 16)
        p.drawArc(cx - r2, cy - r2, r2 * 2, r2 * 2,
                  int((self.angle2 + 150) * 16), 50 * 16)

    def _draw_inner_rings(self, p, cx, cy, R):
        for scale, alpha_base in [
            (0.58, 130), (0.46, 100), (0.34, 80)
        ]:
            r     = int(R * scale)
            boost = int(self.pulse * 50) if (self.is_speaking or self.is_thinking) else 0
            alpha = min(255, alpha_base + boost)
            color = QColor(0, 212, 255, alpha)
            if self.is_thinking:
                color = QColor(255, 180, 0, alpha)
            p.setPen(QPen(color, 1))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(cx - r, cy - r, r * 2, r * 2)

    def _draw_radar_sweep(self, p, cx, cy, R):
        sweep_r = int(R * 0.58)
        color   = QColor(0, 212, 255, 25)
        if self.is_thinking:
            color = QColor(255, 180, 0, 25)
        p.setBrush(QBrush(color))
        p.setPen(Qt.NoPen)
        p.drawPie(
            cx - sweep_r, cy - sweep_r,
            sweep_r * 2, sweep_r * 2,
            int(self.scan_angle * 16), 50 * 16
        )

    def _draw_triangle(self, p, cx, cy, R):
        tri_r     = int(R * 0.28)
        tri_alpha = int(180 + self.pulse * 75) if self.is_speaking else 140
        points    = []
        for i in range(3):
            a = math.radians(120 * i - 90)
            points.append(QPoint(
                cx + int(tri_r * math.cos(a)),
                cy + int(tri_r * math.sin(a))
            ))

        # outer triangle
        color = QColor(0, 212, 255, tri_alpha)
        if self.is_thinking:
            color = QColor(255, 180, 0, tri_alpha)
        p.setPen(QPen(color, 2))
        fill_alpha = 60 if self.is_speaking else 35
        fill_color = QColor(0, 212, 255, fill_alpha)
        if self.is_thinking:
            fill_color = QColor(255, 180, 0, fill_alpha)
        p.setBrush(QBrush(fill_color))
        p.drawPolygon(QPolygon(points))

        # inner inverted triangle
        tri_r2 = int(tri_r * 0.55)
        inner  = []
        for i in range(3):
            a = math.radians(120 * i + 90)
            inner.append(QPoint(
                cx + int(tri_r2 * math.cos(a)),
                cy + int(tri_r2 * math.sin(a))
            ))
        p.setPen(QPen(color, 1))
        p.setBrush(Qt.NoBrush)
        p.drawPolygon(QPolygon(inner))

    def _draw_center_glow(self, p, cx, cy, R):
        dot_r = 8
        if self.is_speaking or self.is_thinking or self.pulse > 0.1:
            glow_r = int(dot_r + self.pulse * 20)
            grad   = QRadialGradient(cx, cy, glow_r)
            c      = QColor(0, 212, 255) if not self.is_thinking else QColor(255, 180, 0)
            grad.setColorAt(0.0, QColor(c.red(), c.green(), c.blue(), 180))
            grad.setColorAt(1.0, QColor(c.red(), c.green(), c.blue(), 0))
            p.setBrush(QBrush(grad))
            p.setPen(Qt.NoPen)
            p.drawEllipse(cx - glow_r, cy - glow_r, glow_r * 2, glow_r * 2)

        dot_color = QColor(200, 240, 255, 255) if self.is_speaking else QColor(0, 212, 255, 220)
        p.setBrush(QBrush(dot_color))
        p.setPen(Qt.NoPen)
        p.drawEllipse(cx - dot_r, cy - dot_r, dot_r * 2, dot_r * 2)

    def _draw_labels(self, p, cx, cy, R):
        # CORE STATUS label bottom left of reactor
        status = "ONLINE" if not self.is_thinking else "THINKING"
        color  = QColor(GREEN) if not self.is_thinking else QColor(255, 180, 0)

        p.setPen(QColor(CYAN_DIM))
        f_sm = QFont("Menlo", 7)
        p.setFont(f_sm)
        p.drawText(cx - R, cy + int(R * 0.72), "CORE STATUS")

        p.setPen(color)
        f_lg = QFont("Menlo", 10, QFont.Bold)
        p.setFont(f_lg)
        p.drawText(cx - R, cy + int(R * 0.72) + 18, status)

        # POWER OUTPUT label bottom right
        p.setPen(QColor(CYAN_DIM))
        p.setFont(f_sm)
        power_label = "POWER OUTPUT"
        pw = p.fontMetrics().horizontalAdvance(power_label)
        p.drawText(cx + R - pw, cy + int(R * 0.72), power_label)

        p.setPen(QColor(CYAN))
        p.setFont(f_lg)
        pct = f"{min(100, 97 + int(self.pulse * 3)):.1f}%"
        pw2 = p.fontMetrics().horizontalAdvance(pct)
        p.drawText(cx + R - pw2, cy + int(R * 0.72) + 18, pct)

        # J.A.R.V.I.S. below
        p.setPen(QColor(CYAN_DIM))
        f_title = QFont("Helvetica Neue", 9, QFont.Bold)
        p.setFont(f_title)
        label = "J.A.R.V.I.S."
        lw    = p.fontMetrics().horizontalAdvance(label)
        p.drawText(cx - lw // 2, cy + R + 22, label)