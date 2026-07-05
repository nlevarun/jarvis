from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QSizePolicy
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor

from ui.theme import CYAN, CYAN_DIM, CYAN_DARK, BG, BG_PANEL, BORDER, WHITE, GREEN, AMBER, RED
from ui.animations import ThinkingDots


# ══════════════════════════════════════════════════════════════
# TERMINAL PANEL  — live response chat
# ══════════════════════════════════════════════════════════════
class TerminalPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {BG_PANEL};
                border: 1px solid {BORDER};
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # --- header ---
        header = QWidget()
        header.setFixedHeight(32)
        header.setStyleSheet(f"""
            QWidget {{
                background-color: {CYAN_DARK};
                border: none;
                border-bottom: 1px solid {BORDER};
            }}
        """)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(12, 0, 12, 0)
        h_layout.setSpacing(8)

        arrow = QLabel("◈")
        arrow.setStyleSheet(
            f"color: {CYAN}; font-size: 10pt; background: transparent; border: none;"
        )
        title = QLabel("LIVE RESPONSE // J.A.R.V.I.S.")
        title.setStyleSheet(
            f"color: {CYAN}; font-family: 'Menlo'; font-size: 8pt; "
            f"font-weight: bold; letter-spacing: 2px; "
            f"background: transparent; border: none;"
        )

        self.thinking_dots = ThinkingDots()
        self.status_dot    = QLabel("● READY")
        self.status_dot.setStyleSheet(
            f"color: {GREEN}; font-family: 'Menlo'; font-size: 8pt; "
            f"background: transparent; border: none;"
        )

        h_layout.addWidget(arrow)
        h_layout.addWidget(title)
        h_layout.addStretch()
        h_layout.addWidget(self.thinking_dots)
        h_layout.addWidget(self.status_dot)
        root.addWidget(header)

        # --- scroll area ---
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollBar:vertical {{
                background: {BG};
                width: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: {CYAN_DARK};
            }}
        """)

        self._content = QWidget()
        self._content.setStyleSheet(
            f"background: transparent; border: none;"
        )
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(14, 10, 14, 10)
        self._content_layout.setSpacing(4)
        self._content_layout.addStretch()

        self._scroll.setWidget(self._content)
        root.addWidget(self._scroll, 1)

        # cursor blink
        self._cursor_visible = True
        self._cursor_timer   = QTimer(self)
        self._cursor_timer.timeout.connect(self._blink_cursor)
        self._cursor_timer.start(500)
        self._cursor_label   = None

    # ── public API ────────────────────────────────────────────

    def set_thinking(self, v: bool):
        self.thinking_dots.set_visible(v)
        if v:
            self.status_dot.setText("● THINKING")
            self.status_dot.setStyleSheet(
                f"color: {AMBER}; font-family: 'Menlo'; font-size: 8pt; "
                f"background: transparent; border: none;"
            )
        else:
            self.status_dot.setText("● READY")
            self.status_dot.setStyleSheet(
                f"color: {GREEN}; font-family: 'Menlo'; font-size: 8pt; "
                f"background: transparent; border: none;"
            )

    def push_user(self, text: str):
        """Add a user message line."""
        self._remove_cursor()
        lbl = self._make_line(f"> {text}", CYAN)
        self._insert(lbl)
        self._scroll_to_bottom()

    def push_jarvis(self, text: str):
        """Add Jarvis response lines."""
        self._remove_cursor()
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            lbl = self._make_line(f"> {line}", WHITE)
            self._insert(lbl)
        self._add_cursor()
        self._scroll_to_bottom()

    def push_system(self, text: str, color=None):
        """Add a system message."""
        c   = color or CYAN_DIM
        lbl = self._make_line(f"[ {text} ]", c)
        self._insert(lbl)
        self._scroll_to_bottom()

    def clear(self):
        while self._content_layout.count() > 1:
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # ── internals ─────────────────────────────────────────────

    def _make_line(self, text: str, color: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(
            f"color: {color}; font-family: 'Menlo'; font-size: 9pt; "
            f"background: transparent; border: none; padding: 1px 0;"
        )
        return lbl

    def _insert(self, widget):
        # insert before the stretch at the end
        count = self._content_layout.count()
        self._content_layout.insertWidget(count - 1, widget)

    def _add_cursor(self):
        self._cursor_label = self._make_line("▋", CYAN)
        self._insert(self._cursor_label)

    def _remove_cursor(self):
        if self._cursor_label is not None:
            self._cursor_label.deleteLater()
            self._cursor_label = None

    def _blink_cursor(self):
        if self._cursor_label:
            self._cursor_visible = not self._cursor_visible
            self._cursor_label.setVisible(self._cursor_visible)

    def _scroll_to_bottom(self):
        QTimer.singleShot(
            50,
            lambda: self._scroll.verticalScrollBar().setValue(
                self._scroll.verticalScrollBar().maximum()
            )
        )