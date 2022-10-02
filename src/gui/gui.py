import sys
from tabnanny import check
import typing

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton


class MainWindow(QMainWindow):
    """
    Main window for gui interface
    """

    def __init__(self) -> None:
        super().__init__()

        self.button_is_checked = True

        self.setWindowTitle("NIR DENTAL IMAGER")

        self.button = QPushButton("Press me!")
        self.button.setCheckable(True)
        self.button.clicked.connect(self.checking_if_checked)
        self.button.setChecked(self.button_is_checked)

        self.setMinimumSize(QSize(400, 300))

        # sets the widget as central
        self.setCentralWidget(self.button)

    def checking_if_checked(self, checked):
        self.button.setText(f"State: {self.button_is_checked}")
        self.button_is_checked = checked


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    app.exec()
