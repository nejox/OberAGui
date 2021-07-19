import numpy as np
import pandas as pd
import PySimpleGUI as sg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import json
from datetime import datetime
import matplotlib
matplotlib.use('TkAgg')

SETTINGS_FILEPATH = './settings.json'
DATA_FILEPATH = "./data.csv"

config = {}
products = []
ruestData = []

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
                updateSettings(values)
                window.close()
                break
        else:
            window.close()
            break


def processData(df):
    products = df.Material.unique().tolist()
    products.sort()
    rslt = [[] for i in range(len(products)*len(products))]
    oldProd = 'A'
    for index, row in df.iterrows():
        i = len(products) * products.index(oldProd)
        j = products.index(row.Material)
        newI = i + j
        rslt[newI].append(row.Duration)
        oldProd = row.Material
    return rslt, products


def readDefaults(products):
    defaults = {}
    df = pd.read_csv("./defaultValues.csv",sep=";")
    for index, row in df.iterrows():
        defaults[row.From+row.To] = row.Duration
        newI = len(products) * products.index(row.From)+products.index(row.To)
        defaults[newI] = row.Duration

    return defaults


def onInit():
    df = generateData()
    data, products = processData(df)
    defaultVals = readDefaults(products)
    # read settings
    with open(SETTINGS_FILEPATH) as file:
        config = json.load(file)
    return config, data, products, defaultVals


def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg

def getFigureMaster():

    n = len(products)
    fig, ax = plt.subplots(n,n, figsize=(7,7))
    t = np.arange(0, 3, .01)

    for i in range(0,n):
        for j in range(0,n):

            if i != j:
                #ax[i][j].plot(t, 2 * np.sin(2 * np.pi * t))
                ax[i][j].hist(ruestData[i*n+j],color="red",bins=15)#, density=True)#weights=np.zeros_like(ruestData[i*n+j]) + 1. / len(ruestData[i*n+j]))
                ax[i][j].xaxis.set_major_locator(plt.MultipleLocator(10))
                ax[i][j].axvline(defaults[i*n+j], color="blue",linewidth=2)
            else:
                ax[i][j].xaxis.set_ticks([])
                ax[i][j].yaxis.set_ticks([])

            if i == 0:
                ax[i][j].set_title('Product '+products[j])
            if j == 0:
                ax[i][j].set(ylabel='Product '+products[i])
    return fig

def getFigureDetail(fromP,toP):
    newI = len(products) * products.index(fromP) + products.index(toP)

    fig = plt.figure()
    plt.hist(ruestData[newI], color="red", bins=15)
    plt.axvline(defaults[newI], color="blue", linewidth=2)

    return fig

def updateFigure(fromP, toP):
    plt.clf()
    newI = len(products) * products.index(fromP) + products.index(toP)
    plt.hist(ruestData[newI], color="red", bins=15)
    plt.axvline(defaults[newI], color="blue", linewidth=2)

if __name__ == '__main__':

    config, ruestData, products, defaults = onInit()

    sg.theme('DarkGrey14')
    menu_def = [['Edit', ['Settings']]]

    masterCol = [#[sg.Text("Master View - Matrices are shown here")],
                 [sg.Canvas(key='-CANVAS_MASTER-')]]
    detailCol = [#[sg.Text("Detail View - Ist/Soll Graph here")],
                 [sg.Canvas(key='-CANVAS_DETAIL-')],
                 [sg.Text("Rüsten von:",size=(15,1),pad=((100,45),0)), sg.Text("Rüsten auf:",size=(15,1))],
                 [sg.InputCombo(products, default_value='A', key="-COMBO_FROM-", size=(12,1), pad=((100,70),0), enable_events=True),
                  sg.InputCombo(products, default_value='B', key="-COMBO_TO-", size=(12,1), enable_events=True)]
                 #[sg.Button()]
                 ]

    layout = [
        [sg.Menu(menu_def, tearoff=False)],
         [sg.Column(masterCol),
         sg.VSeperator(),
         sg.Column(detailCol)]
    ]
    window = sg.Window('Matrix Viewer', layout, size=(1280, 720), finalize=True)

    draw_figure(window['-CANVAS_MASTER-'].TKCanvas, getFigureMaster())
    fromP = window["-COMBO_FROM-"].DefaultValue
    toP = window["-COMBO_TO-"].DefaultValue
    fig = getFigureDetail(fromP,toP)
    fig_agg = draw_figure(window['-CANVAS_DETAIL-'].TKCanvas, fig)

    while True:
        event, values = window.read()
        print(event, values)
        print(values['-COMBO_FROM-'])
        print(values['-COMBO_TO-'])

        if event == sg.WIN_CLOSED or event == 'Cancel':  # if user closes window or clicks cancel
            break
        if event == '-COMBO_TO-' or event == '-COMBO_FROM-':
            if values['-COMBO_FROM-'] != values['-COMBO_TO-']:
                updateFigure(values['-COMBO_FROM-'], values['-COMBO_TO-'])
                fig_agg.draw()
        if event == 'Settings':
            showSettings()

    window.close()

