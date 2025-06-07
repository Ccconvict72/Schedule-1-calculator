from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QMovie

class LoadingDialog(QDialog):
    cancel_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Please Wait...")
        self.setModal(True)
        self.setFixedSize(300, 200)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.movie = QMovie(resource_path("assets/images/processing.gif"))
        self.label.setMovie(self.movie)
        layout.addWidget(self.label)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self._on_cancel)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)

    def start(self):
        self.movie.start()
        self.show()

    def stop(self):
        self.movie.stop()
        self.accept()  # closes the dialog

    def _on_cancel(self):
        self.cancel_requested.emit()
        self.reject()  # closes the dialog
