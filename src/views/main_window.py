import os
import asyncio

from PySide6.QtWidgets import *
from PySide6.QtCore import QThread, Signal, QTimer
from PySide6.QtGui import QPixmap, QFont, QImage, QTextOption, QIcon

from views.settings_manager import SettingsManager, SettingsDialog
from views.custom_widgets import CustomTextEdit, BoxLayout, MessageBoxHandler
from views.path_manager import PathManager
from views.image_view import ImageView
from views.control_panel import ControlPanel
from views.search_engine_thread import SearchEngineThread

from components.sorter import sort_main, stop_sort
from components.file_processing import create_temp_folder, initialize_dict
from config.config import *


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FTS")
        self.settings_manager = SettingsManager()
        self.path_dict = None
        self.checking_images = False
        self.img_rendered = 0

        self.settings_dialog = SettingsDialog(self, self.settings_manager)
        self.path_manager = PathManager(self)
        self.image_view = ImageView(self)
        self.control_panel = ControlPanel(self)
        self.msgbox_handler = MessageBoxHandler()

        self.initialize_ui()
        self.load_settings()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.image_view.check_files)
        self.timer.start(5000)

    def initialize_ui(self):
        self.setGeometry(100, 100, 1400, 800)
        self.setStyleSheet("background-color: #333333;")
        self.setFixedSize(1400, 600)

        layout_main = BoxLayout(QBoxLayout.LeftToRight)
        self.setLayout(layout_main)

        self.path_manager.setup_left_layout(layout_main)
        self.image_view.setup_central_layout(layout_main)
        self.control_panel.setup_right_layout(layout_main)

    def open_settings_dialog(self):
        self.settings_dialog.show()

    def save_settings(self):
        settings_data = {
            "PATH_INPUT": self.path_manager.path_input.text(),
            "PATH_OUTPUT": self.path_manager.path_output.text(),
            "IS_SEP_CHARS": str(self.is_sep_chars),
            "IS_DL_IMAGES": str(self.is_dl_images),
        }
        self.settings_manager.save_settings(settings_data)

    def load_settings(self):
        settings = self.settings_manager.load_settings()
        self.input_path = settings["PATH_INPUT"]
        self.output_path = settings["PATH_OUTPUT"]
        self.path_dict = settings["PATH_DICT"]
        self.is_sep_chars = settings["IS_SEP_CHARS"] == "True"
        self.is_dl_images = settings["IS_DL_IMAGES"] == "True"

        self.path_manager.path_input.setText(self.input_path)
        self.path_manager.path_output.setText(self.output_path)
        self.settings_dialog.checkbox_sep_chars.setChecked(self.is_sep_chars)
        self.settings_dialog.checkbox_dl_images.setChecked(self.is_dl_images)