import numpy as np
import pandas as pd
from PyQt5 import QtWidgets
import pyqtgraph as pg
import copy
import flammkuchen as fl
from scipy.io.wavfile import read, write
import simpleaudio as sa
import json
import os
import datetime

from .calculate_md5_hash import get_md5_hash
from .region_item import RegionItem


class DataHandler(QtWidgets.QFrame):
    """
    Class that handles all annotated data within one DataFrame.
    """
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.audio_player = None
        self.audio_data_original = None
        self.audio_data = None
        self.audio_rate = None

        # load setup.json
        with open("../setup.json") as f:
            self.setup = json.load(f)

        # needed for play/stop button event
        self.play_obj = None

        # object will be initialized in class TableWidget
        self.table_widget = None

        # objects that will be initialized in class AnnotatePreciseWidget
        self.annotate_precise_widget = None
        self.plot = None
        self.region = None

        # dataframe that saves all annotations
        self.table_data = pd.DataFrame(columns=['Initial', 'From', 'To', 'Event', 'Selected', 'Region'])

        # set of possible events
        self.events = self.setup['classes']

        self._load_data()

    ##################################################################################
    # Load/Save data
    ##################################################################################
    def _load_data(self):
        """
        Load data from an audio file.
        """
        print(self.path)
        try:
            self.audio_rate, self.audio_data_original = read(self.path)
        except:
            raise Exception(f"Can't load the file. ({self.path})")

        self.audio_data = self.audio_data_original
        if len(self.audio_data.shape) == 2:
            self.audio_data = self.audio_data[:, 0]

    def load_annotations(self, dict_):
        self.table_data = dict_['DataFrame']
        self.table_data['Selected'] = False
        regions = []
        for idx in range(len(self.table_data)):
            region = pg.LinearRegionItem()
            region.setRegion([self.table_data.loc[idx, 'From'], self.table_data.loc[idx, 'To']])
            region.setMovable(False)
            region.sigRegionChanged.connect(self.change_selected_region)
            self.plot.addItem(region)
            regions.append(region)
        self.table_data['Region'] = regions
        self.reload_table()

    def save(self, path):
        df = copy.deepcopy(self.table_data)
        del df['Region']
        del df['Selected']

        d = {'Filename': self.path.name, 'FileHash': get_md5_hash(self.path), 'DataFrame': df}
        fl.save(path, d)

    def save_annotated_events_wav(self, path):
        """ Method for saving each annotated event in an own .wav-file. """
        for class_ in self.events:
            class_path = os.path.join(path, class_)
            os.mkdir(class_path)
            idx = 0
            for index, row in self.table_data.iterrows():
                if row['Event'] == class_:
                    data = self.audio_data_original[row['From']:row['To'], ...]
                    write(filename=os.path.join(class_path, f"{class_}_{idx}.wav"), rate=self.audio_rate, data=data)
                    idx += 1

    def save_annotated_events_csv(self, path):
        """ Method for saving all annotations to a .csv-file. """
        df = copy.deepcopy(self.table_data)
        for index, row in df.iterrows():
            milliseconds_from = str(datetime.timedelta(milliseconds=(row["From"] / self.audio_rate) * 1000))[:-4]
            milliseconds_to = str(datetime.timedelta(milliseconds=(row["To"] / self.audio_rate) * 1000))[:-4]
            df.loc[index, 'From'] = milliseconds_from + f" ({row['From']})"
            df.loc[index, 'To'] = milliseconds_to + f" ({row['To']})"

        del df['Region']
        del df['Selected']
        del df['Initial']
        df.to_csv(path, sep=';')

    ##################################################################################
    # Methods that modify the DataFrame through window events
    ##################################################################################
    def add_event(self):
        """
        Method adds an event ('yellow' event).
        """
        # check if any row is selected --> if yes, no new event can be added until the row in unselected again
        for index, row in self.table_data.iterrows():
            if bool(row['Selected']) is True:
                return

        # get current position/region and add a new event there
        pos = self.audio_player.position() / 1000 * self.audio_rate
        min_x, max_x = self.region.getRegion()

        region = RegionItem()
        region.setRegion([min_x, max_x])
        region.setMovable(False)
        region.sigRegionChanged.connect(self.change_selected_region)
        self.plot.addItem(region)

        self.table_data = self.table_data.append(
                {'Initial': pos, 'From': min_x, 'To': max_x, 'Event': '', 'Selected': False, 'Region': region},
                ignore_index=True)

        self.table_widget.reload_table()

    def add_precise_event(self, event_idx):
        """
        Methods adds a precisely annotated event ('green' event).
        """
        # first check if we want to annotate an already selected region
        for index, row in self.table_data.iterrows():
            if bool(row['Selected']) is True:
                self.table_data.loc[index, 'Event'] = self.events[event_idx]
                self.reload_table()
                self._update_region(self.table_data.loc[index, 'Region'])
                return

        # if not, the normal region will be used to annotate the selected region
        pos = self.audio_player.position() / 1000 * self.audio_rate
        min_x, max_x = self.region.getRegion()

        if int(min_x) == int(max_x):
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText("Error")
            msg.setInformativeText('Please select a region.')
            msg.setWindowTitle("Error")
            msg.exec_()
            return

        region = pg.LinearRegionItem()
        region.setRegion([min_x, max_x])
        region.setMovable(False)
        region.sigRegionChanged.connect(self.change_selected_region)
        self.plot.addItem(region)

        self.table_data = self.table_data.append(
            {'Initial': pos, 'From': int(min_x), 'To': int(max_x),
             'Event': self.events[event_idx], 'Selected': False, 'Region': region},
            ignore_index=True)

        self.reload_table()

    def delete_selected_row(self):
        """
        Deletes a selected table entry from the DataFrame.
        """
        for index, row in self.table_data.iterrows():
            if row['Selected'] is True:
                self.plot.removeItem(self.table_data.loc[index, 'Region'])
                self.table_data = self.table_data.drop(index)
                self.table_data = self.table_data.reset_index(drop=True)
                self.unselect_all()
                self.reload_table()
                break

    def reload_table(self):
        """
        Reloading the GUI table.
        """
        self.table_widget.reload_table()

    def play_selected_region(self):
        """
        Method for playing the selected region.
        """
        if self.audio_player.state() == self.audio_player.PlayingState:
            return
        else:
            min_x, max_x = self.region.getRegion()
            for index, row in self.table_data.iterrows():
                if row['Selected'] is True:
                    min_x = row['From']
                    max_x = row['To']

            data_to_play = np.asarray(self.audio_data[int(min_x):int(max_x)], order='C')
            if len(data_to_play) == 0:
                return
            self.play_obj = sa.play_buffer(data_to_play, 1, 2, self.audio_rate)

    def change_selected_region(self):
        """
        Method that changes the values within the DataFrame when the boundaries of the selected region are changing.
        """
        region = self.sender()
        min_x, max_x = region.getRegion()
        for index, row in self.table_data.iterrows():
            if row['Selected'] is True:
                self.table_data.loc[index, 'From'] = min_x
                self.table_data.loc[index, 'To'] = max_x
                self.reload_table()
                break

    def select_previous_or_next_event(self, x):
        """
        Method for selecting the previous or next annotated event (when clicking the corresponding button/key)
        """
        if len(self.table_data) == 0:
            return

        currently_selected = None
        for index, row in self.table_data.iterrows():
            if bool(row['Selected']) is True:
                currently_selected = index
                break

        if currently_selected is None:
            if x == -1:
                return
            else:
                new_index = 0
        else:
            new_index = currently_selected + x
            if new_index == -1:
                self.reload_table()
                return
            elif new_index >= len(self.table_data):
                new_index = len(self.table_data) - 1

        self.unselect_all()
        self.table_widget.select_row(new_index)

    def unselect_all(self):
        """
        Method for unselecting all events within the table. (I just do it for all entries to keep everything clean)
        """
        for index, row in self.table_data.iterrows():
            row['Region'].setMovable(False)
            self._update_region(row['Region'])

        self.region.setVisible(True)
        self.region.setMovable(True)
        self.table_data.loc[:, 'Selected'] = False
        self.reload_table()

    @staticmethod
    def _update_region(region):
        """ Set visible false and true as workaround to update the regions color inside the PyGraphItem """
        region.setVisible(False)
        region.setVisible(True)

    ##################################################################################
    # Methods to get data for Bar Graph Window
    ##################################################################################
    def get_bar_graph_data(self, flag='length'):
        if flag is not 'count' and flag is not 'length':
            raise ValueError("Parameter 'flag' is not valid.")

        y_data = np.zeros(10)
        for index, event in enumerate(self.events):
            for _, row in self.table_data.iterrows():
                if row['Event'] == event:
                    if flag == 'count':
                        y_data[index] += 1
                    elif flag == 'length':
                        length = row['To'] - row['From']
                        y_data[index] += length
        if max(y_data) == 0:
            return y_data
        else:
            return y_data / max(y_data)



