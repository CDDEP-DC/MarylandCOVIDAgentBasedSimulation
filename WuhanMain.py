
import random
import numpy as np
import math
import time
import pickle
from datetime import datetime
import os
import csv

import PostProcessing
import ParameterSet
import Utils
import GlobalModel
# import ProcessingDataForPresentation

def main():
    runs = 1
    xRes = 50           # Landscan Resolution
    yRes = 50
    modelPopNames = 'Wuhan'
    ParameterSet.ResultsFolder = ParameterSet.ResultsFolder + "/Wuhan"
    if not os.path.exists(ParameterSet.ResultsFolder):
        os.makedirs(ParameterSet.ResultsFolder)

    # clear file folder
    outputfiles = os.listdir(ParameterSet.ResultsFolder)
    for x in outputfiles:
        os.remove(os.path.join(ParameterSet.ResultsFolder, x))

    for run in range(0, runs):
        endTime = 10
        stepLength = 1
        dateTimeObj = datetime.now()
        resultsName = str(dateTimeObj.year) + str(dateTimeObj.month) + \
                      str(dateTimeObj.day) + str(dateTimeObj.hour) + \
                      str(dateTimeObj.minute) + str(dateTimeObj.second) + \
                      str(dateTimeObj.microsecond)

        Model = 'Wuhan'  # select model

        RegionalList, numInfList, CoordDict, HospitalTransitionRate = GlobalModel.modelSetup(Model,
                modelPopNames, combineLocations=True, XRes=xRes, YRes=yRes)
        GlobalModel.RunModel(RegionalList, modelPopNames, endTime, stepLength,
                             resultsName, numInfList)
        results = Utils.FileRead(
            ParameterSet.ResultsFolder + "/Results_" + resultsName + ".pickle")
        # print(results)
        # PostProcessing.WriteAggregatedResults(results ,Model ,resultsName
        #                                       ,modelPopNames ,RegionalList
        #                                       ,CoordDict ,endTime)

        GlobalModel.cleanUp(modelPopNames)

if __name__ == "__main__":
    # execute only if run as a script
    main()
