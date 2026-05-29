"""Quick check: menu bar inside central layout shows a popup. Run from repo root."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QMenuBar, QVBoxLayout, QWidget

from gui.dg_theme import menu_bar_stylesheet, normalize_theme


class T(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Menu test")
        shell = QWidget()
        lay = QVBoxLayout(shell)
        mb = QMenuBar(shell)
        mb.setObjectName("appMenuBar")
        mb.setNativeMenuBar(False)
        m = mb.addMenu("File")
        a = QAction("Hello", self)
        a.triggered.connect(lambda: self.statusBar().showMessage("File menu works", 3000))
        m.addAction(a)
        lay.addWidget(mb)
        lay.addWidget(QLabel("Click File above — status bar should update."))
        self.setCentralWidget(shell)
        self.setStatusBar(self.statusBar() or __import__("PyQt6.QtWidgets", fromlist=["QStatusBar"]).QStatusBar())
        mb.setStyleSheet(menu_bar_stylesheet(normalize_theme("dark")))
        self.menuBar().setVisible(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = T()
    w.resize(480, 120)
    w.show()
    raise SystemExit(app.exec())
