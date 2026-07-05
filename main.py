import sys
from PySide6.QtWidgets import QApplication
from ui.window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("J.A.R.V.I.S.")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())