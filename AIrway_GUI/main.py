from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt
import sys
from pathlib import Path
import flammkuchen as fl
import os

from widgets.table_widget import TableWidget
from widgets.annotate_precise_widget import AnnotatePreciseWidget
from widgets.player_controls import PlayerControls

from helpers.data_handler import DataHandler
from helpers.audio_player import AudioPlayer
from helpers.calculate_md5_hash import get_md5_hash


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

        self.menu_setting = self.menu.addMenu("&Settings")
        # self.menu_setting.addAction("Change window size", )

        # init some variables
        self.data_handler = None
        self.audio_player = None

        self.setGeometry(200, 150, 1300, 800)
        # self.setWindowIcon(QtGui.QIcon(' '))
        self.setWindowTitle("AIrway - Preview, annotate and analyze data")
        self.setWindowIcon(QtGui.QIcon("images/logo.png"))

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
        table_widget = TableWidget(self.audio_player, self.data_handler, self.annotate_precise_widget)
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
        self._ask_save()

        fn = QtWidgets.QFileDialog.getOpenFileName(
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
        self._ask_save()

        fn = QtWidgets.QFileDialog.getOpenFileName(
            directory=str(self.directory) if self.directory else "", filter="*.airway")[0]
        if not fn:
            return

        d_path = Path(fn)
        self.save_path = d_path
        dict_ = fl.load(str(d_path))
        if os.path.exists(dict_['Filename']):
            if get_md5_hash(dict_['Filename']) != dict_['FileHash']:
                self._error_messagebox(f'File with name "{dict_["Filename"]}" is not the same used in "{d_path.name}" '
                                       f'(detected different MD5 hashes).')
                return
            else:
                audio_path = Path(str(d_path.parent) + '/' + dict_['Filename'])
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
        if self.save_path is None:
            fn = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Annotations',
                                                       directory=str(
                                                           self.directory) + '/' + self.filename if self.directory else self.filename,
                                                       filter="*.airway")[0]
            if not fn:
                return
            self.save_path = fn

        print("Saving to: ", self.save_path)
        self.data_handler.save(self.save_path)

        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle('Saving')
        msg.setText(f'Saved annotations to \n "{self.save_path}"')
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setWindowIcon(QtGui.QIcon("images/logo.png"))
        msg.exec_()

    def _close(self):
        self._ask_save()
        self.close()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self._ask_save()

    ##################################################################################
    # Helper
    ##################################################################################

    @staticmethod
    def _error_messagebox(error_msg):
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle('Error')
        msg.setText(error_msg)
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setWindowIcon(QtGui.QIcon("images/logo.png"))
        msg.exec_()

    def _ask_save(self):
        if self.initialized:
            reply = QtWidgets.QMessageBox.question(self, 'Save', 'Do you want to save?',
                                                   QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                   QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
                self._save()

    ##################################################################################
    # Shortcuts
    ##################################################################################

    def init_shortcuts(self):
        keys_and_functions = [(Qt.Key_Return, self._add_event), (Qt.Key_Left, self._previous_event),
                              (Qt.Key_Right, self._next_event), (Qt.Key_P, self._play_region),
                              (Qt.Key_Delete, self._delete_row), ("Ctrl+S", self._save),
                              (Qt.Key_Space, self.player.player_buttons_widget.toggle_play)]

        for (key, function) in keys_and_functions:
            event = QtWidgets.QShortcut(QtGui.QKeySequence(key), self)
            event.activated.connect(function)
            event.setContext(QtCore.Qt.ShortcutContext.WindowShortcut)

        event_keys = [Qt.Key_1, Qt.Key_2, Qt.Key_3, Qt.Key_4, Qt.Key_5, Qt.Key_6, Qt.Key_7,
                      Qt.Key_8, Qt.Key_9, Qt.Key_Q, Qt.Key_S]
        for key in event_keys:
            event = QtWidgets.QShortcut(QtGui.QKeySequence(key), self)
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
        if pressed_key == 'S':
            self.data_handler.add_precise_event(event_idx=8)
        elif pressed_key == 'Q':
            self.data_handler.add_precise_event(event_idx=9)
        else:
            self.data_handler.add_precise_event(event_idx=int(pressed_key) - 1)


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


if __name__ == '__main__':
    sys.excepthook = except_hook
    app = QtWidgets.QApplication([])
    # Force the style to be the same on all OSs:
    app.setStyle("Fusion")
    set_palette(app)
    gui = MainWindow()
    gui.show()
    sys.exit(app.exec_())
