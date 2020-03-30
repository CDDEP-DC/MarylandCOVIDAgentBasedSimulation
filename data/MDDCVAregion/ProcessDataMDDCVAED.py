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
        self.ComHosAdj = pd.read_csv(datadir + "/EDCommunityMatrix.csv", index_col=0)

        # print(self.ComHosAdj)

        """ Create Adjacency Flow Matrix """
        td = self.ComNames.copy()
        td = td.merge(pd.DataFrame(self.ComHosAdj), how='left',
                      left_on='ZIP_CODE', right_index=True) # left join on population > 0
        td = td.set_index('ZIP_CODE')
        TranCH = td.values
        self.TranCH = np.asarray(TranCH)
        # print(self.ComHosAdj.index.difference(np.array(popdata['ZIP_CODE'])).values) # find difference in set

        self.HosNames = self.ComHosAdj.columns
        P = list(range(len(self.HosNames)))     # Hospital

        FacList = pd.read_csv(datadir + '/FacilityList.csv')
        self.HosNamesDict = {} # Dictionary mapping HSCRC ID to Name
        for i in range(0,FacList.HOSPID.__len__()):
            self.HosNamesDict[int(FacList.HOSPID[i])] = FacList.ProviderNames[i]

        self.ProviderNamesColumn = {} # Dictionary mapping name to column in adjacency matrix

        for i in P:
            self.ProviderNamesColumn[i] = self.HosNamesDict[int(self.HosNames[i])]



        print("*****************  Finished Loading Data")