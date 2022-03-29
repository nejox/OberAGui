import PySimpleGUI as sg
import json
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter
from matplotlib.ticker import MultipleLocator

from DataProcessor import DataProcessor
from Config import *

matplotlib.use('TkAgg')

def major_formatter(x, pos):
    return "%.2f" % x

class GuiManager:
    """
    Class to manage the GUI
    """
    def __init__(self):
        # init
        self.data = {}
        self.products = []
        self.defaults = {}
        self.keys = []
        self.settingsChanged = False
        self.pathChanged = False

        # read settings
        with open(SETTINGS_FILEPATH) as file:
            self.settings = json.load(file)

        try:
            self.data, self.products, self.keys = DataProcessor.processDataFromCSV(self.settings["filePath"])
        except Exception:
            sg.popup_error("Could not open/read file:", self.settings["filePath"])

        try:
            self.defaults = DataProcessor.readDefaultsFromCSV(DEFAULTS_FILEPATH, self.products)
        except Exception:
            sg.popup("Could not read Default Values")

        # gui interface definitions
        sg.theme(THEME)
        menu_def = [['Edit', ['Settings']]]
        masterCol = [[sg.Canvas(key='-CANVAS_MASTER-')]]
        if len(self.keys) > 0 and len(self.products) > 0:
            detailCol = [[sg.Canvas(key='-CANVAS_DETAIL-')],
                              [sg.Text("Rüsten von:", size=(15, 1), pad=((100, 45), 0)),
                               sg.Text("Rüsten auf:", size=(15, 1), pad=((60, 45), 0))],
                              [sg.InputCombo(list(self.keys), default_value=self.keys[0], key="-COMBO_FROM-", size=(20, 1),
                                             pad=((100, 70), 0), enable_events=True),
                               sg.InputCombo(list(self.products), default_value=self.products[1], key="-COMBO_TO-", size=(20, 1),
                                             enable_events=True)]
                              ]
        else:
            detailCol = [[sg.Canvas(key='-CANVAS_DETAIL-')],
                            [sg.Text("Rüsten von:", size=(15, 1), pad=((100, 45), 0)),
                                sg.Text("Rüsten auf:", size=(15, 1))],
                            [sg.InputCombo([], key="-COMBO_FROM-", size=(20, 1), pad=((100, 70), 0), enable_events=True),
                             sg.InputCombo([], key="-COMBO_TO-", size=(20, 1), enable_events=True)]
                        ]

        self.layout = [
            [sg.Menu(menu_def, tearoff=False)],
            [sg.Column(masterCol),
             sg.VSeperator(),
             sg.Column(detailCol)]
        ]

    def getFigureDetail(self, productFrom, productTo):
        fig = Figure(figsize=(6, 5))
        ax = fig.add_subplot(111)
        if len(self.products) > 0 and productTo in self.data[productFrom]:
            if len(self.defaults) > 0:
                defaultVal = self.defaults[productFrom][productTo]
            else:
                defaultVal = None

            self.setHistogram(ax, self.data[productFrom][productTo], defaultVal, False)
            fig.tight_layout()

        return fig

    def calcDivergence(self, ruestData, defaultVal):
        mean = np.array(ruestData).mean()
        return (mean - defaultVal) / mean * 100

    def getFigureMaster(self):
        n = len(self.keys)
        m = len(self.products)
        if n > 0:
            fig, ax = plt.subplots(n, m, figsize=(12, 10))

            for i, productFrom in enumerate(self.keys, 0):
                for j, productTo in enumerate(self.products, 0):

                    if productFrom != productTo and productTo in self.data[productFrom]:

                        if len(self.defaults) > 0:
                            defaultVal = self.defaults[productFrom][productTo]

                            # calculate divergence
                            percent = self.calcDivergence(self.data[productFrom][productTo], defaultVal)

                            if (percent <= self.settings["dg"]):
                                ax[i][j].set_facecolor('xkcd:olive green')
                            elif (percent <= self.settings["g"]):
                                ax[i][j].set_facecolor('xkcd:grey green')
                            elif (percent <= self.settings["y"]):
                                ax[i][j].set_facecolor('xkcd:light yellow')
                            else:
                                ax[i][j].set_facecolor('xkcd:dark pink')

                        else:
                            defaultVal = None

                        self.setHistogram(ax[i][j], self.data[productFrom][productTo], defaultVal)

                    else:
                        ax[i][j].xaxis.set_ticks([])
                        ax[i][j].yaxis.set_ticks([])

                    if i == 0:
                        ax[i][j].set_title(productTo, size=7)
                    if j == 0:
                        ax[i][j].set_ylabel(productFrom, size=7)

                    ax[i][j].tick_params(axis='both', which='major', labelsize=7)

                    fig.align_ylabels(ax[:, 0])
                    fig.tight_layout()
        else:
            fig, ax = plt.subplots(1, 1, figsize=(12, 10))

        return fig

    def setHistogram(self, ax, data, defaultVal, isMaster=True):
        if self.settings["showAbsFrequencies"]:
            ax.hist(data, color="black", bins=BINS)
            if not isMaster:
                ax.set_ylabel(DETAIL_YAXIS_LABEL_ABS, size=12)
                ax.set_xlabel(DETAIL_XAXIS_LABEL, size=12)
        else:
            weights = np.zeros_like(data) + 1. / len(data)  # 100 for percentages
            ax.hist(data, weights=weights, color="black", bins=BINS)
            if not isMaster:
                ax.yaxis.set_major_formatter(FuncFormatter(major_formatter))
                ax.set_ylabel(DETAIL_YAXIS_LABEL_REL, size=12)
                ax.set_xlabel(DETAIL_XAXIS_LABEL, size=12)

        ax.xaxis.set_major_locator(MultipleLocator(10))
        # ax.tick_params(axis='x', which='major', labelrotation=45)
        # ax.xaxis.set_ticks(data)

        if defaultVal is not None:
            ax.axvline(defaultVal, color="cyan", linewidth=2)

        if self.settings["centerDiagrams"]:
            valueList = []
            [valueList.extend(values) for firstLvl in self.data.values() for values in firstLvl.values()]
            maxVal = max(valueList)
            #minVal = min(valueList)
            minVal = 0

            maxVal = maxVal + 15 - maxVal % 15

            ax.set_xlim(left=minVal, right=maxVal + 1)
            ax.set_xticks(range(minVal, maxVal + 1, 15))

    def draw_figure(self, canvas, figure):
        figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
        figure_canvas_agg.draw()
        figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
        return figure_canvas_agg

    def checkInputs(self, values):
        try:
            as_int = int(values['-INPUT_DG-'])
        except:
            sg.Popup('Ops!', "wrong input!")
            return False
        try:
            as_int = int(values['-INPUT_G-'])
        except:
            sg.Popup('Ops!', "wrong input!")
            return False
        try:
            as_int = int(values['-INPUT_Y-'])
        except:
            sg.Popup('Ops!', "wrong input!")
            return False
        try:
            as_int = int(values['-INPUT_R-'])
        except:
            sg.Popup('Ops!', "wrong input!")
            return False
        return True

    def updateSettings(self, values):
        self.settings["filePath"] = values['-INPUT_FILE-']
        self.settings["dg"] = int(values['-INPUT_DG-'])
        self.settings["g"] = int(values['-INPUT_G-'])
        self.settings["y"] = int(values['-INPUT_Y-'])
        self.settings["r"] = int(values['-INPUT_R-'])
        self.settings["showAbsFrequencies"] = values['-INPUT_FREQ-']
        self.settings["centerDiagrams"] = values["-INPUT_CENTERING-"]

        with open(SETTINGS_FILEPATH, 'w') as file:
            json.dump(self.settings, file)

    def showSettings(self):
        frameLayout = [
            [sg.Text("  " + VGOOD, size=(12, 1)), sg.Input(default_text=self.settings['dg'], key='-INPUT_DG-', size=(5, 1))],
            [sg.Text("  " + GOOD, size=(12, 1)), sg.Input(default_text=self.settings['g'], key='-INPUT_G-', size=(5, 1))],
            [sg.Text("  " + OK, size=(12, 1)), sg.Input(default_text=self.settings['y'], key='-INPUT_Y-', size=(5, 1))],
            [sg.Text("  " + BAD, size=(12, 1)), sg.Input(default_text=self.settings['r'], key='-INPUT_R-', size=(5, 1))]
        ]

        settingsLayout = [
            [sg.Text("CSV-File: ")],
            [sg.InputText(default_text=self.settings['filePath'], key='-INPUT_FILE-'), sg.FileBrowse()],
            [sg.Checkbox("scaled Diagrams", key="-INPUT_CENTERING-", default=self.settings["centerDiagrams"])],
            [sg.Checkbox("show abs. Frequencies", key="-INPUT_FREQ-", default=self.settings["showAbsFrequencies"])],
            [sg.Frame("Degree of deviation", frameLayout)],
            [sg.Text("                                                          "), sg.Button('Apply'),
             sg.Button('Cancel')]
        ]
        window = sg.Window('Settings', settingsLayout, size=(420, 300), finalize=True)

        while True:
            event, values = window.read()

            if event == 'Apply':
                if self.checkInputs(values):
                    self.settingsChanged = True
                    oldPath = self.settings["filePath"]
                    self.updateSettings(values)

                    # update Data and update graphs
                    if oldPath != self.settings["filePath"]:
                        self.pathChanged = True

                    window.close()
                    break
            else:
                window.close()
                break

    def updateDetail(self, fromP, toP):
        self.figDetail.clear()
        ax = self.figDetail.add_subplot(111)
        if len(self.products) > 0 and fromP in self.data and toP in self.data[fromP]:
            if len(self.defaults) > 0:
                defaultVal = self.defaults[fromP][toP]
            else:
                defaultVal = None

            self.setHistogram(ax, self.data[fromP][toP], defaultVal, False)

    def callWindow(self, sizeX, sizeY):
        window = sg.Window(TITLE, self.layout, size=(sizeX, sizeY), finalize=True)
        #window.Maximize()

        fromP = window["-COMBO_FROM-"].DefaultValue
        toP = window["-COMBO_TO-"].DefaultValue

        self.figMaster = self.getFigureMaster()
        masterCanvas = self.draw_figure(window['-CANVAS_MASTER-'].TKCanvas, self.figMaster)

        self.figDetail = self.getFigureDetail(fromP, toP)
        detailCanvas = self.draw_figure(window['-CANVAS_DETAIL-'].TKCanvas, self.figDetail)

        while True:
            event, values = window.read()

            if event == sg.WIN_CLOSED or event == 'Cancel':  # if user closes window or clicks cancel
                break
            if event == '-COMBO_TO-' or event == '-COMBO_FROM-':
                if values['-COMBO_FROM-'] != values['-COMBO_TO-']:
                    self.updateDetail(values['-COMBO_FROM-'], values['-COMBO_TO-'])
                    detailCanvas.draw()

            if event == 'Settings':
                self.showSettings()

            if self.pathChanged:
                self.pathChanged = False
                try:
                    self.data, self.products, self.keys = DataProcessor.processDataFromCSV(self.settings["filePath"])
                except Exception:
                    sg.popup_error("Could not open/read file:", self.settings["filePath"])
                #self.defaults = DataProcessor.readDefaults(DEFAULTS_FILEPATH, self.products)
                window["-COMBO_FROM-"].update(value=self.products[0], values=list(self.products))
                window["-COMBO_TO-"].update(value=self.products[1], values=list(self.products))

            if self.settingsChanged:
                self.settingsChanged = False
                masterCanvas.figure = self.getFigureMaster()
                masterCanvas.draw()

                self.updateDetail(values["-COMBO_FROM-"], values['-COMBO_TO-'])
                detailCanvas.draw()

        window.close()