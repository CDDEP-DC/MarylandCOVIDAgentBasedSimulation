


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
    
    if not os.path.exists(ParameterSet.PopDataFolder):
        os.makedirs(ParameterSet.PopDataFolder)
        
    if not os.path.exists(ParameterSet.QueueFolder):
        os.makedirs(ParameterSet.QueueFolder)
        
    if not os.path.exists(ParameterSet.ResultsFolder):
        os.makedirs(ParameterSet.ResultsFolder)
        

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
    Model = 'IndiaSIM'  # select model
    GlobalModel.cleanUp(modelPopNames)
 
    ParameterSet.ResultsFolder = ParameterSet.ResultsFolder + "/MDDCVAregionInt"
    if not os.path.exists(ParameterSet.ResultsFolder):
        os.makedirs(ParameterSet.ResultsFolder)
    
    #interventionnames = ['seasonality2','seasonality','distance.10','highcontact','worse','baseline']
    #interventionnames = ['distance.10','worse']
    #intervenionreduction1 = [1,.9,.9]
    #intervenionreduction2 = [0,0,0]
    #intervenionreductionSchool = [1,.5,.5]
    interventionnames = ['baseline','worse','baddistance.75','baddistance.25','baddistance.50']
    intervenionreduction1 = [1,1,.75,.25,.5]
    intervenionreduction2 = [0,0,0,0,0]
    intervenionreductionSchool = [1,.5,.5,.5,.5]
    
    for run in range(0,runs):
        stepLength = 1
        dateTimeObj = datetime.now()
        resultsName = str(dateTimeObj.year) + str(dateTimeObj.month) + \
                      str(dateTimeObj.day) + str(dateTimeObj.hour) + \
                      str(dateTimeObj.minute) + str(dateTimeObj.second) + \
                      str(dateTimeObj.microsecond)
        
        Utils.JiggleParameters()
        
        ParameterVals = { 
            'AG04AsymptomaticRate':ParameterSet.AG04AsymptomaticRate,
            'AG04HospRate':ParameterSet.AG04HospRate,
            'AG517AsymptomaticRate':ParameterSet.AG517AsymptomaticRate,
            'AG517HospRate':ParameterSet.AG517HospRate,
            'AG1849AsymptomaticRate':ParameterSet.AG1849AsymptomaticRate,
            'AG1849HospRate':ParameterSet.AG1849HospRate,
            'AG5064AsymptomaticRate':ParameterSet.AG5064AsymptomaticRate,
            'AG5064HospRate':ParameterSet.AG5064HospRate,
            'AG65AsymptomaticRate':ParameterSet.AG65AsymptomaticRate,
            'AG65HospRate':ParameterSet.AG65HospRate,
            'IncubationTime':ParameterSet.IncubationTime,
            'totalContagiousTime':ParameterSet.totalContagiousTime,
            'hospitalSymptomaticTime':ParameterSet.hospitalSymptomaticTime,
            'hospTime':ParameterSet.hospTime,
            'EDVisit':ParameterSet.EDVisit,
            'preContagiousTime':ParameterSet.preContagiousTime,
            'postContagiousTime':ParameterSet.postContagiousTime,
            'householdcontactRate':ParameterSet.householdcontactRate,
            'ProbabilityOfTransmissionPerContact':ParameterSet.ProbabilityOfTransmissionPerContact,
            'symptomaticContactRateReduction':ParameterSet.symptomaticContactRateReduction,
            'ImportationRate':ParameterSet.ImportationRate,
            'ImportationRatePower':ParameterSet.ImportationRatePower
        }
                      
        for intnum in range(0,len(interventionnames)):
            if 'seasonality' in interventionnames[intnum]:
                endTime = 365
            else:
                endTime = 300
            ParameterSet.Intervention = interventionnames[intnum]
            if 'worse' in interventionnames[intnum]:
                Utils.JiggleParameters('worse')
            if 'distance' in interventionnames[intnum]:
                ParameterSet.InterventionDate = random.randint(75,91)
                ParameterSet.InterventionEndDate = ParameterSet.InterventionDate + 75
            else:
                ParameterSet.InterventionDate = -1
                ParameterSet.InterventionEndDate = -1
            ParameterSet.InterventionReduction = intervenionreduction1[intnum]
            ParameterSet.InterventionReduction2 = intervenionreduction1[intnum]
            ParameterSet.InterventionReductionSchool = intervenionreductionSchool[intnum]
            print(ParameterSet.ProbabilityOfTransmissionPerContact)
            resultsNameP = interventionnames[intnum] + "_" + resultsName
        
            #try:
            #ParameterSet.debugmodelevel = ParameterSet.debugerror
            
            RegionalList, numInfList, HospitalNames, LocationImportationRisk, RegionListGuide = GlobalModel.modelSetup(Model, modelPopNames,combineLocations=True,TestNumPops=10)
            
            GlobalModel.RunModel(RegionalList, modelPopNames, endTime, stepLength, resultsNameP, numInfList,LocationImportationRisk=LocationImportationRisk, RegionListGuide=RegionListGuide)
            
            results = Utils.FileRead(ParameterSet.ResultsFolder + "/Results_" + resultsNameP + ".pickle")
         
            PostProcessing.WriteAggregatedResults(results,Model,resultsNameP,modelPopNames,RegionalList,ParameterVals,HospitalNames,endTime)    
            GlobalModel.cleanUp(modelPopNames)
            #except:        
            #    GlobalModel.cleanUp(modelPopNames)
            
if __name__ == "__main__":
    # execute only if run as a script
    main()
