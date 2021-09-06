from Config import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter
from matplotlib.ticker import MultipleLocator
from datetime import datetime
import matplotlib.pyplot as plt
import PySimpleGUI as sg
import numpy as np
import pandas as pd
import json
import matplotlib

matplotlib.use('TkAgg')

settingsChanged = False
pathChanged = False

def checkInputs(values):
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

def updateSettings(values):

    settings["filePath"] = values['-INPUT_FILE-']
    settings["dg"] = int(values['-INPUT_DG-'])
    settings["g"] = int(values['-INPUT_G-'])
    settings["y"] = int(values['-INPUT_Y-'])
    settings["r"] = int(values['-INPUT_R-'])
    settings["showAbsFrequencies"] = values['-INPUT_FREQ-']
    settings["centerDiagrams"] = values["-INPUT_CENTERING-"]

    with open(SETTINGS_FILEPATH, 'w') as file:
        json.dump(settings, file)

def showSettings():
    frameLayout = [
        [sg.Text("  Dunkelgrün", size=(12, 1)), sg.Input(default_text=settings['dg'], key='-INPUT_DG-', size=(5, 1))],
        [sg.Text("  Grün", size=(12, 1)), sg.Input(default_text=settings['g'], key='-INPUT_G-', size=(5, 1))],
        [sg.Text("  Gelb", size=(12, 1)), sg.Input(default_text=settings['y'], key='-INPUT_Y-', size=(5, 1))],
        [sg.Text("  Rot", size=(12, 1)), sg.Input(default_text=settings['r'], key='-INPUT_R-', size=(5, 1))]
    ]

    settingsLayout = [
        [sg.Text("CSV-File: ")],
        [sg.InputText(default_text=settings['filePath'], key='-INPUT_FILE-'), sg.FileBrowse()],
        [sg.Checkbox("scaled Diagrams", key="-INPUT_CENTERING-", default=settings["centerDiagrams"])],
        [sg.Checkbox("show abs. Frequencies", key="-INPUT_FREQ-", default=settings["showAbsFrequencies"])],
        [sg.Frame("Percentages",frameLayout)],
        [sg.Text("                                                          "), sg.Button('Apply'), sg.Button('Cancel')]
    ]
    window = sg.Window('Settings', settingsLayout, size=(420, 300), finalize=True)

    while True:
        event, values = window.read()

        if event == 'Apply':
            if checkInputs(values):
                global settingsChanged
                settingsChanged = True
                oldPath = settings["filePath"]
                updateSettings(values)

                #update Data and update graphs
                if oldPath != settings["filePath"]:
                    global pathChanged
                    pathChanged = True

                window.close()
                break
        else:
            window.close()
            break

def processData(filePath):
    rslt = []
    products = []
    try:
        df = pd.read_csv(filePath, sep=";")

        products = df.Material.unique().tolist()
        products.sort()
        rslt = [[] for i in range(len(products)*len(products))]
        #TODO: Wissen welches Produkt davor war
        oldProd = 'A'
        for index, row in df.iterrows():
            i = len(products) * products.index(oldProd)
            j = products.index(row.Material)
            newI = i + j
            rslt[newI].append(row.Duration)
            oldProd = row.Material

    except Exception:
        sg.popup_error("Could not open/read file:", filePath)

    return rslt, products

def readDefaults(products):

    ldefaults = {}
    if len(products) > 0:
        df = pd.read_csv(DEFAULTS_FILEPATH, sep=";")
        for index, row in df.iterrows():
            ldefaults[row.From+row.To] = row.Duration
            try:
                newI = len(products) * products.index(row.From)+products.index(row.To)
                ldefaults[newI] = row.Duration
            except ValueError:
                continue

    return ldefaults

def onInit():
    # read settings
    with open(SETTINGS_FILEPATH) as file:
        settings = json.load(file)

    data, products = processData(settings["filePath"])
    defaultVals = readDefaults(products)

    return settings, data, products, defaultVals

def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg

def getFigureMaster():

    n = len(products)

    if n > 0:
        fig, ax = plt.subplots(n,n, figsize=(7,6))

        for i in range(0, n):
            for j in range(0, n):

                if i != j:
                    dataIndex = i * n + j

                    setHistogram(ax[i][j], ruestData[dataIndex], defaults[dataIndex])

                    # calculate divergence
                    mean = np.array(ruestData[dataIndex]).mean()
                    d = defaults[dataIndex]
                    percent = (mean - d) / mean * 100

                    if (percent <= settings["dg"]):
                        ax[i][j].set_facecolor('xkcd:olive green')
                    elif (percent <= settings["g"]):
                        ax[i][j].set_facecolor('xkcd:grey green')
                    elif (percent <= settings["y"]):
                        ax[i][j].set_facecolor('xkcd:light yellow')
                    else:
                        ax[i][j].set_facecolor('xkcd:dark pink')

                else:
                    ax[i][j].xaxis.set_ticks([])
                    ax[i][j].yaxis.set_ticks([])

                if i == 0:
                    ax[i][j].set_title('Product ' + products[j], size=12)
                if j == 0:
                    ax[i][j].set_ylabel('Product ' + products[i], size=12)
    else:
        fig, ax = plt.subplots(1, 1, figsize=(7, 7))
    fig.align_ylabels(ax[:, 0])
    fig.tight_layout()
    return fig

def getFigureDetail(fromP,toP):
    fig = Figure(figsize=(6,5))
    ax = fig.add_subplot(111)
    if len(products) > 0:
        dataIndex = len(products) * products.index(fromP) + products.index(toP)
        setHistogram(ax, ruestData[dataIndex], defaults[dataIndex], False)
        fig.tight_layout()

    return fig

def major_formatter(x, pos):
    return "%.2f" % x

def setHistogram(ax, data, defaultVal, isMaster=True):
    if settings["showAbsFrequencies"]:
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
    ax.axvline(defaultVal, color="cyan", linewidth=2)
    if settings["centerDiagrams"]:
        maxVal = max(np.amax(ruestData))
        list = np.amin(ruestData)
        minVal = 0
        if list:
            minVal = min(np.amin(ruestData))

        maxVal = maxVal + 15 - maxVal % 15

        ax.set_xlim(left=minVal, right=maxVal+1)
        ax.set_xticks(range(minVal, maxVal+1, 15))

def updateDetail(fromP, toP):
    figDetail.clear()
    ax = figDetail.add_subplot(111)
    if len(products) > 0:
        dataIndex = len(products) * products.index(fromP) + products.index(toP)
        setHistogram(ax, ruestData[dataIndex], defaults[dataIndex], False)


if __name__ == '__main__':

    settings, ruestData, products, defaults = onInit()

    sg.theme(THEME)
    menu_def = [['Edit', ['Settings']]]

    masterCol = [[sg.Canvas(key='-CANVAS_MASTER-')]]
    detailCol = [[sg.Canvas(key='-CANVAS_DETAIL-')],
                 [sg.Text("Rüsten von:",size=(15,1),pad=((100,45),0)), sg.Text("Rüsten auf:",size=(15,1))],
                 [sg.InputCombo(products, default_value=products[0], key="-COMBO_FROM-", size=(12,1), pad=((100,70),0), enable_events=True),
                  sg.InputCombo(products, default_value=products[1], key="-COMBO_TO-", size=(12,1), enable_events=True)]
                 ]

    layout = [
        [sg.Menu(menu_def, tearoff=False)],
         [sg.Column(masterCol),
         sg.VSeperator(),
         sg.Column(detailCol)]
    ]
    window = sg.Window(TITLE, layout, size=(1280, 720), finalize=True)

    figMaster = getFigureMaster()
    masterCanvas = draw_figure(window['-CANVAS_MASTER-'].TKCanvas, figMaster)

    fromP = window["-COMBO_FROM-"].DefaultValue
    toP = window["-COMBO_TO-"].DefaultValue

    figDetail = getFigureDetail(fromP,toP)
    detailCanvas = draw_figure(window['-CANVAS_DETAIL-'].TKCanvas, figDetail)

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Cancel':  # if user closes window or clicks cancel
            break
        if event == '-COMBO_TO-' or event == '-COMBO_FROM-':
            if values['-COMBO_FROM-'] != values['-COMBO_TO-']:
                updateDetail(values['-COMBO_FROM-'], values['-COMBO_TO-'])
                detailCanvas.draw()

        if event == 'Settings':
            showSettings()

        if pathChanged:
            pathChanged = False
            ruestData, products = processData(settings["filePath"])
            defaults = readDefaults(products)
            window["-COMBO_FROM-"].update(value=products[0], values=products)
            window["-COMBO_TO-"].update(value=products[1], values=products)

        if settingsChanged:
            settingsChanged = False
            masterCanvas.figure = getFigureMaster()
            masterCanvas.draw()
            
            updateDetail(window["-COMBO_FROM-"].DefaultValue, window['-COMBO_TO-'].DefaultValue)
            detailCanvas.draw()

    window.close()

