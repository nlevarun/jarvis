import psutil
import time
import socket
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                                QLabel, QSizePolicy, QScrollArea)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QFont

from ui.theme import (CYAN, CYAN_DIM, CYAN_DARK, BG, BG_PANEL, BORDER,
                      WHITE, WHITE_DIM, GREEN, GREEN_DIM, AMBER, RED,
                      FONT_MONO, FONT_UI, SIZE_XS, SIZE_SM, SIZE_MD)


# ── helpers ───────────────────────────────────────────────────
def _lbl(text="", color=WHITE, size=SIZE_MD, bold=False, mono=False):
    l = QLabel(text)
    l.setStyleSheet(
        f"color:{color}; font-family:'{FONT_MONO if mono else FONT_UI}';"
        f"font-size:{size}pt; font-weight:{'bold' if bold else 'normal'};"
        f"background:transparent; border:none;"
    )
    l.setWordWrap(True)
    return l


class BarWidget(QWidget):
    def __init__(self, color=CYAN):
        super().__init__()
        self._v = 0.0
        self._c = QColor(color)
        self.setFixedHeight(5)

    def set_value(self, v):
        self._v = max(0.0, min(1.0, v))
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(BORDER))
        w = int(self.width() * self._v)
        if w > 0:
            c = QColor(RED) if self._v > 0.85 else QColor(AMBER) if self._v > 0.65 else self._c
            p.fillRect(0, 0, w, self.height(), c)


class MiniChart(QWidget):
    def __init__(self, bars=28, color=CYAN):
        super().__init__()
        self._d = [0.0] * bars
        self._c = QColor(color)
        self._b = bars
        self.setFixedHeight(36)

    def push(self, v):
        self._d.append(max(0.0, min(1.0, v)))
        if len(self._d) > self._b:
            self._d.pop(0)
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(BG))
        w, h  = self.width(), self.height()
        bw    = max(1, w // self._b - 1)
        for i, v in enumerate(self._d):
            x  = i * (bw + 1)
            bh = int(v * h)
            c  = QColor(self._c)
            c.setAlpha(int(80 + 175 * v))
            p.fillRect(x, h - bh, bw, bh, c)


# ── base panel ────────────────────────────────────────────────
class Panel(QWidget):
    def __init__(self, title="", tag="", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QWidget {{
                background-color:{BG_PANEL};
                border:1px solid {BORDER};
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 6, 10, 10)
        root.setSpacing(5)

        # header
        hdr = QHBoxLayout()
        hdr.setSpacing(4)
        hdr.addWidget(_lbl("SYSTEM //", CYAN_DIM, SIZE_XS, mono=True))
        hdr.addWidget(_lbl(title, CYAN, SIZE_XS, bold=True, mono=True))
        hdr.addStretch()
        if tag:
            hdr.addWidget(_lbl(tag, CYAN_DIM, SIZE_XS, mono=True))
        root.addLayout(hdr)

        div = QWidget()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background:{BORDER}; border:none;")
        root.addWidget(div)

        self.body = root

    def add(self, w):    self.body.addWidget(w)
    def addL(self, l):   self.body.addLayout(l)
    def addS(self):      self.body.addStretch()

    def _row(self, label, value, lc=CYAN_DIM, vc=WHITE):
        r = QHBoxLayout()
        r.addWidget(_lbl(label, lc, SIZE_SM, mono=True))
        r.addStretch()
        r.addWidget(_lbl(value, vc, SIZE_SM, bold=True, mono=True))
        self.addL(r)
        return r


# ══════════════════════════════════════════════════════════════
# SYSTEMS OVERVIEW  (CPU, RAM, Disk, Network, Temp)
# ══════════════════════════════════════════════════════════════
class SystemsPanel(Panel):
    def __init__(self):
        super().__init__("SYSTEMS", "OVERVIEW")
        self._rows = {}

        specs = [
            ("CPU",   CYAN,  "0%"),
            ("MEMORY", AMBER, "-- GB"),
            ("DISK",  CYAN,  "0%"),
            ("NETWORK", GREEN, "-- KB/s"),
            ("TEMP",  CYAN,  "-- °C"),
        ]
        for name, color, default in specs:
            row = QHBoxLayout()
            icon_map = {
                "CPU": "⬡", "MEMORY": "⬡",
                "DISK": "⬡", "NETWORK": "⬡", "TEMP": "⬡"
            }
            icon = _lbl(icon_map[name], color, SIZE_SM, mono=True)
            icon.setFixedWidth(16)
            lbl  = _lbl(name, WHITE_DIM, SIZE_SM, mono=True)
            lbl.setFixedWidth(70)
            val  = _lbl(default, WHITE, SIZE_SM, bold=True, mono=True)
            val.setFixedWidth(70)
            val.setAlignment(Qt.AlignRight)
            row.addWidget(icon)
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(val)
            self.addL(row)

            bar = BarWidget(color)
            self.add(bar)
            self._rows[name] = (val, bar)

        self.addS()

    def refresh(self, cpu, ram, disk, net_kb, temp):
        v, b = self._rows["CPU"]
        v.setText(f"{cpu:.0f}%")
        b.set_value(cpu / 100)

        v, b = self._rows["MEMORY"]
        used = (ram.total - ram.available) / 1e9
        tot  = ram.total / 1e9
        v.setText(f"{used:.1f}/{tot:.0f}G")
        b.set_value(ram.percent / 100)

        v, b = self._rows["DISK"]
        v.setText(f"{disk:.0f}%")
        b.set_value(disk / 100)

        v, b = self._rows["NETWORK"]
        v.setText(f"{net_kb:.0f}KB/s")
        b.set_value(min(net_kb / 5000, 1.0))

        v, b = self._rows["TEMP"]
        if temp is not None:
            v.setText(f"{temp:.0f}°C")
            b.set_value(min(temp / 100, 1.0))
        else:
            v.setText("N/A")


# ══════════════════════════════════════════════════════════════
# NETWORK PANEL
# ══════════════════════════════════════════════════════════════
class NetworkPanel(Panel):
    def __init__(self):
        super().__init__("NETWORK", "REAL-TIME")
        self._prev_sent = psutil.net_io_counters().bytes_sent
        self._prev_recv = psutil.net_io_counters().bytes_recv

        self._up_chart = MiniChart(color=GREEN)
        self._dn_chart = MiniChart(color=CYAN)

        up_r = QHBoxLayout()
        self._up_icon = _lbl("▲", GREEN, SIZE_SM, mono=True)
        self._up_val  = _lbl("-- KB/s", GREEN, SIZE_SM, bold=True, mono=True)
        up_r.addWidget(_lbl("UPLOAD", CYAN_DIM, SIZE_SM, mono=True))
        up_r.addWidget(self._up_icon)
        up_r.addStretch()
        up_r.addWidget(self._up_val)
        self.addL(up_r)
        self.add(self._up_chart)

        dn_r = QHBoxLayout()
        self._dn_icon = _lbl("▼", CYAN, SIZE_SM, mono=True)
        self._dn_val  = _lbl("-- KB/s", CYAN, SIZE_SM, bold=True, mono=True)
        dn_r.addWidget(_lbl("DOWNLOAD", CYAN_DIM, SIZE_SM, mono=True))
        dn_r.addWidget(self._dn_icon)
        dn_r.addStretch()
        dn_r.addWidget(self._dn_val)
        self.addL(dn_r)
        self.add(self._dn_chart)

        # IP
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            ip = "127.0.0.1"

        status_r = QHBoxLayout()
        status_r.addWidget(_lbl("STATUS", CYAN_DIM, SIZE_SM, mono=True))
        status_r.addStretch()
        status_r.addWidget(_lbl("CONNECTED", GREEN, SIZE_SM, bold=True, mono=True))
        self.addL(status_r)

        ip_r = QHBoxLayout()
        ip_r.addWidget(_lbl("IP ADDRESS", CYAN_DIM, SIZE_SM, mono=True))
        ip_r.addStretch()
        ip_r.addWidget(_lbl(ip, WHITE, SIZE_SM, mono=True))
        self.addL(ip_r)
        self.addS()

    def refresh(self):
        c    = psutil.net_io_counters()
        up   = (c.bytes_sent - self._prev_sent) / 1024
        dn   = (c.bytes_recv - self._prev_recv) / 1024
        self._prev_sent = c.bytes_sent
        self._prev_recv = c.bytes_recv
        self._up_val.setText(f"{up:.0f} KB/s")
        self._dn_val.setText(f"{dn:.0f} KB/s")
        self._up_chart.push(min(up / 1000, 1.0))
        self._dn_chart.push(min(dn / 5000, 1.0))


# ══════════════════════════════════════════════════════════════
# WORLD CLOCK
# ══════════════════════════════════════════════════════════════
class WorldClockPanel(Panel):
    def __init__(self):
        super().__init__("WORLD CLOCK", "")
        from datetime import datetime, timezone, timedelta

        self._cities = [
            ("SAN FRANCISCO", -7),
            ("LONDON",         1),
            ("TOKYO",          9),
        ]
        self._time_labels = []
        self._date_labels = []

        row = QHBoxLayout()
        row.setSpacing(0)
        for city, offset in self._cities:
            col = QVBoxLayout()
            col.setSpacing(2)
            col.setAlignment(Qt.AlignHCenter)
            city_lbl = _lbl(city, CYAN_DIM, SIZE_XS, mono=True)
            city_lbl.setAlignment(Qt.AlignCenter)
            time_lbl = _lbl("--:--", WHITE, 14, bold=True, mono=True)
            time_lbl.setAlignment(Qt.AlignCenter)
            date_lbl = _lbl("---", CYAN_DIM, SIZE_XS, mono=True)
            date_lbl.setAlignment(Qt.AlignCenter)
            col.addWidget(city_lbl)
            col.addWidget(time_lbl)
            col.addWidget(date_lbl)
            row.addLayout(col)
            if city != self._cities[-1][0]:
                row.addStretch()
            self._time_labels.append((time_lbl, date_lbl, offset))

        self.addL(row)
        self.addS()

        t = QTimer(self)
        t.timeout.connect(self._tick)
        t.start(1000)
        self._tick()

    def _tick(self):
        from datetime import datetime, timezone, timedelta
        for time_lbl, date_lbl, offset in self._time_labels:
            dt = datetime.now(timezone.utc) + timedelta(hours=offset)
            time_lbl.setText(dt.strftime("%H:%M"))
            date_lbl.setText(dt.strftime("%b %d").upper())


# ══════════════════════════════════════════════════════════════
# AI STATUS
# ══════════════════════════════════════════════════════════════
class AIStatusPanel(Panel):
    def __init__(self):
        super().__init__("AI STATUS", "ASSISTANT")

        specs = [
            ("MODEL",   "llama3.2",  WHITE),
            ("STATUS",  "ONLINE",    GREEN),
            ("LATENCY", "-- ms",     CYAN),
            ("CONTEXT", "0 msgs",    WHITE),
            ("VOICE",   "DANIEL",    CYAN),
            ("MODE",    "STANDARD",  WHITE),
        ]
        self._vals = {}
        for key, default, color in specs:
            r = QHBoxLayout()
            r.addWidget(_lbl(key, CYAN_DIM, SIZE_SM, mono=True))
            r.addStretch()
            v = _lbl(default, color, SIZE_SM, bold=True, mono=True)
            r.addWidget(v)
            self.addL(r)
            self._vals[key] = v

        self.addS()

    def set_latency(self, ms):
        self._vals["LATENCY"].setText(f"{ms} ms")

    def set_context(self, n):
        self._vals["CONTEXT"].setText(f"{n} msgs")

    def set_status(self, s, color=GREEN):
        self._vals["STATUS"].setText(s)
        self._vals["STATUS"].setStyleSheet(
            f"color:{color}; font-family:'{FONT_MONO}'; font-size:{SIZE_SM}pt;"
            f"font-weight:bold; background:transparent; border:none;"
        )


# ══════════════════════════════════════════════════════════════
# TOOLS / MODULES
# ══════════════════════════════════════════════════════════════
class ToolsPanel(Panel):
    def __init__(self):
        super().__init__("TOOLS", "MODULES")

        tools = [
            "VOICE RECOGNITION",
            "TEXT TO SPEECH",
            "INTERNET ACCESS",
            "FILE SYSTEM",
            "COMMAND MODULE",
        ]
        for tool in tools:
            r = QHBoxLayout()
            dot = _lbl("⊙", CYAN_DIM, SIZE_SM, mono=True)
            dot.setFixedWidth(16)
            r.addWidget(dot)
            r.addWidget(_lbl(tool, WHITE_DIM, SIZE_SM, mono=True))
            r.addStretch()
            r.addWidget(_lbl("● ONLINE", GREEN, SIZE_SM, bold=True, mono=True))
            self.addL(r)

        self.addS()


# ══════════════════════════════════════════════════════════════
# SYSTEM LOG
# ══════════════════════════════════════════════════════════════
class LogPanel(Panel):
    def __init__(self):
        super().__init__("LOG", "RT-LOG")
        self._entries = []
        self._lbl = _lbl("", CYAN_DIM, SIZE_SM, mono=True)
        self._lbl.setAlignment(Qt.AlignTop)
        self.add(self._lbl)
        self.addS()
        self.push("System integrity check complete")
        self.push("All subsystems nominal")
        self.push("Awaiting operator input")

    def push(self, msg, color=None):
        ts    = time.strftime("%H:%M:%S")
        entry = (f'<span style="color:{CYAN};">[{ts}]</span> '
                 f'<span style="color:{WHITE};">{msg}</span>')
        self._entries.append(entry)
        if len(self._entries) > 8:
            self._entries.pop(0)
        self._lbl.setText("<br>".join(self._entries))