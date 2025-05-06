import pyqtgraph as pg
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from util.logger import CLogger

logger = CLogger().get_logger()


class Dashboard(QWidget):
    """
    PyQt6 Widget that will display a breakdown of a specific users'
    hours for the pay period.
    """

    def __init__(self, BUILD):
        super().__init__()

        if BUILD == "DEBUG":
            logger.info("Dashboard: %s", BUILD)

        self.plot_widget = pg.PlotWidget()

        x = [1, 2, 3, 4, 5]
        y = [6, 7, 2, 4, 5]

        self.plot_widget.plot(x, y, pen="r")

        # Title Label
        self.title_label = QLabel("Dashboard", self)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 20px; padding: 10px;")

        # Test Button
        self.count = 0
        self.button = QPushButton(f"Click Count: {self.count}", self)
        self.button.clicked.connect(self.count_clicks)

        middle_layout = QVBoxLayout()
        middle_layout.addWidget(self.title_label)
        middle_layout.addWidget(self.button)
        middle_layout.addWidget(self.plot_widget)

        # Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(middle_layout)

        self.setLayout(main_layout)

    def count_clicks(self):
        self.count += 1
        self.button.setText(f"Click Count: {self.count}")
