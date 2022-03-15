import pyqtgraph as pg


class RegionItem(pg.LinearRegionItem):
    def __init__(self):
        super(RegionItem, self).__init__()
        self.table_data = None
        self.table_widget = None

    def mouseClickEvent(self, ev):
        for index, row in self.table_data.iterrows():
            if row['Region'] == self:
                self.table_widget.select_row(index)