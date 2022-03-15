from PyQt5 import QtWidgets


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

        play_region_button = QtWidgets.QPushButton('(P) - Play/Pause')
        play_region_button.clicked.connect(self.play_region)

        next_event_button = QtWidgets.QPushButton('(->) - Next Event')
        next_event_button.clicked.connect(self.next_event)

        self.container.addWidget(previous_event_button)
        self.container.addWidget(play_region_button)
        self.container.addWidget(next_event_button)
        self.main_layout.addLayout(self.container)

        self.buttons_class_labels = ['(S) - Speech', '(1) - wet cough', '(2) - dry cough', '(3) - throat clearing',
                                     '(4) - dry swallow', '(Q) - Silence', '(5) - wheeze', '(6) - sneeze',
                                     '(7) - short of breath', '(8) - voice quality']

        classes_buttons_layout = QtWidgets.QGridLayout()
        classes_buttons_layout.setSpacing(10)  # No Spacing
        classes_buttons_layout.setContentsMargins(20, 0, 0, 0)
        for x in range(2):
            for y in range(5):
                button = QtWidgets.QPushButton(self.buttons_class_labels[x*5 + y])
                button.setStyleSheet("QPushButton {border-style: outset; border-width: 2px; border-radius: 12px; "
                                     "border-color: black; padding: 4px; background-color: #DBDBDB; color: black}"
                                     "QPushButton::hover {background-color: lightgreen;}"
                                     )
                button.setFixedWidth(170)
                button.setFixedHeight(50)
                button.clicked.connect(self.annotate_event_button_pressed)
                classes_buttons_layout.addWidget(button, x, y)
        self.main_layout.addLayout(classes_buttons_layout)

        self.setLayout(self.main_layout)

    def play_region(self):
        if self._data_handler.play_obj is not None and self._data_handler.play_obj.is_playing():
            self._data_handler.play_obj.stop()
        else:
            self._data_handler.play_selected_region()

    def next_event(self):
        self._data_handler.select_previous_or_next_event(+1)

    def previous_event(self):
        self._data_handler.select_previous_or_next_event(-1)

    def annotate_event_button_pressed(self):
        sender = self.sender()
        event = sender.text()[1]
        if event == 'S':
            event_idx = 8
        elif event == 'Q':
            event_idx = 9
        else:
            event_idx = int(event) - 1

        self._data_handler.add_precise_event(event_idx)
