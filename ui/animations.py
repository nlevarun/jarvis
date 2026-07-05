import math
import random
from PySide6.QtWidgets import QWidget, QHBoxLayout, QSizePolicy
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QFont

from ui.theme import CYAN, CYAN_DIM, CYAN_DARK, BG, GREEN, WHITE, BORDER


# ══════════════════════════════════════════════════════════════
# WAVEFORM  (bottom left — voice input indicator)
# ══════════════════════════════════════════════════════════════
class WaveformWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._active  = False
        self._bars    = 32
        self._heights = [0.05] * self._bars
        self._phase   = 0.0
        self.setFixedHeight(40)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(40)

    def set_active(self, active: bool):
        self._active = active

    def _tick(self):
        self._phase += 0.15
        if self._active:
            for i in range(self._bars):
                target = 0.3 + 0.7 * abs(
                    math.sin(self._phase + i * 0.4) *
                    math.cos(self._phase * 0.7 + i * 0.2)
                )
                self._heights[i] += (target - self._heights[i]) * 0.3
        else:
            for i in range(self._bars):
                target = 0.05 + 0.08 * abs(math.sin(self._phase * 0.3 + i * 0.5))
                self._heights[i] += (target - self._heights[i]) * 0.15
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(BG))
        w, h   = self.width(), self.height()
        bar_w  = max(2, (w - self._bars) // self._bars)
        gap    = 1

        for i, val in enumerate(self._heights):
            x     = i * (bar_w + gap)
            bh    = int(val * h)
            y     = h - bh
            alpha = int(100 + 155 * val)
            if self._active:
                color = QColor(0, 212, 255, alpha)
            else:
                color = QColor(0, 100, 140, alpha)
            p.fillRect(x, y, bar_w, bh, color)
        p.end()


# ══════════════════════════════════════════════════════════════
# THINKING DOTS  (animated "..." when Jarvis is processing)
# ══════════════════════════════════════════════════════════════
class ThinkingDots(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._visible = False
        self._frame   = 0
        self.setFixedSize(50, 20)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(400)

    def set_visible(self, v: bool):
        self._visible = v
        self.update()

    def _tick(self):
        if self._visible:
            self._frame = (self._frame + 1) % 4
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(BG))
        if not self._visible:
            return
        dot_r = 4
        spacing = 14
        for i in range(3):
            alpha = 255 if i < self._frame else 60
            color = QColor(0, 212, 255, alpha)
            p.setBrush(color)
            p.setPen(Qt.NoPen)
            x = 6 + i * spacing
            y = self.height() // 2
            p.drawEllipse(x - dot_r, y - dot_r, dot_r * 2, dot_r * 2)
        p.end()


# ══════════════════════════════════════════════════════════════
# VOICE ACTIVITY BARS  (bottom right)
# ══════════════════════════════════════════════════════════════
class VoiceActivityWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._active  = False
        self._bars    = 16
        self._heights = [0.05] * self._bars
        self._phase   = 0.0
        self.setFixedHeight(36)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(50)

    def set_active(self, v: bool):
        self._active = v

    def _tick(self):
        self._phase += 0.2
        for i in range(self._bars):
            if self._active:
                target = 0.2 + 0.8 * abs(math.sin(self._phase + i * 0.6))
            else:
                target = 0.05 + 0.05 * abs(math.sin(self._phase * 0.2 + i))
            self._heights[i] += (target - self._heights[i]) * 0.25
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(BG))
        w, h  = self.width(), self.height()
        bar_w = max(2, (w - self._bars) // self._bars)
        gap   = 2

        for i, val in enumerate(self._heights):
            x     = i * (bar_w + gap)
            bh    = int(val * h)
            y     = h - bh
            alpha = int(80 + 175 * val)
            color = QColor(0, 255, 159, alpha) if self._active else QColor(0, 100, 80, alpha)
            p.fillRect(x, y, bar_w, bh, color)
        p.end()


# ══════════════════════════════════════════════════════════════
# BOTTOM BAR  (waveform + mic status + voice activity)
# ══════════════════════════════════════════════════════════════
class BottomBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(56)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {BG};
                border-top: 1px solid {CYAN_DARK};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(16)

        self.waveform = WaveformWidget()
        layout.addWidget(self.waveform, 3)

        self.mic_label = _make_label("● MIC ACTIVE", GREEN, 8)
        self.mic_label.setFixedWidth(100)
        layout.addWidget(self.mic_label)

        layout.addStretch()

        voice_label = _make_label("VOICE ACTIVITY", CYAN_DIM, 7)
        layout.addWidget(voice_label)

        self.voice_bars = VoiceActivityWidget()
        self.voice_bars.setFixedWidth(140)
        layout.addWidget(self.voice_bars)

    def set_listening(self, v: bool):
        self.waveform.set_active(v)
        self.voice_bars.set_active(v)
        if v:
            self.mic_label.setText("● MIC ACTIVE")
            self.mic_label.setStyleSheet(
                f"color: {GREEN}; font-family: 'Menlo'; font-size: 8pt; "
                f"background: transparent; border: none;"
            )
        else:
            self.mic_label.setText("○ MIC IDLE")
            self.mic_label.setStyleSheet(
                f"color: {CYAN_DIM}; font-family: 'Menlo'; font-size: 8pt; "
                f"background: transparent; border: none;"
            )


def _make_label(text, color, size):
    from PySide6.QtWidgets import QLabel
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color: {color}; font-family: 'Menlo'; font-size: {size}pt; "
        f"background: transparent; border: none;"
    )
    return lbl