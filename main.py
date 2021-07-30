import numpy as np
import pandas as pd
import PySimpleGUI as sg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import json
from datetime import datetime
import matplotlib
matplotlib.use('TkAgg')

SETTINGS_FILEPATH = './settings.json'
DATA_FILEPATH = "./data.csv"

#config = {}
#products = []
#ruestData = []
settingsChanged = False
pathChanged = False

def generateData():
    from numpy.random import seed
    from numpy.random import randint
    seed(1)
    products = ['A', 'B', 'C', 'D']
    oldKey = 0
    data = []
    for i in range(0,100):
        key = 0
        while True:
            key = randint(0,4)
            if key != oldKey:
                oldKey = key
                break
        currentProd = products[key]
        value = randint(15,60)
        timestmp = datetime.now(tz=None).strftime("%d-%b-%Y %H:%M:%S")
        data.extend([(currentProd,value,timestmp)])
    df = pd.DataFrame(data,columns=["Material","Duration","Timestamp"])
    df.to_csv(DATA_FILEPATH, sep=";",index=False)
    return df

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

    config["filePath"] = values['-INPUT_FILE-']
    config["dg"] = int(values['-INPUT_DG-'])
    config["g"] = int(values['-INPUT_G-'])
    config["y"] = int(values['-INPUT_Y-'])
    config["r"] = int(values['-INPUT_R-'])

    with open(SETTINGS_FILEPATH, 'w') as file:
        json.dump(config, file)

def showSettings():
    frameLayout = [
        [sg.Text("  Dunkelgrün", size=(12, 1)), sg.Input(default_text=config['dg'], key='-INPUT_DG-', size=(5, 1))],
        [sg.Text("  Grün", size=(12, 1)), sg.Input(default_text=config['g'], key='-INPUT_G-', size=(5, 1))],
        [sg.Text("  Gelb", size=(12, 1)), sg.Input(default_text=config['y'], key='-INPUT_Y-', size=(5, 1))],
        [sg.Text("  Rot", size=(12, 1)), sg.Input(default_text=config['r'], key='-INPUT_R-', size=(5, 1))]
    ]

    settingsLayout = [
        [sg.Text("CSV-File: ")],
        [sg.InputText(default_text=config['filePath'], key='-INPUT_FILE-'), sg.FileBrowse()],
        [sg.Frame("Percentages",frameLayout)],

        [sg.Text("                                                          "), sg.Button('Apply'), sg.Button('Cancel')]
    ]
    window = sg.Window('Settings', settingsLayout, size=(420, 230), finalize=True)

    while True:
        event, values = window.read()

        if event == 'Apply':
            if checkInputs(values):
                global settingsChanged
                settingsChanged = True
                oldPath = config["filePath"]
                updateSettings(values)

                #update Data and update graphs
                if oldPath != config["filePath"]:
                    print("path changed")
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
        df = pd.read_csv("./defaultValues.csv",sep=";")
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
        config = json.load(file)

    data, products = processData(config["filePath"])
    defaultVals = readDefaults(products)

    return config, data, products, defaultVals

def draw_figure(canvas, figure):
    print("drawFigure",figure)
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg

def getFigureMaster():

    n = len(products)

    if n > 0:
        fig, ax = plt.subplots(n,n, figsize=(7,7))

        for i in range(0, n):
            for j in range(0, n):

                if i != j:
                    ax[i][j].hist(ruestData[i * n + j], color="black",
                                  bins=15)  # , density=True)#weights=np.zeros_like(ruestData[i*n+j]) + 1. / len(ruestData[i*n+j]))
                    ax[i][j].xaxis.set_major_locator(plt.MultipleLocator(10))
                    ax[i][j].axvline(defaults[i * n + j], color="cyan", linewidth=2)

                    # calculate abweichung
                    mean = np.array(ruestData[i * n + j]).mean()
                    d = defaults[i * n + j]
                    percent = (mean - d) / mean * 100

                    if (percent <= config["dg"]):
                        ax[i][j].set_facecolor('xkcd:olive green')
                    elif (percent <= config["g"]):
                        ax[i][j].set_facecolor('xkcd:grey green')
                    elif (percent <= config["y"]):
                        ax[i][j].set_facecolor('xkcd:light yellow')
                    else:
                        ax[i][j].set_facecolor('xkcd:dark pink')

                else:
                    ax[i][j].xaxis.set_ticks([])
                    ax[i][j].yaxis.set_ticks([])

                if i == 0:
                    ax[i][j].set_title('Product ' + products[j] , size=12)
                if j == 0:
                    #ax[i][j].set(ylabel='Product ' + products[i])
                    ax[i][j].set_ylabel('Product ' + products[i], size=12)
    else:
        fig, ax = plt.subplots(1, 1, figsize=(7, 7))
    fig.align_ylabels(ax[:, 0])
    fig.tight_layout()
    return fig

def getFigureDetail(fromP,toP):
    #plt.cla()
    fig = Figure() #plt.figure()
    ax = fig.add_subplot(111)
    if len(products) > 0:
        newI = len(products) * products.index(fromP) + products.index(toP)
        ax.hist(ruestData[newI], color="black", bins=15)
        try:
            ax.axvline(defaults[newI], color="cyan", linewidth=2)
        except ValueError:
            print(newI)
            print(defaults)

    return fig

def updateDetail(fromP, toP):
    figDetail.clear()
    ax = figDetail.add_subplot(111)
    if len(products) > 0:
        newI = len(products) * products.index(fromP) + products.index(toP)
        ax.hist(ruestData[newI], color="black", bins=15)
        ax.axvline(defaults[newI], color="cyan", linewidth=2)

def showMaster():
    figMaster, ax = getFigureMaster()
    plt.close(figMaster)
    figAgg_Master = draw_figure(window['-CANVAS_MASTER-'].TKCanvas, figMaster)


if __name__ == '__main__':

    config, ruestData, products, defaults = onInit()

    sg.theme('DarkGrey14')
    menu_def = [['Edit', ['Settings']]]

    masterCol = [#[sg.Text("Master View - Matrices are shown here")],
                 [sg.Canvas(key='-CANVAS_MASTER-')]]
    detailCol = [#[sg.Text("Detail View - Ist/Soll Graph here")],
                 [sg.Canvas(key='-CANVAS_DETAIL-')],
                 [sg.Text("Rüsten von:",size=(15,1),pad=((100,45),0)), sg.Text("Rüsten auf:",size=(15,1))],
                 [sg.InputCombo(products, default_value=products[0], key="-COMBO_FROM-", size=(12,1), pad=((100,70),0), enable_events=True),
                  sg.InputCombo(products, default_value=products[1], key="-COMBO_TO-", size=(12,1), enable_events=True)]
                 #[sg.Button()]
                 ]

    layout = [
        [sg.Menu(menu_def, tearoff=False)],
         [sg.Column(masterCol),
         sg.VSeperator(),
         sg.Column(detailCol)]
    ]
    window = sg.Window('Matrix Viewer', layout, size=(1280, 720), finalize=True)

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
                print("updating detail")
                updateDetail(values['-COMBO_FROM-'], values['-COMBO_TO-'])
                #detailCanvas.figure = getFigureDetail(values['-COMBO_FROM-'], values['-COMBO_TO-'])
                #detailCanvas.get_tk_widget().pack(side='top', fill='both', expand=1)
                detailCanvas.draw()
                #detailCanvas.draw_idle()

        if event == 'Settings':
            showSettings()

        if pathChanged:
            pathChanged = False
            print("updating data")
            ruestData, products = processData(config["filePath"])
            defaults = readDefaults(products)
            window["-COMBO_FROM-"].update(value=products[0], values=products)
            window["-COMBO_TO-"].update(value=products[1], values=products)

        if settingsChanged:
            settingsChanged = False
            print("updating master")
            masterCanvas.figure = getFigureMaster()
            masterCanvas.draw()
            
            updateDetail(window["-COMBO_FROM-"].DefaultValue, window['-COMBO_TO-'].DefaultValue)
            detailCanvas.draw()

    window.close()

