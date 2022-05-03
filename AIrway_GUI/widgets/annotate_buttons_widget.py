from PyQt5 import QtWidgets
import sounddevice as sd


class AnnotateButtonsWidget(QtWidgets.QFrame):
    """
    Class containing all buttons for annotating an event precisely.
    """
    def __init__(self, data_handler):
        super().__init__()
        self._data_handler = data_handler
        self._init_ui()

    def _init_ui(self):
        self.main_layout = QtWidgets.QVBoxLayout()
        self.container = QtWidgets.QHBoxLayout()
        previous_event_button = QtWidgets.QPushButton('(<-) - Previous Event')
        previous_event_button.clicked.connect(self.previous_event)

        play_region_button = QtWidgets.QPushButton('(P) - Play')
        play_region_button.clicked.connect(self.play_region)

        stop_region_button = QtWidgets.QPushButton('Stop')
        stop_region_button.clicked.connect(self.stop_region)

        next_event_button = QtWidgets.QPushButton('(->) - Next Event')
        next_event_button.clicked.connect(self.next_event)

        self.container.addWidget(previous_event_button)
        self.container.addWidget(play_region_button)
        self.container.addWidget(stop_region_button)
        self.container.addWidget(next_event_button)
        self.main_layout.addLayout(self.container)

        self.buttons_class_labels = []
        for shortcut, class_ in zip(self._data_handler.setup['shortcuts'], self._data_handler.setup['classes']):
            self.buttons_class_labels.append(f'({shortcut}) {class_}')

        classes_buttons_layout = QtWidgets.QGridLayout()
        classes_buttons_layout.setSpacing(10)  # No Spacing
        classes_buttons_layout.setContentsMargins(20, 0, 0, 0)
        x = 0
        idx = 0
        while True:
            for y in range(5):
                if idx >= len(self.buttons_class_labels):
                    break
                button = QtWidgets.QPushButton(self.buttons_class_labels[x*5 + y])
                button.setStyleSheet("QPushButton {border-style: outset; border-width: 2px; border-radius: 12px; "
                                     "border-color: black; padding: 4px; background-color: #DBDBDB; color: black}"
                                     "QPushButton::hover {background-color: lightgreen;}"
                                     )
                button.setFixedWidth(170)
                button.setFixedHeight(50)
                button.clicked.connect(self.annotate_event_button_pressed)
                classes_buttons_layout.addWidget(button, x, y)
                idx += 1
            x += 1
            if idx >= len(self.buttons_class_labels):
                break
        self.main_layout.addLayout(classes_buttons_layout)

        self.setLayout(self.main_layout)

    def play_region(self):
        if self._data_handler.play_obj is not None and self._data_handler.play_obj.is_playing():
            self._data_handler.play_obj.stop()
        else:
            self._data_handler.play_selected_region()

    @staticmethod
    def stop_region():
        sd.stop()

    def next_event(self):
        self._data_handler.select_previous_or_next_event(+1)

    def previous_event(self):
        self._data_handler.select_previous_or_next_event(-1)

    def annotate_event_button_pressed(self):
        string = self.sender().text()
        start = string.find("(")
        end = string.find(")")
        pressed_key = string[start+1:end]
        idx = 0
        for shortcut in self._data_handler.setup['shortcuts']:
            if pressed_key == shortcut:
                self._data_handler.add_precise_event(event_idx=idx)
            else:
                idx += 1
