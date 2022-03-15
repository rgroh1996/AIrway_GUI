from PyQt5 import QtWidgets, Qt

from .player_widgets import PlayerButtonsWidget, PlayerBarWidget


class PlayerControls(QtWidgets.QFrame):
    """
    Class that contains all widgets related to the whole audio/media player.
    """
    def __init__(self, data_handler):
        super().__init__()
        self._data_handler = data_handler
        self._audio_player = self._data_handler.audio_player
        self._init_ui()

        self._audio_player.durationChanged.connect(self.change_file)

    @property
    def audio_player(self):
        return self._audio_player

    def _init_ui(self):
        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # create player buttons
        self.player_buttons_widget = PlayerButtonsWidget(self._data_handler)
        self.main_layout.addWidget(self.player_buttons_widget)

        # create player bar and time labels
        container_layout = QtWidgets.QHBoxLayout()
        self.current_position = QtWidgets.QLabel("00:00")
        container_layout.addWidget(self.current_position)

        player_bar_widget = PlayerBarWidget(self._audio_player)
        player_bar_widget.timestamp_updated.connect(self.current_position.setText)
        container_layout.addWidget(player_bar_widget)

        self.end_position = QtWidgets.QLabel()
        container_layout.addWidget(self.end_position)

        self.main_layout.addLayout(container_layout)
        self.main_layout.addStretch()

        event_button = QtWidgets.QPushButton(' (Enter) - Event')
        event_button.setStyleSheet("QPushButton {border-style: outset; border-width: 2px; border-radius: 12px; "
                                   "border-color: black; padding: 4px; background-color: #DBDBDB; color: black}"
                                   "QPushButton::hover {background-color: yellow;}"
                                   )
        event_button.setFixedWidth(170)
        event_button.setFixedHeight(50)
        event_button.clicked.connect(self.event_button_clicked)
        self.main_layout.addWidget(event_button, alignment=Qt.Qt.AlignHCenter)

        self.main_layout.addStretch()
        self.setLayout(self.main_layout)

    def change_file(self):
        """
        Method updates the end position time label (right to the progress bar) when a new file is loaded.
        """
        duration = int(self._audio_player.duration() / 1000)
        seconds = str(duration % 60)
        minutes = str(duration // 60)
        self.end_position.setText(minutes.zfill(2) + ':' + seconds.zfill(2))

    def event_button_clicked(self):
        """
        Event-method that adds a new 'yellow'-event to the table when clicked.
        """
        self._data_handler.add_event()



