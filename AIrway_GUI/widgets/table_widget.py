from PyQt5 import QtWidgets, QtGui, QtCore
import pyqtgraph as pg
import datetime


class TableWidget(QtWidgets.QWidget):
    """
    Class containing everything for displaying annotated events inside a TableWidget.
    """
    def __init__(self, audio_player, data_handler, annotate_precise_widget, main_window):
        super().__init__()
        self._audio_player = audio_player
        self._data_handler = data_handler
        self.annotate_precise_widget = annotate_precise_widget
        self.main_window = main_window

        self.main_layout = QtWidgets.QVBoxLayout()

        self.table = QtWidgets.QTableWidget()
        self.table.setMinimumWidth(500)
        self.table.setMaximumWidth(1000)
        self.table.setColumnCount(4)
        self.table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.table.setHorizontalHeaderLabels([" ", "From", "To", "Event"])
        self.table.cellClicked.connect(self._select_row)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # configure header
        self.table.setColumnWidth(0, 1)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 200)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Fixed)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.Fixed)

        self._data_handler.table_widget = self.table
        self.main_layout.addWidget(self.table)

        delete_button = QtWidgets.QPushButton('(Del) - Delete selected row')
        delete_button.clicked.connect(self._delete_selected_row)
        self.main_layout.addWidget(delete_button)
        self.setLayout(self.main_layout)

    def _select_row(self):
        """
        Event-method when selecting a row (i.e. when clicking on the row)
        """
        if len(self.table.selectedIndexes()):
            # Get current row
            row = self.table.selectedIndexes()[0].row()
            self.select_row(row)

    def select_row(self, row):
        """
        Method for selecting a specific row depending on the row index.
        """
        if self._audio_player.state() == self._audio_player.PlayingState:
            return
        else:
            df = self._data_handler.table_data
            if bool(df.loc[row, 'Selected']) is True:
                self._data_handler.unselect_all()
                df.loc[row, 'Selected'] = False
                df.loc[row, 'Region'].setMovable(False)
            else:
                self._data_handler.unselect_all()
                df.loc[row, 'Selected'] = True
                df.loc[row, 'Region'].setMovable(True)
                self.annotate_precise_widget.region.setMovable(False)
                self.annotate_precise_widget.region.setVisible(False)

        self.reload_table()

    @staticmethod
    def set_region_brush(region, color):
        region.setBrush(pg.mkColor(color))
        region.setHoverBrush(pg.mkColor(color))

    def _clear_table(self):
        """
        Method for removing all table entries.
        """
        while self.table.rowCount() > 0:
            self.table.removeRow(0)
        self.table.setRowCount(0)

    def reload_table(self):
        """
        Method for reloading the whole table.
        Therefore, the DataFrame of the DataHandler is used everytime since there are all information.
        """
        self._clear_table()

        # iterate over the whole DataFrame
        for index, row in self._data_handler.table_data.iterrows():
            i = self.table.rowCount()
            self.table.setRowCount(i + 1)

            checkbox = QtWidgets.QTableWidgetItem()
            checkbox.setCheckState(QtCore.Qt.Checked if bool(row['Selected']) else QtCore.Qt.Unchecked)
            self.table.setItem(i, 0, checkbox)

            # convert start/end to a time format
            milliseconds_from = str(datetime.timedelta(milliseconds=(row["From"]/self._data_handler.audio_rate)*1000))
            milliseconds_to = str(datetime.timedelta(milliseconds=(row["To"]/self._data_handler.audio_rate)*1000))

            item = QtWidgets.QTableWidgetItem(milliseconds_from[:-4])
            item.setForeground(QtGui.QBrush(QtGui.QColor(0, 0, 0)))
            self.table.setItem(i, 1, item)
            item = QtWidgets.QTableWidgetItem(milliseconds_to[:-4])
            item.setForeground(QtGui.QBrush(QtGui.QColor(0, 0, 0)))
            self.table.setItem(i, 2, item)

            if not row['Event']:
                self.table.setItem(i, 3, QtWidgets.QTableWidgetItem('---'))
                color = QtGui.QColor(238, 233, 108)
                self.set_region_brush(row['Region'], (238, 233, 108, 150))
            else:
                color = QtGui.QColor(87, 223, 151)
                self.set_region_brush(row['Region'], (87, 223, 151, 150))

            if row['Selected'] is True:
                self.table.item(i, 0).setBackground(QtGui.QColor(204, 97, 212))
                self.set_region_brush(row['Region'], (204, 97, 212, 150))
            else:
                self.table.item(i, 0).setBackground(QtGui.QColor(255, 255, 255))

            # add current information to each region item
            row['Region'].table_data = self._data_handler.table_data
            row['Region'].table_widget = self

            item = QtWidgets.QTableWidgetItem(str(row["Event"]))
            item.setForeground(QtGui.QBrush(QtGui.QColor(0, 0, 0)))
            self.table.setItem(i, 3, item)

            for j in range(1, 4):
                self.table.item(i, j).setBackground(color)

        self.scroll_to_index(len(self._data_handler.table_data) - 1)

        # update bar graph window
        self.main_window.update_bar_graph_window()

    def scroll_to_index(self, index):
        index_to_scroll = self.table.model().index(index, 0)
        self.table.scrollTo(index_to_scroll)

    def _delete_selected_row(self):
        self._data_handler.delete_selected_row()

