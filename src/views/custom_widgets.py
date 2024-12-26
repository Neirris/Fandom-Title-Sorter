from PySide6.QtWidgets import QMessageBox, QLabel, QTextEdit, QBoxLayout
from PySide6.QtGui import QTextOption, QFont
from PySide6.QtCore import Qt


class MessageBoxHandler:
    def __init__(self):
        self.error_msg = QMessageBox()
        self.error_msg.setWindowTitle('Ошибка!')
        self.error_msg.setIcon(QMessageBox.Warning)
        self.error_msg.setStandardButtons(QMessageBox.Ok)

    def error_msg_exec(self, text):
        self.error_msg.setText(text)
        label = self.error_msg.findChild(QLabel)
        font = label.font()
        font.setPointSize(16)
        self.error_msg.setFont(font)
        self.error_msg.exec_()


class CustomTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        option = QTextOption()
        option.setWrapMode(QTextOption.NoWrap)
        self.document().setDefaultTextOption(option)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)


class BoxLayout(QBoxLayout):
    def __init__(self, *args, **kwargs):
        super(BoxLayout, self).__init__(*args, **kwargs)
        self.setContentsMargins(1, 1, 1, 1)
        self.setSpacing(1)