# -----------------------------------------------------------------------------
# ProcessDataMD.py
# -----------------------------------------------------------------------------
import pandas as pd
import numpy as np
import os
import re
import random


class InputData:
    def __init__(self, datadir, popdata):
        print('*****************  Loading Population Files')
        self.ComPop = popdata['POPULATION']
        self.ComNames = pd.DataFrame(popdata['ZIP_CODE'])

        """ Import Adjacency Matrix from the Input Folder """
        print('*****************  Loading Adjacency Files')
        fileNames = os.listdir(datadir)
        self.ComHosAdj = {}

        for x in fileNames:
            if x.startswith("AdjComHos"):
                self.ComHosAdj[int("".join(re.findall(r'\d+', x)))] = \
                    pd.read_csv(datadir + '/{}'.format(x), index_col=0)
                print('Loading', x)

        """ Calculate average populations """
        self.AvgPopC = np.array(self.ComPop)

        """ Create Adjacency Flow Matrix """
        ComHosQtr = [[]] * len(list(self.ComHosAdj.keys()))

        n = 0
        for x in sorted(self.ComHosAdj.keys()):
            td = self.ComNames.copy()
            td = td.merge(pd.DataFrame(self.ComHosAdj[x]), how='left',
                          left_on='ZIP_CODE', right_index=True)
            td = td.set_index('ZIP_CODE')
            ComHosQtr[n] = td.values
            n += 1

        self.ComHosQtr = np.asarray(ComHosQtr)
        self.HosNames = self.ComHosAdj[x].columns

        P = list(range(len(self.HosNames)))     # Hospital
        R = list(range(len(self.ComNames)))     # Community

        FacList = pd.read_csv(datadir + '/FacilityList.csv')
        self.HosNamesDict = {} # Dictionary mapping HSCRC ID to Name
        for i in range(0,FacList.HOSPID.__len__()):
            self.HosNamesDict[int(FacList.HOSPID[i])] = FacList.ProviderNames[i]

        self.ProviderNamesColumn = {} # Dictionary mapping name to column in adjacency matrix
        n = 0
        for i in P:
            self.ProviderNamesColumn[n] = self.HosNamesDict[int(self.HosNames[n])]
            n += 1

        # Average Adjacency Matrix for All Quarters
        self.MoveCH = np.array([[0 for j in P] for i in R]).astype(np.float)

        for i in R:
            self.MoveCH[i, :] = self.ComHosQtr[:, i, :].mean(axis=0) / 90 # convert to days

        # Calculate Total Movement Outflows
        TotCH = np.array([0 for i in R]).astype(np.float)

        for i in R:
            TotCH[i] = self.MoveCH[i, :].sum()

        # Prevent NaN and set null
        TotCH = np.where(TotCH == 0, 1, TotCH)

        # Calculate Transition Rate for Movement Destination
        self.TranCH = np.array([[0 for j in P] for i in R]).astype(np.float)

        for i in R:
            self.TranCH[i, :] = self.MoveCH[i, :] / TotCH[i]


        # Calculate Movement Rate for Movement Destination
        self.MoveRateCH = np.array([[0 for j in P] for i in R]).astype(np.float)

        for i in R:
            self.MoveRateCH[i, :] = self.MoveCH[i, :] / self.AvgPopC[i]

        print("*****************  Finished Loading Data")