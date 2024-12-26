from PySide6.QtWidgets import QDialog, QCheckBox, QVBoxLayout, QPushButton, QFileDialog
from PySide6.QtCore import QSettings

class SettingsManager:
    def __init__(self):
        self.settings = QSettings("Nepkka", "FTS")
        self.SETTINGS_KEYS = {
            "PATH_INPUT": "path_input",
            "PATH_OUTPUT": "path_output",
            "PATH_DICT": "path_dict",
            "IS_SEP_CHARS": "is_sep_chars",
            "IS_DL_IMAGES": "is_dl_images",
        }

    def save_settings(self, data):
        for key, value in data.items():
            self.settings.setValue(self.SETTINGS_KEYS[key], value)

    def load_settings(self):
        default_settings = {
            "PATH_INPUT": "",
            "PATH_OUTPUT": "",
            "PATH_DICT": "",
            "IS_SEP_CHARS": "False",
            "IS_DL_IMAGES": "False",
        }
        return {key: self.settings.value(self.SETTINGS_KEYS[key], default_value) for key, default_value in default_settings.items()}


class SettingsDialog(QDialog):
    def __init__(self, parent, settings_manager):
        super().__init__(parent)
        self.parent = parent
        self.settings_manager = settings_manager
        self.initialize_ui()

    def initialize_ui(self):
        self.setWindowTitle("Настройки")
        self.setFixedSize(300, 200)  # Увеличиваем высоту окна для новой кнопки

        self.setStyleSheet("""
            QCheckBox {
                color: white;
            }
            QPushButton {
                color: white;
            }
        """)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.checkbox_sep_chars = QCheckBox("Отделять персонажей")
        layout.addWidget(self.checkbox_sep_chars)

        self.checkbox_dl_images = QCheckBox("Скачивать HD")
        layout.addWidget(self.checkbox_dl_images)

        self.button_select_dict = QPushButton("Выбрать словарь")
        self.button_select_dict.clicked.connect(self.select_dict)
        layout.addWidget(self.button_select_dict)

        self.button_save = QPushButton("Сохранить")
        self.button_save.clicked.connect(self.save_settings)
        layout.addWidget(self.button_save)

        self.load_settings()

    def select_dict(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Выберите файл словаря", "", "JSON Files (*.json)", options=options)
        if file_name:
            self.settings_manager.save_settings({"PATH_DICT": file_name})

    def save_settings(self):
        settings_data = {
            "IS_SEP_CHARS": str(self.checkbox_sep_chars.isChecked()),
            "IS_DL_IMAGES": str(self.checkbox_dl_images.isChecked()),
        }
        self.settings_manager.save_settings(settings_data)

    def load_settings(self):
        settings = self.settings_manager.load_settings()
        self.checkbox_sep_chars.setChecked(settings["IS_SEP_CHARS"] == "True")
        self.checkbox_dl_images.setChecked(settings["IS_DL_IMAGES"] == "True")