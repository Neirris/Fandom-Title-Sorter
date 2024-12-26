from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton, QHBoxLayout, QFileDialog, QVBoxLayout, QBoxLayout
from PySide6.QtGui import QIcon
from views.custom_widgets import BoxLayout

class PathManager:
    def __init__(self, parent):
        self.parent = parent

    def setup_left_layout(self, layout_main):
        layout_left = BoxLayout(QBoxLayout.TopToBottom)
        layout_main.addLayout(layout_left, 1)

        layout_input = QVBoxLayout()
        layout_input.setSpacing(5) 

        self.path_input_label = QLabel("Папка ввода:")
        self.path_input_label.setFixedHeight(20)
        self.path_input_label.setStyleSheet('background-color: #C0C0C0; padding-left: 5px;')
        layout_input.addWidget(self.path_input_label)

        self.path_input = QLineEdit()
        self.path_input.setStyleSheet('background-color: #C0C0C0;')
        self.path_input.setReadOnly(True)
        layout_input.addWidget(self.path_input)

        self.button_input = QPushButton("Открыть папку ввода")
        self.button_input.setStyleSheet('background-color: #C0C0C0;')
        self.button_input.clicked.connect(self.open_input_folder)
        layout_input.addWidget(self.button_input)

        layout_left.addLayout(layout_input)

        layout_output = QVBoxLayout()
        layout_output.setSpacing(5) 

        self.path_output_label = QLabel("Папка вывода:")
        self.path_output_label.setFixedHeight(20)
        self.path_output_label.setStyleSheet('background-color: #C0C0C0; padding-left: 5px;')
        layout_output.addWidget(self.path_output_label)

        self.path_output = QLineEdit()
        self.path_output.setStyleSheet('background-color: #C0C0C0;')
        self.path_output.setReadOnly(True)
        layout_output.addWidget(self.path_output)

        self.button_output = QPushButton("Открыть папку вывода")
        self.button_output.setStyleSheet('background-color: #C0C0C0;')
        self.button_output.clicked.connect(self.open_output_folder)
        layout_output.addWidget(self.button_output)

        layout_left.addLayout(layout_output)

    def open_input_folder(self):
        folder = QFileDialog.getExistingDirectory(self.parent, "Выбрать папку ввода")
        if folder:
            self.path_input.setText(folder)
            self.parent.input_path = folder
            self.parent.save_settings()
            image_files = self.parent.image_view.get_image_files(folder)
            if image_files:
                self.parent.image_view.display_images(image_files)

    def open_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self.parent, "Выбрать папку вывода")
        if folder:
            self.path_output.setText(folder)
            self.parent.output_path = folder
            self.parent.save_settings()

    def clear_input_path(self):
        self.path_input.clear()
        self.parent.input_path = ""
        self.parent.save_settings()

    def clear_output_path(self):
        self.path_output.clear()
        self.parent.output_path = ""
        self.parent.save_settings()