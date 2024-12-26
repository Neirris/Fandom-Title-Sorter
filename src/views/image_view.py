from PySide6.QtWidgets import QScrollArea, QWidget, QGridLayout, QLabel, QBoxLayout
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt, QDir
from views.custom_widgets import BoxLayout
from config.config import valid_extensions
import os


class ImageView:
    def __init__(self, parent):
        self.parent = parent
        self.image_files = []
        self.current_row = 0
        self.img_rendered = 0

    def setup_central_layout(self, layout_main):
        layout_central = BoxLayout(QBoxLayout.TopToBottom)
        layout_main.addLayout(layout_central, 2)

        self.input_scroll = QScrollArea(widgetResizable=True)
        self.input_scroll.setStyleSheet('background-color: #808080;')
        layout_central.addWidget(self.input_scroll, 1)

        self.image_widget = QWidget()
        self.image_widget_layout = QGridLayout(self.image_widget)
        self.input_scroll.setWidget(self.image_widget)

        self.input_scroll.verticalScrollBar().valueChanged.connect(self.scroll_value_changed)

    def scroll_value_changed(self, value):
        scrollbar = self.input_scroll.verticalScrollBar()
        if value >= scrollbar.maximum() - 50:
            self.load_more_images(12)

    def display_images(self, image_files, img_num=12):
        self.image_files = image_files
        self.current_row = 0
        self.clear_image_widgets()
        self.load_more_images(img_num)

    def clear_image_widgets(self):
        for i in reversed(range(self.image_widget_layout.count())):
            widget = self.image_widget_layout.itemAt(i).widget()
            self.image_widget_layout.removeWidget(widget)
            widget.setParent(None)

    def load_more_images(self, img_num):
        self.disconnect_slider_released()

        grid_layout = self.input_scroll.widget().layout()

        for _ in range(img_num):
            if self.current_row < len(self.image_files):
                image_file = self.image_files[self.current_row]
                image = QImage(image_file)
                label = QLabel()
                label.setPixmap(QPixmap.fromImage(image).scaledToWidth(135))
                label.setAlignment(Qt.AlignCenter)
                label.setToolTip(image_file)

                label.mouseDoubleClickEvent = lambda event, file=image_file: self.open_image(event, file)

                grid_layout.addWidget(label, self.current_row // 4, self.current_row % 4)

                self.current_row += 1
        self.img_rendered = len(self.image_widget.findChildren(QLabel))
        self.connect_slider_released()

    def open_image(self, event, image_file):
        if event.button() == Qt.LeftButton and event.modifiers() == Qt.NoModifier:
            os.startfile(image_file)

    def check_files(self):
        if not self.parent.checking_images:
            self.parent.checking_images = True
            self.check_images_presence()

    def check_images_presence(self):
        if not QDir(self.parent.path_manager.path_input.text()).exists():
            return
        current_image_files = self.image_files
        new_image_files = self.get_image_files(self.parent.path_manager.path_input.text())
        if current_image_files != new_image_files:
            self.image_files = new_image_files
            if self.img_rendered <= 12:
                self.img_rendered = 12
            self.display_images(new_image_files, self.img_rendered)
        self.parent.checking_images = False

    def get_image_files(self, directory):
        image_files = []
        for entry in QDir(directory).entryInfoList():
            if entry.isFile():
                file_path = entry.filePath()
                if file_path.lower().endswith(valid_extensions):
                    image_files.append(file_path)
        return image_files

    def disconnect_slider_released(self):
        self.input_scroll.verticalScrollBar().valueChanged.disconnect(self.scroll_value_changed)

    def connect_slider_released(self):
        self.input_scroll.verticalScrollBar().valueChanged.connect(self.scroll_value_changed)