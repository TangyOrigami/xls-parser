from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QComboBox, QLineEdit


class SearchableComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.lineEdit().textEdited.connect(self.filter_items)
        self.original_items = []

    def addItems(self, items):
        self.original_items.extend(items)
        super().addItems(items)

    def showPopup(self):
        self.filter_items(self.lineEdit().text())
        super().showPopup()

    def filter_items(self, text):
        self.clear()
        if text:
            filtered_items = [
                item for item in self.original_items if text.lower() in item.lower()
            ]
            super().addItems(filtered_items)
        else:
            super().addItems(self.original_items)
        self.setCurrentIndex(-1)
