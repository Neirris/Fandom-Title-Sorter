import asyncio
from PySide6.QtCore import QThread, Signal

from components.sorter import sort_main, stop_sort
from components.file_processing import create_temp_folder, initialize_dict


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
        self.sort_main_task = asyncio.run(
            sort_main(self.path_input, self.path_output, self.path_dict, self.is_sep_chars, self.is_dl_images, self)
        )

    def stop(self):
        self.is_running = False
        self.wait()

    def update_text(self, text, pb_counter_max):
        self.curr_line += 1
        self.update_signal.emit(f'{self.curr_line}) {text}', pb_counter_max)