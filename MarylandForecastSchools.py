


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


def main():
    
    ParameterSet.HHSizeDist = [14.7,26.9,18.6,20.1,10.9,4.8,4]
    ParameterSet.HHSizeAgeDist = {}
    ParameterSet.HHSizeAgeDist[1] = [0,0,5.1,3.7,5.9]
    ParameterSet.HHSizeAgeDist[2] = [0.1,0.8,7.6,9.1,9.3]
    ParameterSet.HHSizeAgeDist[3] = [1.1,2.8,8.2,4.6,1.9]
    ParameterSet.HHSizeAgeDist[4] = [1.8,5.7,9,2.8,0.8]
    ParameterSet.HHSizeAgeDist[5] = [1,3.8,4.5,1.2,0.4]
    ParameterSet.HHSizeAgeDist[6] = [0.5,1.7,1.9,0.5,0.2]
    ParameterSet.HHSizeAgeDist[7] = [0.5,1.4,1.5,0.4,0.2]

    runs = 10000
    modelPopNames = 'ZipCodes'
    Model = 'Maryland'  # select model
    GlobalModel.cleanUp(modelPopNames)
    ParameterSet.ResultsFolder = ParameterSet.ResultsFolder + "/MarylandInt"
    if not os.path.exists(ParameterSet.ResultsFolder):
        os.makedirs(ParameterSet.ResultsFolder)
    
    #interventionnames = ['seasonality2','seasonality','distance.10','highcontact','worse','baseline']
    #interventionnames = ['distance.10','worse']
    #intervenionreduction1 = [1,.9,.9]
    #intervenionreduction2 = [0,0,0]
    #intervenionreductionSchool = [1,.5,.5]
    interventionnames = ['worse','worsedistance.10','worsedistance.25','worsedistance.40']
    intervenionreduction1 = [1,.9,.75,.6]
    intervenionreduction2 = [0,0,0,0]
    intervenionreductionSchool = [1,.5,.5,.5]
    
    #DiseaseVariables:
    ParameterSet.IncubationTime = 11
    ParameterSet.totalContagiousTime = 5
    ParameterSet.symptomaticTime = 6
    ParameterSet.hospitalSymptomaticTime = 14
    ParameterSet.hospTime = 7
    ParameterSet.EDVisit = .8
    ParameterSet.preContagiousTime = 2
    ParameterSet.postContagiousTime = 6
    ParameterSet.ICUtime = 14
    ParameterSet.PostICUTime = 5
    ParameterSet.ImportationRate = 2
    
    for run in range(0,runs):
        stepLength = 1
        dateTimeObj = datetime.now()
        resultsName = str(dateTimeObj.year) + str(dateTimeObj.month) + \
                      str(dateTimeObj.day) + str(dateTimeObj.hour) + \
                      str(dateTimeObj.minute) + str(dateTimeObj.second) + \
                      str(dateTimeObj.microsecond)
        
        Utils.JiggleParameters()
                      
        for intnum in range(0,len(interventionnames)):
            if 'seasonality' in interventionnames[intnum]:
                endTime = 334
            else:
                endTime = 201
            ParameterSet.Intervention = interventionnames[intnum]
            if 'worse' in interventionnames[intnum]:
                Utils.JiggleParameters('worse')
            if 'distance' in interventionnames[intnum]:
                ParameterSet.InterventionDate = random.randint(84,92)
            else:
                ParameterSet.InterventionDate = -1
            ParameterSet.InterventionEndDate = random.randint(151,160)
            ParameterSet.InterventionReduction = intervenionreduction1[intnum]
            ParameterSet.InterventionReduction2 = intervenionreduction1[intnum]
            ParameterSet.InterventionReductionSchool = intervenionreductionSchool[intnum]
            print(ParameterSet.ProbabilityOfTransmissionPerContact)
            resultsNameP = interventionnames[intnum] + "_" + resultsName
        
            #try:
            RegionalList, numInfList, HospitalNames, LocationImportationRisk, RegionListGuide = GlobalModel.modelSetup(Model, modelPopNames,combineLocations=True,TestNumPops=10)
            
            GlobalModel.RunModel(RegionalList, modelPopNames, endTime, stepLength, resultsNameP, numInfList,LocationImportationRisk=LocationImportationRisk, RegionListGuide=RegionListGuide)
            
            results = Utils.FileRead(ParameterSet.ResultsFolder + "/Results_" + resultsNameP + ".pickle")
         
            PostProcessing.WriteAggregatedResults(results,Model,resultsNameP,modelPopNames,RegionalList,HospitalNames,endTime)    
            GlobalModel.cleanUp(modelPopNames)
            #except:        
            #    GlobalModel.cleanUp(modelPopNames)
            
if __name__ == "__main__":
    # execute only if run as a script
    main()
