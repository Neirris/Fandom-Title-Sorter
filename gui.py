import os
import asyncio

from PySide6.QtWidgets import *
from PySide6.QtCore import QDir, Qt, QFileInfo, QSettings, QThread, Signal, QTimer
from PySide6.QtGui import QPixmap, QFont, QImage, QTextOption

from sorter import sort_main, stop_sort
from file_processing import create_temp_folder, initialize_dict
from config import *


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)

        self.setWindowTitle("Settings")
        self.setGeometry(200, 200, 300, 200)

        self.layout = QVBoxLayout(self)

        self.checkbox_sep_chars = QCheckBox("Separate Characters")
        self.checkbox_sep_chars.setFont(QFont("Arial", 24))
        self.checkbox_sep_chars.setStyleSheet("color: white;")
        self.layout.addWidget(self.checkbox_sep_chars)

        self.checkbox_dl_images = QCheckBox("Download High-Res Images")
        self.checkbox_dl_images.setFont(QFont("Arial", 24))
        self.checkbox_dl_images.setStyleSheet("color: white;")
        self.layout.addWidget(self.checkbox_dl_images)
        self.checkbox_dl_images.setHidden(True)

        self.button_dict = QPushButton("Select Dictionary")
        self.button_dict.setFont(QFont("Arial", 24))
        self.button_dict.setStyleSheet('background-color: #C0C0C0;')
        self.layout.addWidget(self.button_dict)
        self.button_dict.clicked.connect(self.open_json_dialog)
        
        self.checkbox_sep_chars.stateChanged.connect(self.save_sep_char_settings)
        self.checkbox_dl_images.stateChanged.connect(self.save_dl_img_settings)         
        
        
    def save_sep_char_settings(self):
        self.parent().settings.setValue("is_sep_chars", str(self.checkbox_sep_chars.isChecked()))
        self.parent().is_sep_chars = self.checkbox_sep_chars.isChecked()
          
            
    def save_dl_img_settings(self):
        self.parent().settings.setValue("is_dl_images", str(self.checkbox_dl_images.isChecked()))
        self.parent().is_dl_images = self.checkbox_dl_images.isChecked()
            
               
    def open_json_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        file_dialog = QFileDialog()
        file_dialog.setOptions(options)
        file_dialog.setWindowTitle("Open JSON File")
        file_dialog.setNameFilter("JSON Files (*.json)")
        file_dialog.setFileMode(QFileDialog.ExistingFile)

        if file_dialog.exec_() == QFileDialog.Accepted:
            self.path_dict = file_dialog.selectedFiles()[0]
            self.parent().settings.setValue("path_dict", self.path_dict)     
            
class SearchEngineThread(QThread):
    stopped = Signal(str)
    update_signal = Signal(str, int)

    def __init__(self, path_input, path_output, path_dict, is_sep_chars, is_dl_images, parent=None):
        super(SearchEngineThread, self).__init__(parent)
        self.path_input = path_input
        self.path_output = path_output
        self.path_dict = path_dict
        self.is_sep_chars = is_sep_chars
        self.is_dl_images = is_dl_images
        self.is_running = True
        self.parent_instance = parent
        self.path_error = f'{path_input}\\TEMP_ERROR_IMAGES'
        self.path_temp_images = f'{path_input}\\TEMP_IMAGES'
        self.curr_line = 0
        self.pb_counter = 0

    def run(self):
        create_temp_folder(self.path_error)
        create_temp_folder(self.path_temp_images)
        initialize_dict(self.path_input, self.path_dict)
        self.sort_main_task = asyncio.run(sort_main(self.path_input, self.path_output, self.path_dict, self.is_sep_chars, self.is_dl_images, self))
        

    def stop(self):
        self.is_running = False
        self.wait()
        # delete_empty_folder(self.path_error)  
        # delete_empty_folder(self.path_temp_images)
        
    def update_text(self, text, pb_counter_max):    
        self.curr_line += 1
        self.update_signal.emit(f'{self.curr_line}) {text}', pb_counter_max)


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


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FTS")
        self.settings = QSettings("Nepkka", "FTS")
        
        self.path_dict = None
        self.checking_images = False
        self.img_rendered = 0
        
        self.settings_dialog = SettingsDialog(self)
        self.initialize_ui()
        self.load_settings()
        
        self.timer = QTimer(self) 
        self.timer.timeout.connect(self.check_files)
        self.timer.start(1000) #1000 = 1sec
               
    def initialize_ui(self):
        self.setGeometry(100, 100, 1400, 800)
        self.setStyleSheet("background-color: #333333;")
        self.setFixedSize(1400, 600)

        self.msgbox_handler()

        layout_main = BoxLayout(QBoxLayout.LeftToRight)
        self.setLayout(layout_main)

        self.setup_left_layout(layout_main)
        self.setup_central_layout(layout_main)
        self.setup_right_layout(layout_main)
        
        
    def open_settings_dialog(self):
        self.settings_dialog.show()
        
        
    def save_settings(self):
        self.settings.setValue("path_input", self.path_input.text())
        self.settings.setValue("path_output", self.path_output.text())


    def load_settings(self):
        self.input_path = self.settings.value("path_input", "")
        self.output_path = self.settings.value("path_output", "")
        self.path_input.setText(self.input_path)
        self.path_output.setText(self.output_path)
        self.path_dict = self.settings.value("path_dict", "")
        self.path_input.editingFinished.emit()
        self.path_output.editingFinished.emit()
        
        if self.settings.value("is_sep_chars") is None:
            self.settings.setValue("is_sep_chars", "False")
            
        if self.settings.value("is_dl_images") is None:
            self.settings.setValue("is_dl_images", "False")

        self.is_sep_chars = self.settings.value("is_sep_chars") == "True"
        self.is_dl_images = self.settings.value("is_dl_images") == "True"
                     
        self.settings_dialog.checkbox_sep_chars.setChecked(self.is_sep_chars)
        self.settings_dialog.checkbox_dl_images.setChecked(self.is_dl_images)
        
        
    def setup_left_layout(self, layout_main):
        layout_left = BoxLayout(QBoxLayout.TopToBottom)
        layout_main.addLayout(layout_left, 1)

        self.path_input, self.path_input_label, self.tree_view_widget_input = self.create_file_explorer_widget("Input Folder:")
        layout_left.addWidget(self.path_input_label, 0)
        layout_left.addWidget(self.path_input, 1)
        layout_left.addWidget(self.tree_view_widget_input, 2)

        self.path_output, self.path_output_label, self.tree_view_widget_output = self.create_file_explorer_widget("Output Folder:")
        layout_left.addWidget(self.path_output_label, 0)
        layout_left.addWidget(self.path_output, 1)
        layout_left.addWidget(self.tree_view_widget_output, 2)
        self.path_output.editingFinished.connect(lambda: self.update_tree_path(self.path_output))


    def setup_central_layout(self, layout_main):
        layout_central = BoxLayout(QBoxLayout.TopToBottom)
        layout_main.addLayout(layout_central, 2)

        self.input_scroll = QScrollArea(widgetResizable=True)
        self.input_scroll.setStyleSheet('background-color: #808080;')
        layout_central.addWidget(self.input_scroll, 1)

        self.image_widget = QWidget()
        self.image_widget_layout = QGridLayout(self.image_widget)
        self.input_scroll.setWidget(self.image_widget)

        self.image_files = []
        self.current_row = 0

        self.input_scroll.verticalScrollBar().valueChanged.connect(self.scroll_value_changed)
           

    def setup_right_layout(self, layout_main):
        layout_right = BoxLayout(QBoxLayout.TopToBottom)
        layout_main.addLayout(layout_right, 1)
        self.rr = layout_right
        
        self.output_widget = CustomTextEdit()
        self.output_widget.setFont(QFont("Arial", 16))
        self.output_widget.setStyleSheet('background-color: #000000;')
        self.output_widget.setTextColor('#FFFFFF')
        self.output_widget.setReadOnly(True)
        layout_right.addWidget(self.output_widget)      

        self.progress_bar = CustomTextEdit()
        self.progress_bar.setFont(QFont("Arial", 16))
        self.progress_bar.setStyleSheet('background-color: #a9a9a9;')
        self.progress_bar.setTextColor('#000000')
        self.progress_bar.setReadOnly(True)
        self.progress_bar.setFixedHeight(35)
        layout_right.addWidget(self.progress_bar, 1)

        box_layout = BoxLayout(QBoxLayout.LeftToRight)
        layout_right.addLayout(box_layout, 1)

        self.button_settings = QPushButton("⚙️")
        self.button_settings.setFont(QFont("Arial", 24))
        self.button_settings.setStyleSheet('background-color: #C0C0C0;')
        box_layout.addWidget(self.button_settings)
        self.button_settings.clicked.connect(self.open_settings_dialog)

        self.button_start = QPushButton("▶️")
        self.button_start.setFont(QFont("Arial", 24))
        self.button_start.setStyleSheet('background-color: #3CB371;')
        box_layout.addWidget(self.button_start)
        self.button_start.clicked.connect(self.start_button_clicked)

        self.button_stop = QPushButton("🛑")
        self.button_stop.setFont(QFont("Arial", 24))
        self.button_stop.setStyleSheet('background-color: #FA8072;')
        box_layout.addWidget(self.button_stop)
        self.button_stop.clicked.connect(self.stop_button_clicked)

        self.button_start.setEnabled(True)
        self.button_stop.setEnabled(False)
        
    def update_text_from_thread(self, text, pb_counter_max):
        self.output_widget.append(text)
        progress_counter = round(self.thread.curr_line/pb_counter_max*100, 2) 
        self.progress_bar.setPlainText(f'[{self.thread.curr_line} / {pb_counter_max}] {progress_counter}%')
        self.progress_bar.setAlignment(Qt.AlignCenter)           
        if int(progress_counter) == 100:
            self.stop_button_clicked()
       
            
    def disconnect_slider_released(self):
        self.input_scroll.verticalScrollBar().valueChanged.disconnect(self.scroll_value_changed)


    def connect_slider_released(self):
        self.input_scroll.verticalScrollBar().valueChanged.connect(self.scroll_value_changed)


    def scroll_value_changed(self, value):
        scrollbar = self.input_scroll.verticalScrollBar()
        if value >= scrollbar.maximum() - 50:
            self.load_more_images(12)   


    def start_button_clicked(self):
        if not self.input_path and not self.output_path:
            self.error_msg_exec("No Paths Selected")
        if not self.input_path:
            self.error_msg_exec("No Input Path")
        if not self.output_path:
            self.error_msg_exec("No Output Path")
        else:
            image_files = self.get_image_files(self.input_path)
            if not image_files:
                self.error_msg_exec("Input Folder is Empty")
            else:  
                self.thread = SearchEngineThread(self.input_path, self.output_path, self.path_dict, self.is_sep_chars, self.is_dl_images, parent=self)
                self.thread.update_signal.connect(self.update_text_from_thread)
                self.thread.start()
                
                self.button_start.setDisabled(True)
                self.button_stop.setEnabled(True)
                self.button_settings.setDisabled(True)           
                self.path_input.setDisabled(True)     
                self.tree_view_widget_input.setDisabled(True)     
                self.path_output.setDisabled(True)     
                self.tree_view_widget_output.setDisabled(True)    
                
                self.output_widget.clear()
                self.progress_bar.clear() 
             
                
    def stop_button_clicked(self):
        stop_sort()
        self.thread.stop()
        self.button_stop.setDisabled(True)
        self.button_start.setEnabled(True)
        self.button_settings.setEnabled(True)
        self.path_input.setEnabled(True)     
        self.tree_view_widget_input.setEnabled(True)     
        self.path_output.setEnabled(True)     
        self.tree_view_widget_output.setEnabled(True)     


    def create_file_explorer_widget(self, label_text):
        path_text_label = QLabel(label_text)
        path_text_label.setFixedHeight(20)
        path_text_label.setStyleSheet('background-color: #C0C0C0; padding-left: 5px;')

        path_text_input = QLineEdit()
        path_text_input.setStyleSheet('background-color: #C0C0C0;')
        path_text_input.editingFinished.connect(lambda: self.update_tree_path(path_text_input))

        tree_view_widget = QWidget()
        tree_view_widget.setStyleSheet('background-color: #C0C0C0;')

        tree_view = QTreeView()
        tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        tree_view.doubleClicked.connect(lambda index: self.handle_double_click(index, path_text_input))

        model = QFileSystemModel()
        model.setRootPath(QDir.rootPath())
        model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot)
        tree_view.setModel(model)
        tree_view.setRootIndex(model.index(''))

        for column in range(model.columnCount()):
            if model.headerData(column, Qt.Horizontal) != "Name":
                tree_view.setColumnHidden(column, True)
        tree_view.header().setHidden(True)

        tree_view_widget_layout = QVBoxLayout(tree_view_widget)
        tree_view_widget_layout.addWidget(tree_view, 1)

        return path_text_input, path_text_label, tree_view_widget


    def update_tree_path(self, path_type):
        path = path_type.text()
        label = path_type.previousInFocusChain()

        if label.text() == "Input Folder:":
            if not QDir(path).exists():
                self.error_msg_exec('Incorrect Path')
            else:
                tree_view_widget = path_type.nextInFocusChain()
                tree_view = tree_view_widget.findChild(QTreeView)
                model = tree_view.model()
                tree_view.setRootIndex(model.index(path))

                if label.text() == "Input Folder:":
                    image_files = self.get_image_files(path)
                    self.input_path = path
                    if image_files:
                        self.display_images(image_files)
        elif label.text() == "Output Folder:":
            if not QDir(path).exists():
                self.error_msg_exec('Incorrect Path')
            else:
                tree_view_widget = path_type.nextInFocusChain()
                tree_view = tree_view_widget.findChild(QTreeView)
                model = tree_view.model()
                tree_view.setRootIndex(model.index(path))
                self.output_path = path
        self.save_settings()
        
        
    def handle_double_click(self, index, path_input):
        file_info = QFileInfo(index.model().filePath(index))
        if file_info.isDir():
            path = file_info.filePath()
            path_input.setText(path)
            self.update_tree_path(path_input)
      
            
    def get_image_files(self, directory):
        image_files = []
        for entry in QDir(directory).entryInfoList():
            if entry.isFile():
                file_path = entry.filePath()
                if file_path.lower().endswith(valid_extensions):
                    image_files.append(file_path)

        return image_files
  
  
    def open_image(self, event, image_file):
        if event.button() == Qt.LeftButton and event.modifiers() == Qt.NoModifier:
            os.startfile(image_file)
         
            
    def display_images(self, image_files, img_num = 12):
        self.image_files = image_files
        self.current_row = 0
        self.clear_image_widgets()
        self.load_more_images(img_num)


    def clear_image_widgets(self):
        for i in reversed(range(self.image_widget_layout.count())):
            widget = self.image_widget_layout.itemAt(i).widget()
            self.image_widget_layout.removeWidget(widget)
            widget.setParent(None)
         
            
    def check_files(self):
        if not self.checking_images:
            self.checking_images = True
            self.check_images_presence()                           
          
           
    def check_images_presence(self):
        if not QDir(self.path_input.text()).exists():
            return
        current_image_files = self.image_files
        new_image_files = self.get_image_files(self.path_input.text())                    
        if current_image_files != new_image_files:
            self.image_files = new_image_files
            if self.img_rendered <= 12:
                self.img_rendered = 12
            self.display_images(new_image_files, self.img_rendered)
        self.checking_images = False


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
        

    def msgbox_handler(self):
        self.error_msg = QMessageBox()
        self.error_msg.setWindowTitle('Error!')
        self.error_msg.setIcon(QMessageBox.Warning)
        self.error_msg.setStandardButtons(QMessageBox.Ok)

    def error_msg_exec(self, text):
        self.error_msg.setText(text)
        label = self.error_msg.findChild(QLabel)
        font = label.font()
        font.setPointSize(16)
        self.error_msg.setFont(font)
        self.error_msg.exec_()
        