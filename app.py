import sys
from util.controller import Controller as c
from PyQt6.QtWidgets import (QApplication, QWidget, QPushButton,
                             QFileDialog, QVBoxLayout, QLabel)
from PyQt6.QtCore import Qt


class FileUploadWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Upload Example")
        self.setGeometry(100, 100, 400, 200)

        self.upload_button = QPushButton("Upload File", self)
        self.upload_button.clicked.connect(self.open_file_dialog)

        self.file_path_label = QLabel("No file selected", self)
        self.file_path_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.upload_button)
        layout.addWidget(self.file_path_label)
        self.setLayout(layout)

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file_path:
            self.file_path_label.setText(f"Selected file: {file_path}")
            # Further actions with the file can be performed here,
            # such as reading its content or processing it
            users = c.extract_data(file_path)

            c._test_print(users)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FileUploadWindow()
    window.show()
    sys.exit(app.exec())
