import psutil

from PySide6.QtCore import Qt, QTimer

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
)

from ui.widgets import TopBar, ArcReactorWidget
from ui.panels import (
    MonitorPanel,
    NetworkPanel,
    LogPanel,
    ActivityPanel,
    SuitPanel,
    VitalSignsPanel,
)

from core.ai import ask
from core.tts import speak


BG = "#050d12"


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("J.A.R.V.I.S.")
        self.resize(1650, 950)

        self.setStyleSheet(f"""
            QMainWindow {{
                background: {BG};
            }}

            QWidget {{
                background: {BG};
            }}
        """)

        # ----------------------------------------------------
        # Central Widget
        # ----------------------------------------------------

        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ----------------------------------------------------
        # Top Bar
        # ----------------------------------------------------

        self.topbar = TopBar()
        root.addWidget(self.topbar)

        # ----------------------------------------------------
        # Main HUD
        # ----------------------------------------------------

        body = QHBoxLayout()
        body.setContentsMargins(14, 14, 14, 14)
        body.setSpacing(14)

        root.addLayout(body)

        # ====================================================
        # LEFT COLUMN
        # ====================================================

        left = QVBoxLayout()
        left.setSpacing(12)

        self.vitals = VitalSignsPanel()
        self.suit = SuitPanel()

        left.addWidget(self.vitals, 3)
        left.addWidget(self.suit, 2)

        body.addLayout(left, 2)

        # ====================================================
        # CENTER
        # ====================================================

        center = QVBoxLayout()
        center.setSpacing(12)

        center.addStretch()

        self.arc = ArcReactorWidget()
        center.addWidget(
            self.arc,
            alignment=Qt.AlignCenter
        )

        center.addStretch()

        self.prompt = QLineEdit()

        self.prompt.setPlaceholderText(
            "Ask J.A.R.V.I.S. anything..."
        )

        self.prompt.returnPressed.connect(
            self.process_prompt
        )

        self.prompt.setStyleSheet("""
            QLineEdit{
                border:1px solid #0a8fa8;
                padding:10px;
                color:white;
                font-size:12pt;
                background:#08141c;
            }
        """)

        center.addWidget(self.prompt)

        body.addLayout(center, 3)

        # ====================================================
        # RIGHT COLUMN
        # ====================================================

        right = QVBoxLayout()
        right.setSpacing(12)

        self.monitor = MonitorPanel()
        self.network = NetworkPanel()
        self.activity = ActivityPanel()

        right.addWidget(self.monitor, 2)
        right.addWidget(self.network, 2)
        right.addWidget(self.activity, 3)

        body.addLayout(right, 2)

        # ----------------------------------------------------
        # Bottom Log
        # ----------------------------------------------------

        self.logs = LogPanel()

        root.addWidget(self.logs)

        # ----------------------------------------------------
        # Timer
        # ----------------------------------------------------

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)

        self.logs.push("J.A.R.V.I.S. initialized.")
        self.logs.push("Systems online.")
        self.logs.push("Awaiting operator.")

        self.refresh()

    # ----------------------------------------------------
    # Refresh system panels
    # ----------------------------------------------------

    def refresh(self):
        """
        Updates all live system information.
        Called once per second.
        """

        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory()

        self.monitor.refresh(cpu, ram)
        self.network.refresh()
        self.vitals.refresh(cpu)

    # ----------------------------------------------------
    # Process a prompt
    # ----------------------------------------------------

    def process_prompt(self):

        prompt = self.prompt.text().strip()

        if not prompt:
            return

        self.prompt.clear()

        # Log user message
        self.logs.push(f"Operator: {prompt}")

        # Show thinking
        self.activity.set_html(
            "<span style='color:#00d4ff;'>Processing...</span>"
        )

        self.repaint()

        try:

            response = ask(prompt)

        except Exception as e:

            response = f"Error:\n\n{e}"

        # Display response
        html = response.replace("\n", "<br>")
        self.activity.set_html(html)

        self.logs.push("Response generated.")

        # Animate Arc Reactor
        self.arc.start_speaking_animation()

        try:
            speak(response)
        except Exception:
            pass

        # crude estimate of speaking time
        duration = max(
            1500,
            len(response.split()) * 350
        )

        QTimer.singleShot(
            duration,
            self.arc.stop_speaking_animation
        )