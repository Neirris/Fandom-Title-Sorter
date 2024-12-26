from PySide6.QtWidgets import QPushButton, QBoxLayout
from PySide6.QtGui import QIcon, QFont
from PySide6.QtCore import Qt

from views.search_engine_thread import SearchEngineThread
from views.custom_widgets import CustomTextEdit, BoxLayout


class ControlPanel:
    def __init__(self, parent):
        self.parent = parent
        self.output_widget = CustomTextEdit()
        self.progress_bar = CustomTextEdit()
        self.button_start = QPushButton()
        self.button_stop = QPushButton()
        self.button_settings = QPushButton()
        self.initialize_ui()

    def initialize_ui(self):
        self.output_widget.setFont(QFont("Arial", 16))
        self.output_widget.setStyleSheet('background-color: #000000;')
        self.output_widget.setTextColor('#FFFFFF')
        self.output_widget.setReadOnly(True)

        self.progress_bar.setFont(QFont("Arial", 16))
        self.progress_bar.setStyleSheet('background-color: #a9a9a9;')
        self.progress_bar.setTextColor('#000000')
        self.progress_bar.setReadOnly(True)
        self.progress_bar.setFixedHeight(35)

        self.button_start.setIcon(QIcon("src/assets/icons/start.png"))
        self.button_start.setStyleSheet('background-color: #3CB371;')
        self.button_start.clicked.connect(self.start_button_clicked)

        self.button_stop.setIcon(QIcon("src/assets/icons/stop.png"))
        self.button_stop.setStyleSheet('background-color: #FA8072;')
        self.button_stop.clicked.connect(self.stop_button_clicked)

        self.button_settings.setIcon(QIcon("src/assets/icons/settings.png"))
        self.button_settings.setStyleSheet('background-color: #C0C0C0;')
        self.button_settings.clicked.connect(self.parent.open_settings_dialog)

        self.button_start.setEnabled(True)
        self.button_stop.setEnabled(False)

    def setup_right_layout(self, layout_main):
        layout_right = BoxLayout(QBoxLayout.TopToBottom)
        layout_main.addLayout(layout_right, 1)

        layout_right.addWidget(self.output_widget)
        layout_right.addWidget(self.progress_bar, 1)

        box_layout = BoxLayout(QBoxLayout.LeftToRight)
        layout_right.addLayout(box_layout, 1)

        box_layout.addWidget(self.button_settings)
        box_layout.addWidget(self.button_start)
        box_layout.addWidget(self.button_stop)

    def update_text_from_thread(self, text, pb_counter_max):
        self.output_widget.append(text)
        progress_counter = round(self.parent.thread.curr_line / pb_counter_max * 100, 2)
        self.progress_bar.setPlainText(f'[{self.parent.thread.curr_line} / {pb_counter_max}] {progress_counter}%')
        self.progress_bar.setAlignment(Qt.AlignCenter)
        if int(progress_counter) == 100:
            self.stop_button_clicked()

    def set_ui_enabled(self, enabled):
        self.button_start.setEnabled(enabled)
        self.button_stop.setEnabled(not enabled)
        self.button_settings.setEnabled(enabled)
        self.parent.path_manager.path_input.setEnabled(enabled)
        self.parent.path_manager.path_output.setEnabled(enabled)

    def clear_ui_output(self):
        self.output_widget.clear()
        self.progress_bar.clear()

    def validate_paths(self):
        if not self.parent.input_path and not self.parent.output_path:
            self.parent.msgbox_handler.error_msg_exec("Не выбраны пути")
            return False
        if not self.parent.input_path:
            self.parent.msgbox_handler.error_msg_exec("Не выбран путь ввода")
            return False
        if not self.parent.output_path:
            self.parent.msgbox_handler.error_msg_exec("Не выбран путь вывода")
            return False
        return True

    def start_button_clicked(self):
        if not self.validate_paths():
            return

        image_files = self.parent.image_view.get_image_files(self.parent.input_path)
        if not image_files:
            self.parent.msgbox_handler.error_msg_exec("Папка ввода пуста")
            return

        self.parent.thread = SearchEngineThread(
            self.parent.input_path, self.parent.output_path, self.parent.path_dict,
            self.parent.is_sep_chars, self.parent.is_dl_images, parent=self.parent
        )
        self.parent.thread.update_signal.connect(self.update_text_from_thread)
        self.parent.thread.start()

        self.set_ui_enabled(False)
        self.clear_ui_output()

    def stop_button_clicked(self):
        from components.sorter import stop_sort
        stop_sort()
        self.parent.thread.stop()
        self.set_ui_enabled(True)