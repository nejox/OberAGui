import pandas as pd
import numpy as np


class DataProcessor:
    """
        Class for managing the data processing
    """

    def __init__(self):
        pass

    @staticmethod
    def processDataFromCSV(filePath):
        products = []
        dictFrom = {}

        df = pd.read_csv(filePath, sep=";")

        fromMaterials = np.sort(df.iloc[:, 0].unique())

        for mat in fromMaterials:
            dictFrom[mat] = {}

        for index, row in df.iterrows():
            products.append(row[1])
            if row[1] in dictFrom[row[0]]:
                dictFrom[row[0]][row[1]].append(row[2])
            else:
                dictFrom[row[0]][row[1]] = [row[2]]

        products.sort()

        keys = np.array(list(dictFrom.keys()))

        return dictFrom, pd.unique(products), keys

    @staticmethod
    def readDefaultsFromCSV(DEFAULTS_FILEPATH, materials):
        dictDefaults = {}
        if len(materials) > 0:
            df = pd.read_csv(DEFAULTS_FILEPATH, sep=";")

            fromMats = np.sort(df.iloc[:, 0].unique())
            for mat in fromMats:
                dictDefaults[mat] = {}

            for index, row in df.iterrows():
                dictDefaults[row.From][row.To] = row.Duration

        return dictDefaults
