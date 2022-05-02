from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt
import sys
from pathlib import Path
import flammkuchen as fl
import os
from datetime import datetime

from .widgets.table_widget import TableWidget
from .widgets.annotate_precise_widget import AnnotatePreciseWidget
from .widgets.player_controls import PlayerControls
from .widgets.bar_graph_widget import BarGraphWindow

from .helpers.data_handler import DataHandler
from .helpers.audio_player import AudioPlayer
from .helpers.calculate_md5_hash import get_md5_hash


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.directory = None
        self.filename = None
        self.initialized = False
        self.save_path = None

        # open dialog to find out if the user wants to load new data or continue on previous loaded data
        self.menu = self.menuBar()
        self.menu_file = self.menu.addMenu("&File")
        self.menu_file.addAction("Import (.wav)", self._import)
        self.menu_file.addAction("Open (.airway)", self._open)
        self.menu_file.addAction("Save", self._save)
        self.menu_file.addAction("Close/Exit", self._close)

        self.menu_extras = self.menu.addMenu("&Extras")
        self.bar_graph_action = QtWidgets.QAction("Show Bar Graph", self)
        self.bar_graph_action.triggered.connect(self._open_bar_graph_window)
        self.bar_graph_action.setCheckable(True)
        self.menu_extras.addAction(self.bar_graph_action)

        self.menu_extras.addAction("Export Annotations (.csv)", self._export_annotated_events_csv)
        self.menu_extras.addAction("Export Annotations (.wav)", self._export_annotated_events_wav)

        # variables for "Extras" menu point
        self.bar_graph_window = None

        # init some variables
        self.data_handler = None
        self.audio_player = None

        self.setGeometry(200, 150, 1300, 800)
        # self.setWindowIcon(QtGui.QIcon(' '))
        self.setWindowTitle("AIrway - Preview, annotate and analyze data")
        p_ = os.path.dirname(os.path.realpath(__file__))
        self.setWindowIcon(QtGui.QIcon(p_ + "/images/logo.png"))

    def _init_ui(self):
        # create main layouts/widgets
        self.main_widget = QtWidgets.QWidget()
        self.main_layout = QtWidgets.QGridLayout()

        self.audio_player = AudioPlayer(self.data_handler)
        self.data_handler.audio_player = self.audio_player

        # add player buttons/player bar/volume widget
        self.player = PlayerControls(self.data_handler)
        self.main_layout.addWidget(self.player, 0, 0, 1, 1)

        # add annotate precise widget
        self.annotate_precise_widget = AnnotatePreciseWidget(self.audio_player, self.data_handler)
        self.main_layout.addWidget(self.annotate_precise_widget, 1, 0, 1, 1)

        # add table widget
        table_widget = TableWidget(self.audio_player, self.data_handler, self.annotate_precise_widget, self)
        self.data_handler.table_widget = table_widget
        self.main_layout.addWidget(table_widget, 0, 1, 3, 1)

        if self.initialized is False:
            self.init_shortcuts()

        # finally, add main_layout to the main_widget
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)

    ##################################################################################
    # Menu controls
    ##################################################################################

    def _import(self):
        if self._ask_save() is False:
            return

        fn = QtWidgets.QFileDialog.getOpenFileName(self, "Import and load new .wav file",
            directory=str(self.directory) if self.directory else "", filter="*.wav")[0]
        if not fn:
            return

        path = Path(fn)
        self.directory = path.parent
        self.filename = path.stem

        if self.initialized is False:
            self.data_handler = DataHandler(path)
            self._init_ui()
            self.initialized = True
        else:
            self.save_path = None
            for i in reversed(range(self.main_layout.count())):
                self.main_layout.itemAt(i).widget().setParent(None)
            self.data_handler = DataHandler(path)
            self._init_ui()

    def _open(self):
        if self._ask_save() is False:
            return

        fn = QtWidgets.QFileDialog.getOpenFileName(self, "Open and load new .airway file",
            directory=str(self.directory) if self.directory else "", filter="*.airway")[0]
        if not fn:
            return

        d_path = Path(fn)
        self.save_path = d_path
        self.directory = d_path.parent
        self.filename = d_path.stem
        dict_ = fl.load(str(d_path))
        wav_file_path = str(d_path.parent) + '/' + dict_['Filename']
        if os.path.exists(wav_file_path):
            if get_md5_hash(wav_file_path) != dict_['FileHash']:
                self._error_messagebox(f'File with name "{dict_["Filename"]}" is not the same used in "{d_path.name}" '
                                       f'(detected different MD5 hashes).')
                return
            else:
                audio_path = Path(wav_file_path)
        else:
            self._error_messagebox(f'Corresponding filename "{dict_["Filename"]}" not found. '
                                   f'Please make sure it is in the same directory as "{d_path.name}".')
            return

        if self.initialized is False:
            self.data_handler = DataHandler(audio_path)
            self._init_ui()
            self.data_handler.load_annotations(dict_)
            self.initialized = True
        else:
            self.save_path = None
            for i in reversed(range(self.main_layout.count())):
                self.main_layout.itemAt(i).widget().setParent(None)
            self.data_handler = DataHandler(audio_path)
            self._init_ui()
            self.data_handler.load_annotations(dict_)

    def _save(self):
        if self.initialized is False:
            self._error_messagebox("Please load and annotate data first.")
            self.bar_graph_action.setChecked(False)
            return

        if self.save_path is None:
            fn = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Annotations',
                                                       directory=str(
                                                           self.directory) + '/' + self.filename if self.directory else self.filename,
                                                       filter="*.airway")[0]
            if not fn:
                return False
            self.save_path = fn
        else:
            reply = QtWidgets.QMessageBox.question(self, 'Save', f'Save to file {Path(self.save_path).name}?',
                                                   QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                   QtWidgets.QMessageBox.Yes)
            if reply == QtWidgets.QMessageBox.No:
                fn = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Annotations',
                                                           directory=str(
                                                               self.directory) + '/' + self.filename if self.directory else self.filename,
                                                           filter="*.airway")[0]
                if not fn:
                    return False
                self.save_path = fn
        self.data_handler.save(self.save_path)
        self.saving_successful_messagebox(self.save_path)
        return True

    def _close(self):
        self.close_bar_graph_window()
        if not self._ask_save():
            return
        self.close()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.close_bar_graph_window()
        if not self._ask_save():
            a0.ignore()

    ##################################################################################
    # Extras
    ##################################################################################
    def _open_bar_graph_window(self):
        if self.initialized is False:
            self._error_messagebox("Please load data first.")
            self.bar_graph_action.setChecked(False)
            return

        if self.bar_graph_window is None:
            self.bar_graph_action.setChecked(True)
            self.bar_graph_window = BarGraphWindow(self)
            self.bar_graph_window.setFixedSize(400, 300)
            self.bar_graph_window.setWindowTitle("AIrway")
            self.bar_graph_window.setWindowIcon(QtGui.QIcon("AIrway_GUI/images/logo.png"))
            self.bar_graph_window.show()
        else:
            self.close_bar_graph_window()

    def close_bar_graph_window(self):
        if self.bar_graph_window is not None:
            self.bar_graph_action.setChecked(False)
            self.bar_graph_window.close()
            self.bar_graph_window = None

    def update_bar_graph_window(self):
        if self.bar_graph_window is not None:
            self.bar_graph_window.reload_graph()

    def _export_annotated_events_csv(self):
        if self.initialized is False:
            self._error_messagebox("Please load data first.")
            self.bar_graph_action.setChecked(False)
            return

        fn = QtWidgets.QFileDialog.getSaveFileName(self, 'Export Annotations as .csv',
                                                   directory=str(
                                                       self.directory) + '/' + self.filename if self.directory else self.filename,
                                                   filter="*.csv")[0]
        if not fn:
            return
        # save all events to the created folder
        self.data_handler.save_annotated_events_csv(fn)
        self.saving_successful_messagebox(fn)

    def _export_annotated_events_wav(self):
        if self.initialized is False:
            self._error_messagebox("Please load data first.")
            self.bar_graph_action.setChecked(False)
            return

        fn = QtWidgets.QFileDialog.getExistingDirectory(self, 'Export Annotations as .wav',
                                                        directory=str(self.directory) if self.directory else "")
        if not fn:
            return
        # create new folder
        folder_name = "Annotated_Events_" + str(datetime.now().strftime("%d%m%Y_%H%M%S"))
        path = os.path.join(fn, folder_name)
        os.mkdir(path)
        # save all events to the created folder
        self.data_handler.save_annotated_events_wav(path)
        self.saving_successful_messagebox(path)

    @staticmethod
    def saving_successful_messagebox(path):
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle('Saving')
        msg.setText(f'Saved annotations to \n "{path}"')
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setWindowIcon(QtGui.QIcon("AIrway_GUI/images/logo.png"))
        msg.exec_()

    ##################################################################################
    # Helper
    ##################################################################################

    @staticmethod
    def _error_messagebox(error_msg):
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle('Error')
        msg.setText(error_msg)
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setWindowIcon(QtGui.QIcon("AIrway_GUI/images/logo.png"))
        msg.exec_()

    def _ask_save(self):
        if self.initialized:
            reply = QtWidgets.QMessageBox.question(self, 'Save', 'Do you want to save?',
                                                   QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel,
                                                   QtWidgets.QMessageBox.Yes)
            if reply == QtWidgets.QMessageBox.Yes:
                return self._save()
            elif reply == QtWidgets.QMessageBox.Cancel:
                return False
            elif reply == QtWidgets.QMessageBox.No:
                reply = QtWidgets.QMessageBox.question(self, 'Save', 'Are you sure that you want to close without '
                                                                     'saving? (Unsaved content will get lost!)',
                                                       QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                       QtWidgets.QMessageBox.No)
                if reply == QtWidgets.QMessageBox.No:
                    return False
        return True

    ##################################################################################
    # Shortcuts
    ##################################################################################

    def init_shortcuts(self):
        keys_and_functions = [(Qt.Key_Return, self._add_event), (Qt.Key_Left, self._previous_event),
                              (Qt.Key_Right, self._next_event), (Qt.Key_P, self._play_region),
                              (Qt.Key_Delete, self._delete_row), (Qt.Key_Backspace, self._delete_row),
                              ("Ctrl+S", self._save), (Qt.Key_Space, self.player.player_buttons_widget.toggle_play)]

        for (key, function) in keys_and_functions:
            event = QtWidgets.QShortcut(QtGui.QKeySequence(key), self)
            event.activated.connect(function)
            event.setContext(QtCore.Qt.ShortcutContext.WindowShortcut)

        # add shortcuts defined in setup.json to GUI
        for shortcut in self.data_handler.setup['shortcuts']:
            event = QtWidgets.QShortcut(QtGui.QKeySequence(shortcut), self)
            event.activated.connect(self._add_precise_event)
            event.setContext(QtCore.Qt.ShortcutContext.WindowShortcut)

    def _add_event(self):
        self.data_handler.add_event()

    def _delete_row(self):
        self.data_handler.delete_selected_row()

    def _play_region(self):
        self.annotate_precise_widget.play_region()

    def _previous_event(self):
        self.data_handler.select_previous_or_next_event(-1)

    def _next_event(self):
        self.data_handler.select_previous_or_next_event(+1)

    def _add_precise_event(self):
        pressed_key = self.sender().key().toString()
        idx = 0
        for shortcut in self.data_handler.setup['shortcuts']:
            if pressed_key == shortcut:
                self.data_handler.add_precise_event(event_idx=idx)
            else:
                idx += 1


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


def set_palette(app_):
    """
    Method uses a Palette to change the whole window style to dark mode.
    """
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.black)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app_.setPalette(palette)


def main():
    sys.excepthook = except_hook
    app = QtWidgets.QApplication([])
    # Force the style to be the same on all OSs:
    app.setStyle("Fusion")
    set_palette(app)
    gui = MainWindow()
    gui.show()
    exit_code = app.exec()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
