from PyQt6.QtWidgets import (
    QWidget, QPushButton,
    QVBoxLayout, QLabel
)

from PyQt6.QtCore import Qt


class Dashboard(QWidget):
    '''
        PyQt6 Widget that will display a breakdown of a specific users'
        hours for the pay period.
    '''

    def __init__(self, log_level):
        super().__init__()
        self.log_level = log_level

        # Title Label
        self.title_label = QLabel("Dashboard", self)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(
            "font-size: 20px; padding: 10px;")

        # Test Button
        self.count = 0
        self.button = QPushButton(f"Click Count: {self.count}", self)
        self.button.clicked.connect(self.count_clicks)

        middle_layout = QVBoxLayout()
        middle_layout.addWidget(self.title_label)
        middle_layout.addWidget(self.button)

        # Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(middle_layout)

        self.setLayout(main_layout)

    def count_clicks(self):
        self.count += 1
        self.button.setText(f"Click Count: {self.count}")
