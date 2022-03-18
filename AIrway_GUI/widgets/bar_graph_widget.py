from PyQt5 import QtWidgets, QtGui, QtCore
import pyqtgraph as pg
import numpy as np


class BarGraphWindow(QtWidgets.QWidget):
    """
    Class containing everything to display how many events were annotated yet.
    """
    def __init__(self, main_window):
        super(BarGraphWindow, self).__init__()
        self.main_window = main_window
        self.flag = 'length'
        self.init_ui()

    def init_ui(self):
        self.main_layout = QtWidgets.QVBoxLayout()

        buttons_layout = QtWidgets.QHBoxLayout()
        self.toggle_plot_button = QtWidgets.QPushButton("Toggle lengths/counts")
        self.toggle_plot_button.clicked.connect(self.toggle_plot_button_clicked)

        self.plot_label = QtWidgets.QLabel('Length')
        self.plot_label.setAlignment(QtCore.Qt.AlignCenter)
        self.plot_label.setStyleSheet("background-color: lightblue; color: black")

        buttons_layout.addWidget(self.toggle_plot_button)
        buttons_layout.addWidget(self.plot_label)
        self.main_layout.addLayout(buttons_layout)

        self.plot_widget = pg.GraphicsLayoutWidget()
        self.y_axis = pg.AxisItem(orientation='left', showValues=True)
        y = self.main_window.data_handler.setup['classes']
        ydict = dict(enumerate(y))
        self.y_axis.setTicks([ydict.items()])

        self.plot = None
        self.reload_graph()

        self.main_layout.addWidget(self.plot_widget)
        self.setLayout(self.main_layout)

    def toggle_plot_button_clicked(self):
        if self.flag == 'count':
            self.flag = 'length'
            self.plot_label.setText('Length')
            self.plot_label.setStyleSheet("background-color: lightblue; color: black")
        else:
            self.flag = 'count'
            self.plot_label.setText('Count')
            self.plot_label.setStyleSheet("background-color: lightgreen; color: black")
        self.reload_graph()

    def reload_graph(self):
        if self.plot is not None:
            self.plot_widget.removeItem(self.plot)

        self.plot = self.plot_widget.addPlot(row=1, col=0, axisItems={'left': self.y_axis})

        x = self.main_window.data_handler.get_bar_graph_data(self.flag)

        if self.flag == 'count':
            self.bar_graph = pg.BarGraphItem(width=x, y=range(len(x)), x0=0, x1=1, height=0.8, brush=QtGui.QColor('lightgreen'))
        else:
            self.bar_graph = pg.BarGraphItem(width=x, y=range(len(x)), x0=0, x1=1, height=0.8, brush=QtGui.QColor('lightblue'))

        self.plot.addItem(self.bar_graph, ignoreBounds=True)

        self.plot.setYRange(-1, 10, padding=0)
        self.plot.setXRange(0, 1, padding=0)
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.hideAxis('bottom')
        view_box = self.plot.getViewBox()
        view_box.setLimits(xMin=0, xMax=1, yMin=-1, yMax=10)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.main_window.close_bar_graph_window()

