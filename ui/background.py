import math
import random
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPainter, QColor, QPen

from ui.theme import BG, CYAN_DARK, BORDER, CYAN

class BackgroundWidget(QWidget):
    """Animated circuit grid that sits behind the whole UI."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._offset = 0
        self._particles = []
        self._init_particles()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(50)

    def _init_particles(self):
        for _ in range(18):
            self._particles.append({
                "x": random.random(),
                "y": random.random(),
                "speed": random.uniform(0.0003, 0.001),
                "size": random.uniform(1.5, 3.5),
                "alpha": random.randint(30, 100),
            })

    def _tick(self):
        self._offset = (self._offset + 1) % 60
        for p in self._particles:
            p["y"] -= p["speed"]
            if p["y"] < 0:
                p["y"] = 1.0
                p["x"] = random.random()
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(BG))
        w, h = self.width(), self.height()

        # grid lines
        grid = 60
        pen = QPen(QColor(BORDER))
        pen.setWidth(1)
        p.setPen(pen)
        offset = self._offset % grid

        for x in range(-grid, w + grid, grid):
            p.setOpacity(0.25)
            p.drawLine(x + offset, 0, x + offset, h)
        for y in range(-grid, h + grid, grid):
            p.setOpacity(0.25)
            p.drawLine(0, y + offset, w, y + offset)

        # corner brackets on grid intersections
        p.setOpacity(0.15)
        bracket_pen = QPen(QColor(CYAN))
        bracket_pen.setWidth(1)
        p.setPen(bracket_pen)
        bsize = 6
        for gx in range(0, w, grid):
            for gy in range(0, h, grid):
                ax = (gx + offset) % w
                ay = (gy + offset) % h
                p.drawLine(ax, ay, ax + bsize, ay)
                p.drawLine(ax, ay, ax, ay + bsize)

        # floating particles
        for pt in self._particles:
            px = int(pt["x"] * w)
            py = int(pt["y"] * h)
            color = QColor(CYAN)
            color.setAlpha(pt["alpha"])
            p.setOpacity(1.0)
            p.setPen(Qt.NoPen)
            p.setBrush(color)
            r = pt["size"]
            p.drawEllipse(int(px - r), int(py - r), int(r * 2), int(r * 2))

        p.end()