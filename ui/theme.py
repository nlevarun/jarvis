# ══════════════════════════════════════════════════════════════
# J.A.R.V.I.S. — Theme
# ══════════════════════════════════════════════════════════════

# Colors
CYAN        = "#00d4ff"
CYAN_DIM    = "#0a8fa8"
CYAN_DARK   = "#0f4a5c"
BG          = "#050d12"
BG_PANEL    = "#070f16"
BORDER      = "#0f4a5c"
WHITE       = "#cceeff"
WHITE_DIM   = "#7aaabb"
GREEN       = "#00ff9f"
GREEN_DIM   = "#007a4a"
AMBER       = "#e8b84b"
RED         = "#ff4455"
BLACK       = "#000000"

# Fonts
FONT_TITLE  = "Helvetica Neue"
FONT_MONO   = "Menlo"
FONT_UI     = "Helvetica Neue"

# Font sizes
SIZE_XS     = 8
SIZE_SM     = 10
SIZE_MD     = 11
SIZE_LG     = 13
SIZE_XL     = 15
SIZE_XXL    = 18
SIZE_HERO   = 26

# Panel style — used everywhere
PANEL_STYLE = f"""
    QWidget {{
        background-color: {BG_PANEL};
        border: 1px solid {BORDER};
        border-radius: 0px;
    }}
"""

# Global app style
APP_STYLE = f"""
    QMainWindow, QWidget {{
        background-color: {BG};
        color: {WHITE};
        font-family: '{FONT_UI}';
    }}
    QLineEdit {{
        background-color: {BG};
        color: {CYAN};
        border: 1px solid {CYAN_DIM};
        border-radius: 0px;
        padding: 10px 16px;
        font-family: '{FONT_MONO}';
        font-size: {SIZE_LG}pt;
        selection-background-color: {CYAN_DARK};
    }}
    QLineEdit:focus {{
        border: 1px solid {CYAN};
    }}
    QScrollBar:vertical {{
        border: none;
        background: {BG};
        width: 6px;
    }}
    QScrollBar::handle:vertical {{
        background: {CYAN_DIM};
        border-radius: 3px;
    }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{ height: 0px; }}
"""