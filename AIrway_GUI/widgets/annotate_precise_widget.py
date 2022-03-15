from PyQt5 import QtWidgets
import pyqtgraph as pg
import numpy as np

from .annotate_buttons_widget import AnnotateButtonsWidget


class AnnotatePreciseWidget(QtWidgets.QFrame):
    """
    Class containing everything needed for annotating a region precisely, i.e. selecting the precise event.
    """
    def __init__(self, audio_player, data_handler):
        super().__init__()
        self._audio_player = audio_player
        self._audio_player.positionChanged.connect(self.update_region_from_player)
        self.data_handler = data_handler
        self.data_handler.annotate_precise_widget = self

        self.init_ui()

    def init_ui(self):
        self.main_layout = QtWidgets.QVBoxLayout(self)

        self.plot_widget = pg.GraphicsLayoutWidget()
        self.plot = self.plot_widget.addPlot(row=1, col=0)
        self.data_handler.plot = self.plot
        self.plot.setYRange(-max(self.data_handler.audio_data), max(self.data_handler.audio_data), padding=0)
        self.plot.setMouseEnabled(x=True, y=False)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.plot_widget.setSizePolicy(sizePolicy)
        self.main_layout.addWidget(self.plot_widget)

        # region that can be arbitrarily slided by the user
        self.region = pg.LinearRegionItem()
        self.region.setRegion([0, 20000])
        self.region.setBrush(pg.mkColor((160, 160, 160, 250)))
        self.region.setHoverBrush(pg.mkColor((160, 160, 160, 250)))
        self.data_handler.region = self.region
        self.plot.addItem(self.region, ignoreBounds=True)
        self.region.sigRegionChanged.connect(self.update_region)

        self.annotate_buttons_widget = AnnotateButtonsWidget(self.data_handler)
        self.main_layout.addWidget(self.annotate_buttons_widget)

        self.setLayout(self.main_layout)
        self.pplot = self.plot.plot(np.arange(0, len(self.data_handler.audio_data), 1),
                                    self.data_handler.audio_data, pen=(255, 153, 0))
        range_ = self.plot.getViewBox().viewRange()
        self.plot.getViewBox().setLimits(xMin=range_[0][0], xMax=range_[0][1],
                                         yMin=range_[1][0], yMax=range_[1][1])
        self.plot.setDownsampling(True, True)
        self.plot.setClipToView(True)
        self.plot.hideAxis('left')
        self.plot.hideAxis('bottom')

    def update_region_from_player(self):
        """
        Method called continuously when playing through the media player.
        """
        pos = self._audio_player.position() / 1000 * self.data_handler.audio_rate
        self.region.setRegion([pos - 10000, pos + 10000])

    def update_region(self):
        """
        Method called when changing the region boundaries inside pyqtgraph widget.
        """
        min_x, max_x = self.region.getRegion()
        if min_x < 0:
            min_x = 0
        if max_x > len(self.data_handler.audio_data):
            max_x = len(self.data_handler.audio_data)
        self.region.setRegion([min_x, max_x])

    def play_region(self):
        """
        Event-method called when the user wants to play the currently selected region.
        """
        self.annotate_buttons_widget.play_region()