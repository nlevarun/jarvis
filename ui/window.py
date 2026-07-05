import time
import psutil
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                                QHBoxLayout, QLineEdit, QLabel, QSizePolicy)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QObject
from PySide6.QtGui import QFont

from ui.theme import (CYAN, CYAN_DIM, CYAN_DARK, BG, BORDER,
                      WHITE, GREEN, AMBER, APP_STYLE, FONT_MONO)
from ui.background import BackgroundWidget
from ui.reactor import ReactorWidget
from ui.animations import BottomBar
from ui.terminal import TerminalPanel
from ui.panels import (SystemsPanel, NetworkPanel, WorldClockPanel,
                       AIStatusPanel, ToolsPanel, LogPanel)
from ui.widgets import TopBar
from core.ai import ask_with_summary
from core.tts import speak
from core.voice import VoiceListener


# ══════════════════════════════════════════════════════════════
# AI WORKER
# ══════════════════════════════════════════════════════════════
class AIWorker(QObject):
    finished = Signal(str, str, int)  # spoken, full, latency_ms

    def __init__(self, prompt):
        super().__init__()
        self._prompt = prompt

    def run(self):
        t0             = time.time()
        spoken, full   = ask_with_summary(self._prompt)
        ms             = int((time.time() - t0) * 1000)
        self.finished.emit(spoken, full, ms)


# ══════════════════════════════════════════════════════════════
# MAIN WINDOW
# ══════════════════════════════════════════════════════════════
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("J.A.R.V.I.S.")
        self.resize(1680, 960)
        self.setStyleSheet(APP_STYLE)

        self._msg_count = 0
        self._ai_thread = None

        # ── background ───────────────────────────────────────
        self._bg = BackgroundWidget(self)
        self._bg.setGeometry(self.rect())
        self._bg.lower()

        # ── central widget ───────────────────────────────────
        central = QWidget()
        central.setStyleSheet("background: transparent;")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── top bar ──────────────────────────────────────────
        self.topbar = TopBar()
        root.addWidget(self.topbar)

        # ── body ─────────────────────────────────────────────
        body = QHBoxLayout()
        body.setContentsMargins(12, 12, 12, 8)
        body.setSpacing(12)
        root.addLayout(body, 1)

        # ── LEFT COLUMN ──────────────────────────────────────
        left = QVBoxLayout()
        left.setSpacing(10)

        self.systems = SystemsPanel()
        self.network = NetworkPanel()
        self.clock   = WorldClockPanel()

        left.addWidget(self.systems, 4)
        left.addWidget(self.network, 3)
        left.addWidget(self.clock,   2)

        body.addLayout(left, 22)

        # ── CENTER COLUMN ────────────────────────────────────
        center = QVBoxLayout()
        center.setSpacing(10)

        self.reactor = ReactorWidget()
        center.addWidget(self.reactor, 4)

        self.terminal = TerminalPanel()
        center.addWidget(self.terminal, 3)

        # input row
        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        prompt_arrow = QLabel(">")
        prompt_arrow.setFixedWidth(16)
        prompt_arrow.setStyleSheet(
            f"color:{CYAN}; font-family:'{FONT_MONO}'; font-size:12pt;"
            f"background:transparent; border:none;"
        )

        self.prompt = QLineEdit()
        self.prompt.setPlaceholderText("TYPE YOUR COMMAND...")
        self.prompt.returnPressed.connect(self._on_submit)

        enter_lbl = QLabel("PRESS ENTER TO SEND  ↵")
        enter_lbl.setStyleSheet(
            f"color:{CYAN_DIM}; font-family:'{FONT_MONO}'; font-size:7pt;"
            f"background:transparent; border:none;"
        )

        input_row.addWidget(prompt_arrow)
        input_row.addWidget(self.prompt, 1)
        input_row.addWidget(enter_lbl)
        center.addLayout(input_row)

        body.addLayout(center, 36)

        # ── RIGHT COLUMN ─────────────────────────────────────
        right = QVBoxLayout()
        right.setSpacing(10)

        self.ai_status = AIStatusPanel()
        self.tools     = ToolsPanel()
        self.log       = LogPanel()

        right.addWidget(self.ai_status, 4)
        right.addWidget(self.tools,     3)
        right.addWidget(self.log,       3)

        body.addLayout(right, 22)

        # ── bottom bar ───────────────────────────────────────
        self.bottom = BottomBar()
        root.addWidget(self.bottom)

        # ── system stats timer ───────────────────────────────
        self._net_prev_sent = psutil.net_io_counters().bytes_sent
        self._net_prev_recv = psutil.net_io_counters().bytes_recv

        self._stats_timer = QTimer(self)
        self._stats_timer.timeout.connect(self._refresh_stats)
        self._stats_timer.start(1000)
        self._refresh_stats()

        # ── voice listener ───────────────────────────────────
        self._voice = VoiceListener()
        self._voice.wake_word_detected.connect(self._on_wake_word)
        self._voice.command_received.connect(self._on_voice_command)
        self._voice.listening_changed.connect(self.bottom.set_listening)
        self._voice.session_started.connect(self._on_session_start)
        self._voice.session_ended.connect(self._on_session_end)
        self._voice.error.connect(lambda e: self.log.push(f"Voice error: {e}"))
        self._voice.start()

        # ── boot messages ────────────────────────────────────
        self.terminal.push_system("J.A.R.V.I.S. initialized")
        self.terminal.push_system("All systems online")
        self.terminal.push_jarvis(
            "Good evening, sir.\n"
            "All systems are operating within normal parameters.\n"
            "How may I assist you today?"
        )

    # ── resize ───────────────────────────────────────────────
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._bg.setGeometry(self.rect())

    # ── system stats ─────────────────────────────────────────
    def _refresh_stats(self):
        cpu  = psutil.cpu_percent(interval=None)
        ram  = psutil.virtual_memory()
        disk = psutil.disk_usage("/").percent

        c    = psutil.net_io_counters()
        up   = (c.bytes_sent - self._net_prev_sent) / 1024
        dn   = (c.bytes_recv - self._net_prev_recv) / 1024
        net  = up + dn
        self._net_prev_sent = c.bytes_sent
        self._net_prev_recv = c.bytes_recv

        temp = None
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for vals in temps.values():
                    if vals:
                        temp = vals[0].current
                        break
        except Exception:
            pass

        self.systems.refresh(cpu, ram, disk, net, temp)
        self.network.refresh()

    # ── wake word ────────────────────────────────────────────
    def _on_wake_word(self):
        self.terminal.push_system("Wake word detected — listening...")
        self.log.push("Wake word: Hey Jarvis")
        self.reactor.start_thinking()

    # ── voice command ────────────────────────────────────────
    def _on_voice_command(self, text):
        self.prompt.setText(text)
        self._on_submit()

    # ── session start/end ────────────────────────────────────
    def _on_session_start(self):
        self.terminal.push_system("Session active — listening continuously")
        self.log.push("Voice session opened")
        self.bottom.mic_label.setText("● SESSION ACTIVE")
        self.bottom.mic_label.setStyleSheet(
            "color:#00ff9f; font-family:'Menlo'; font-size:8pt;"
            "background:transparent; border:none;"
        )

    def _on_session_end(self):
        self.terminal.push_system("Session closed — say Hey Jarvis to reactivate")
        self.log.push("Voice session closed")
        self.bottom.mic_label.setText("○ AWAITING WAKE WORD")
        self.bottom.mic_label.setStyleSheet(
            f"color:{CYAN_DIM}; font-family:'Menlo'; font-size:8pt;"
            "background:transparent; border:none;"
        )

    # ── text submit ──────────────────────────────────────────
    def _on_submit(self):
        text = self.prompt.text().strip()
        if not text or self._ai_thread is not None:
            return

        self.prompt.clear()
        self._msg_count += 1
        self.ai_status.set_context(self._msg_count)

        self.terminal.push_user(text)
        self.log.push(f"Operator: {text[:40]}")
        self.terminal.set_thinking(True)
        self.reactor.start_thinking()
        self.ai_status.set_status("THINKING", AMBER)

        self._ai_thread = QThread()
        self._ai_worker = AIWorker(text)
        self._ai_worker.moveToThread(self._ai_thread)
        self._ai_thread.started.connect(self._ai_worker.run)
        self._ai_worker.finished.connect(self._on_response)
        self._ai_worker.finished.connect(self._ai_thread.quit)
        self._ai_thread.finished.connect(self._cleanup_thread)
        self._ai_thread.start()

    # ── AI response ──────────────────────────────────────────
    def _on_response(self, spoken, full, ms):
        self.terminal.set_thinking(False)
        self.terminal.push_jarvis(full)
        self.log.push("Response generated.")
        self.ai_status.set_latency(ms)
        self.ai_status.set_status("ONLINE", GREEN)
        self.reactor.start_speaking()

        speak(spoken)

        duration = max(1500, len(spoken.split()) * 400)
        QTimer.singleShot(duration, self.reactor.stop_speaking)

    # ── cleanup ──────────────────────────────────────────────
    def _cleanup_thread(self):
        self._ai_thread = None
        self._ai_worker = None

    def closeEvent(self, event):
        self._voice.stop()
        event.accept()