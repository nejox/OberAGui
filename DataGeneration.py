from numpy.random import seed
from numpy.random import randint
import pandas as pd
import numpy as np
from datetime import datetime


def generateData(dataPath):
    n_samples = 100
    minTime = 15
    maxTime = 120

    products = ['A', 'B', 'C', 'D', 'E']
    data = []

    for i in range(0, n_samples):

        while True:
            keyFrom = randint(0, len(products))
            keyTo = randint(0, len(products))
            if keyFrom != keyTo:
                if len(data) > 0 and data[-1][:2] == (products[keyFrom], products[keyTo]):
                     continue
                break
        prodFrom = products[keyFrom]
        prodTo = products[keyTo]
        timeVal = randint(minTime, maxTime)
        data.extend([(prodFrom, prodTo, timeVal)])
    df = pd.DataFrame(data, columns=["Programm A", "Programm B", "Zeitdauer in Minuten"])
    df.to_csv(dataPath, sep=";", index=False)
    return df


def convertData(path):
    df = pd.read_excel(path)
    data = []

    for index, row in df.iterrows():
        r = np.array([row[1], row[2], datetime.now(tz=None).strftime("%d-%b-%Y %H:%M:%S")])
        data.append(r)

    df = pd.DataFrame(np.array(data), columns=["Material", "Duration", "Timestamp"])

    df.to_csv("data/test_amp.csv", sep=";", index=False)
    print("csv written")


DATA_FILEPATH = "data/genData_"+datetime.now().strftime("%d_%m_%Y_%H_%M_%S")+".csv"
generateData(DATA_FILEPATH)