import psutil
import time
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QFont

# ── shared colors ──────────────────────────────────────────────
CYAN   = "#00d4ff"
DIM    = "#0a8fa8"
BG     = "#050d12"
BORDER = "#0f4a5c"
WHITE  = "#cceeff"
GREEN  = "#00ff9f"
AMBER  = "#e8b84b"
RED    = "#ff4455"

MONO = "Menlo"
SYS  = "Helvetica Neue"


def bracket_style(widget):
    """Adds corner-bracket look via stylesheet."""
    widget.setStyleSheet(f"""
        QWidget {{
            background-color: {BG};
            border: 1px solid {BORDER};
            border-radius: 0px;
        }}
    """)


# ── reusable tiny widgets ──────────────────────────────────────
class HUDLabel(QLabel):
    def __init__(self, text="", color=WHITE, size=9, bold=False, mono=False):
        super().__init__(text)
        font_family = MONO if mono else SYS
        weight = "bold" if bold else "normal"
        self.setStyleSheet(
            f"color: {color}; font-family: '{font_family}'; "
            f"font-size: {size}pt; font-weight: {weight}; "
            f"background: transparent; border: none;"
        )
        self.setWordWrap(True)


class BarWidget(QWidget):
    """A simple horizontal progress bar."""
    def __init__(self, color=CYAN):
        super().__init__()
        self._value = 0.0
        self._color = QColor(color)
        self.setFixedHeight(6)

    def set_value(self, v):
        self._value = max(0.0, min(1.0, v))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(BORDER))
        w = int(self.width() * self._value)
        if w > 0:
            color = self._color
            if self._value > 0.85:
                color = QColor(RED)
            elif self._value > 0.65:
                color = QColor(AMBER)
            p.fillRect(0, 0, w, self.height(), color)


class MiniBarChart(QWidget):
    """Scrolling bar chart for CPU history."""
    def __init__(self, bars=30, color=CYAN):
        super().__init__()
        self._data   = [0.0] * bars
        self._color  = QColor(color)
        self._bars   = bars
        self.setFixedHeight(40)

    def push(self, value):
        self._data.append(max(0.0, min(1.0, value)))
        if len(self._data) > self._bars:
            self._data.pop(0)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(BG))
        w = self.width()
        h = self.height()
        bar_w = max(1, w // self._bars - 1)
        for i, v in enumerate(self._data):
            x     = i * (bar_w + 1)
            bh    = int(v * h)
            alpha = int(80 + 175 * v)
            color = QColor(self._color)
            color.setAlpha(alpha)
            p.fillRect(x, h - bh, bar_w, bh, color)


# ══════════════════════════════════════════════════════════════
# PANEL BASE
# ══════════════════════════════════════════════════════════════
class BasePanel(QWidget):
    def __init__(self, title="", tag="", parent=None):
        super().__init__(parent)
        bracket_style(self)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 6, 10, 10)
        root.setSpacing(6)

        # header row
        header = QHBoxLayout()
        header.setSpacing(0)
        lbl_sys = HUDLabel("SYSTEM //", color=DIM, size=8, mono=True)
        lbl_title = HUDLabel(title, color=CYAN, size=8, bold=True, mono=True)
        lbl_tag = HUDLabel(tag, color=DIM, size=8, mono=True)
        header.addWidget(lbl_sys)
        header.addWidget(lbl_title)
        header.addStretch()
        header.addWidget(lbl_tag)
        root.addLayout(header)

        # divider
        div = QWidget()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background: {BORDER}; border: none;")
        root.addWidget(div)

        self.content_layout = root

    def add(self, widget):
        self.content_layout.addWidget(widget)

    def add_layout(self, layout):
        self.content_layout.addLayout(layout)

    def add_stretch(self):
        self.content_layout.addStretch()


# ══════════════════════════════════════════════════════════════
# VITAL SIGNS PANEL  (CPU history chart)
# ══════════════════════════════════════════════════════════════
class VitalSignsPanel(BasePanel):
    def __init__(self):
        super().__init__(title="VITALS", tag="VITAL SIGNS")

        self.cpu_chart = MiniBarChart(bars=30, color=CYAN)
        self.add(self.cpu_chart)

        row = QHBoxLayout()
        self.lbl_heart = HUDLabel("Heart Rate", color=DIM, size=8)
        self.lbl_bpm   = HUDLabel("-- BPM", color=WHITE, size=18, bold=True)
        row.addWidget(self.lbl_heart)
        row.addStretch()
        row.addWidget(self.lbl_bpm)
        self.add_layout(row)
        self.add_stretch()

        # fake-ish heart rate derived from CPU
        self._base_bpm = 62

    def refresh(self, cpu_pct):
        self.cpu_chart.push(cpu_pct / 100.0)
        bpm = int(self._base_bpm + cpu_pct * 0.4)
        self.lbl_bpm.setText(f"{bpm} BPM")


# ══════════════════════════════════════════════════════════════
# RT-MONITOR PANEL  (CPU + RAM)
# ══════════════════════════════════════════════════════════════
class MonitorPanel(BasePanel):
    def __init__(self):
        super().__init__(title="MONITOR", tag="RT-MONITOR")

        # CPU
        cpu_row = QHBoxLayout()
        self.lbl_cpu = HUDLabel("CPU Load", color=DIM, size=9)
        self.val_cpu = HUDLabel("0%", color=WHITE, size=9, mono=True)
        cpu_row.addWidget(self.lbl_cpu)
        cpu_row.addStretch()
        cpu_row.addWidget(self.val_cpu)
        self.add_layout(cpu_row)
        self.bar_cpu = BarWidget(CYAN)
        self.add(self.bar_cpu)

        # RAM
        ram_row = QHBoxLayout()
        self.lbl_ram = HUDLabel("Memory", color=DIM, size=9)
        self.val_ram = HUDLabel("-- GB", color=WHITE, size=9, mono=True)
        ram_row.addWidget(self.lbl_ram)
        ram_row.addStretch()
        ram_row.addWidget(self.val_ram)
        self.add_layout(ram_row)
        self.bar_ram = BarWidget(CYAN)
        self.add(self.bar_ram)

        # GPU placeholder
        gpu_row = QHBoxLayout()
        self.lbl_gpu = HUDLabel("GPU Temp", color=DIM, size=9)
        self.val_gpu = HUDLabel("N/A", color=WHITE, size=9, mono=True)
        gpu_row.addWidget(self.lbl_gpu)
        gpu_row.addStretch()
        gpu_row.addWidget(self.val_gpu)
        self.add_layout(gpu_row)
        self.add_stretch()

    def refresh(self, cpu_pct, ram):
        self.val_cpu.setText(f"{cpu_pct:.0f}%")
        self.bar_cpu.set_value(cpu_pct / 100.0)
        used_gb = (ram.total - ram.available) / 1e9
        total_gb = ram.total / 1e9
        self.val_ram.setText(f"{used_gb:.1f} / {total_gb:.0f} GB")
        self.bar_ram.set_value(ram.percent / 100.0)


# ══════════════════════════════════════════════════════════════
# NETWORK PANEL
# ══════════════════════════════════════════════════════════════
class NetworkPanel(BasePanel):
    def __init__(self):
        super().__init__(title="NETWORK", tag="UP-LINK")
        self._prev_sent = psutil.net_io_counters().bytes_sent
        self._prev_recv = psutil.net_io_counters().bytes_recv

        row_up = QHBoxLayout()
        self.lbl_up = HUDLabel("Upload", color=DIM, size=9)
        self.val_up = HUDLabel("-- KB/s", color=GREEN, size=9, mono=True)
        row_up.addWidget(self.lbl_up)
        row_up.addStretch()
        row_up.addWidget(self.val_up)
        self.add_layout(row_up)
        self.bar_up = BarWidget(GREEN)
        self.add(self.bar_up)

        row_dn = QHBoxLayout()
        self.lbl_dn = HUDLabel("Download", color=DIM, size=9)
        self.val_dn = HUDLabel("-- KB/s", color=CYAN, size=9, mono=True)
        row_dn.addWidget(self.lbl_dn)
        row_dn.addStretch()
        row_dn.addWidget(self.val_dn)
        self.add_layout(row_dn)
        self.bar_dn = BarWidget(CYAN)
        self.add(self.bar_dn)

        status_row = QHBoxLayout()
        self.lbl_status = HUDLabel("Status", color=DIM, size=9)
        self.val_status = HUDLabel("SIGNAL ENCRYPTED", color=GREEN, size=9, mono=True)
        status_row.addWidget(self.lbl_status)
        status_row.addStretch()
        status_row.addWidget(self.val_status)
        self.add_layout(status_row)
        self.add_stretch()

    def refresh(self):
        counters = psutil.net_io_counters()
        up_kb = (counters.bytes_sent - self._prev_sent) / 1024
        dn_kb = (counters.bytes_recv - self._prev_recv) / 1024
        self._prev_sent = counters.bytes_sent
        self._prev_recv = counters.bytes_recv

        self.val_up.setText(f"{up_kb:.0f} KB/s")
        self.val_dn.setText(f"{dn_kb:.0f} KB/s")
        self.bar_up.set_value(min(up_kb / 1000, 1.0))
        self.bar_dn.set_value(min(dn_kb / 5000, 1.0))


# ══════════════════════════════════════════════════════════════
# SYSTEM LOG PANEL
# ══════════════════════════════════════════════════════════════
class LogPanel(BasePanel):
    def __init__(self):
        super().__init__(title="LOG", tag="RT-LOG")
        self._entries = []
        self.lbl_log  = HUDLabel("", color=DIM, size=8, mono=True)
        self.lbl_log.setAlignment(Qt.AlignTop)
        self.add(self.lbl_log)
        self.add_stretch()

        self.push("System integrity check complete")
        self.push("All subsystems nominal")
        self.push("Awaiting operator input")

    def push(self, message: str, color=None):
        ts = time.strftime("%H:%M:%S")
        c  = color or DIM
        entry = f'<span style="color:{CYAN};">[{ts}]</span> ' \
                f'<span style="color:{WHITE};">{message}</span>'
        self._entries.append(entry)
        if len(self._entries) > 6:
            self._entries.pop(0)
        self.lbl_log.setText("<br>".join(self._entries))


# ══════════════════════════════════════════════════════════════
# IRON MAN SUIT PANEL
# ══════════════════════════════════════════════════════════════
class SuitPanel(BasePanel):
    def __init__(self):
        super().__init__(title="MARK LXXXV", tag="SUIT STATUS")

        for label, value, color in [
            ("Power Core",       "98%",  GREEN),
            ("Structural",       "100%", GREEN),
            ("Repulsors",        "READY", CYAN),
            ("Defense Systems",  "ACTIVE", CYAN),
        ]:
            row = QHBoxLayout()
            lbl = HUDLabel(label, color=DIM, size=9)
            val = HUDLabel(value, color=color, size=9, bold=True, mono=True)
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(val)
            self.add_layout(row)
            bar = BarWidget(color)
            bar.set_value(1.0)
            self.add(bar)

        self.add_stretch()


# ══════════════════════════════════════════════════════════════
# ACTIVITY PANEL  (search results / code output)
# ══════════════════════════════════════════════════════════════
class ActivityPanel(BasePanel):
    def __init__(self):
        super().__init__(title="ACTIVITY", tag="ROOT@JARVIS")
        self.lbl = HUDLabel("", color=DIM, size=8, mono=True)
        self.lbl.setAlignment(Qt.AlignTop)
        self.add(self.lbl)
        self.add_stretch()

    def set_html(self, html: str):
        self.lbl.setText(html)

    def clear(self):
        self.lbl.setText("")