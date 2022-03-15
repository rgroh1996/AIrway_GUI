from PyQt5.QtMultimedia import QMediaPlayer, QMediaPlaylist, QMediaContent
from PyQt5 import QtCore


class AudioPlayer(QMediaPlayer):
    def __init__(self, data_handler):
        super().__init__(flags=QMediaPlayer.VideoSurface)
        self.data_handler = data_handler

        self.playlist = QMediaPlaylist()
        content = QMediaContent(QtCore.QUrl.fromLocalFile(str(self.data_handler.path)))
        self.playlist.addMedia(content)
        self.setPlaylist(self.playlist)

        self.setNotifyInterval(20)